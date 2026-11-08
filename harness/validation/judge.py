#!/usr/bin/env python3
"""Judge a validation run: the BU Bench V1 judge as published, on any of several models.

BU: one binary verdict from the task and the trajectory log (no ground truth in V1).
Odysseys: one verdict per rubric item from the trajectory log and the run's screenshots;
the task's score is the mean, perfect when every item passes.

    OPENAI_API_KEY=... python3 judge.py RUN bu
    OPENAI_API_KEY=... python3 judge.py RUN odysseys DATA_DIR/odysseys/odysseys.json
    OPENAI_API_KEY=... python3 judge.py RUN interaction interaction.jsonl
    JUDGE_CODEX=gpt-5.6-sol python3 judge.py RUN webvoyager
    JUDGE_CODEX=gpt-5.6-sol python3 judge.py RUN bu-v1 DATA_DIR/bu-bench-v1/BU_Bench_V1.json

WebVoyager: the pinned auto_eval prompts (../webvoyager/.judge) over the answer and final.png.
JUDGE_CODEX=MODEL asks that model through `codex exec` on the subscription instead of the
OpenAI API, JUDGE_CLAUDE=MODEL through `claude -p`; verdicts from two judges are not comparable,
so both arms of an A/B take the same one.

Interaction: the Odysseys rubric grader over the rubrics each row of interaction.jsonl carries.
"""
import argparse
import base64
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'runner'))
import codex as host  # noqa: E402  the actor's isolation: no personal skills, extra tools or features

MODEL = 'gpt-5.5'
SIDE = 40_000            # BU grader JUDGE_TEXT_SIDE_LENGTH
OUTPUT_CHARS = 1_500     # per command output in the trajectory log
SCREENSHOTS = 20         # most recent images sent to the Odysseys grader
RUBRICS_AT_ONCE = 4      # Odysseys rubric items graded concurrently

BU_SYSTEM = """You are an expert judge evaluating browser automation agent performance.

<evaluation_framework>

**PRIMARY EVALUATION CRITERIA (in order of importance):**
1. **Task Satisfaction (Most Important)**: Did the agent accomplish what the user asked for?
2. **Output Quality**: Is the final result in the correct format and complete?
3. **Tool Effectiveness**: Did the browser interactions work as expected?
4. **Agent Reasoning**: Quality of decision-making, planning, and problem-solving.
5. **Browser Handling**: Navigation stability, error recovery, and technical execution.

**VERDICT GUIDELINES:**
- true: Task completed as requested, human-like execution, all user criteria were met, and the agent did not make up information.
- false: Task not completed, or only partially completed.

**FAILURE CONDITIONS (automatically set verdict to false):**
- Blocked by captcha or missing authentication
- Output format completely wrong or missing
- Infinite loops or severe technical failures
- Critical user requirements ignored
- Page not loaded
- Browser crashed
- Agent could not interact with required UI elements
- The agent calls done action before completing all key points of the task

**IMPOSSIBLE TASK DETECTION:**
Set `impossible_task` to true when the task fundamentally could not be completed due to ambiguous instructions, broken/inaccessible pages, required authentication without credentials, missing site functionality, or other insurmountable external obstacles.

Do NOT mark as impossible if the agent made poor decisions but the task was achievable.

**IMPORTANT EVALUATION NOTES:**
- Evaluate whether attempted actions actually happened.
- Be initially doubtful of the agent's self-reported success.
- This harness provides browser-cmd shell commands and their outputs instead of daemon-side screenshots. Do not penalize missing screenshots by itself.

</evaluation_framework>

<response_format>
Respond with EXACTLY this JSON structure (no additional text before or after):

{
  "reasoning": "Detailed analysis of task satisfaction, trajectory quality, tool usage, output quality, and overall user satisfaction prediction.",
  "verdict": true or false,
  "failure_reason": "Max 5 sentences explanation of why the task was not completed successfully in case of failure. If verdict is true, use an empty string.",
  "impossible_task": true or false,
  "reached_captcha": true or false
}
</response_format>"""

ODYSSEYS_SYSTEM = """You are an expert evaluator of web-navigation agent trajectories.

You will receive:
- The user task (for context).
- ONE specific rubric item with a requirement and a verification description.
- The agent's full action history (one line per step).
- Every screenshot from the trajectory, in chronological order.

Your goal is to decide whether this single rubric item is satisfied by the trajectory.

Evaluation rules:
- Judge ONLY the one rubric item you are given; ignore all other implicit requirements.
- Ground your judgment in what the screenshots and actions actually show. Do not invent state.
- Filtering / sorting / form requirements must be applied and confirmed to count as satisfied.
- If the agent was blocked (captcha, access denied, etc.) and therefore could not satisfy the rubric, report failure.

Respond in exactly this format:

Thoughts: <your reasoning, citing specific steps/screenshots>
Status: "success" or "failure"
"""


def trajectory(task_dir):
    """One line per step: the actor's messages, commands with their output, web searches, then the answer."""
    lines, calls = [], {}
    for line in (task_dir / 'transcript.jsonl').read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        # Claude Code's stream: assistant text and tool calls, each answered in a later user turn.
        content = (event.get('message') or {}).get('content')
        for part in content if event.get('type') in ('assistant', 'user') and isinstance(content, list) else []:
            if part.get('type') == 'text' and event['type'] == 'assistant':
                lines.append('message: ' + part['text'].replace('\n', ' '))
            elif part.get('type') == 'tool_use':
                calls[part['id']] = len(lines)
                lines.append(f"command: {part['input'].get('command', json.dumps(part['input']))!r} -> ")
            elif part.get('type') == 'tool_result' and part.get('tool_use_id') in calls:
                result = part.get('content')
                text = result if isinstance(result, str) else ' '.join(
                    piece.get('text', '') for piece in result or [] if isinstance(piece, dict))
                lines[calls[part['tool_use_id']]] += text[:OUTPUT_CHARS].replace('\n', ' | ')
        item = event.get('item') or {}
        if event.get('type') != 'item.completed':
            continue
        if item.get('type') == 'agent_message':
            lines.append('message: ' + item.get('text', '').replace('\n', ' '))
        elif item.get('type') == 'command_execution':
            output = item.get('aggregated_output', '')[:OUTPUT_CHARS].replace('\n', ' | ')
            lines.append(f"command: {item.get('command', '')!r} -> {output}")
        elif item.get('type') == 'web_search':
            lines.append('web_search: ' + json.dumps(item.get('action') or item.get('query')))
    answer = (task_dir / 'ANSWER.txt').read_text() if (task_dir / 'ANSWER.txt').exists() else ''
    lines.append('final answer: ' + answer.replace('\n', ' '))
    return '\n'.join(lines)


def truncate(text):
    """BU grader truncateText: whole lines from the head and the tail, about SIDE characters each."""
    if len(text) <= SIDE * 2:
        return text
    lines = text.split('\n')

    def upto(seq):
        kept, size = [], 0
        for line in seq:
            kept.append(line)
            size += len(line) + 1
            if size > SIDE:
                break
        return kept
    head, tail = upto(lines), upto(reversed(lines))[::-1]
    return '\n'.join([*head, f'[...truncated {max(0, len(lines) - len(head) - len(tail))} lines - agent did actions '
                      'but truncated...]', *tail])


def screenshots(task_dir):
    """The latest screenshots, then the harness's own of each kept tab, then final.png: SCREENSHOTS in all."""
    final = [task_dir / 'final.png'] if (task_dir / 'final.png').exists() else []
    audited = sorted((task_dir / 'tabs').glob('*.png'))[-(SCREENSHOTS - 1):]
    shots = sorted((path for path in (task_dir / 'work' / 'media' / 'browser').glob('*.png')
                    if path.name not in {shot.name for shot in audited}), key=lambda p: p.stat().st_mtime)
    room = SCREENSHOTS - len(final) - len(audited)
    shots = (shots[len(shots) - room:] if room > 0 else []) + audited + final
    return [base64.b64encode(path.read_bytes()).decode() for path in shots]


def audited_tabs(task_dir):
    """The harness's `tab check` at the end of the run, for the grader beside the actor's own claims."""
    tabs = task_dir / 'tabs.txt'
    return f'\n\nFinal browser tabs (audited by the harness):\n{tabs.read_text().strip()}' if tabs.exists() else ''


def ask(system, text, images=()):
    if os.environ.get('JUDGE_CODEX'):
        return ask_codex(system, text, images)
    if os.environ.get('JUDGE_CLAUDE'):
        return ask_claude(system, text, images)
    content = [{'type': 'text', 'text': text},
               *({'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{data}'}} for data in images)]
    body = json.dumps({'model': MODEL, 'seed': 42, 'max_completion_tokens': 8192,
                       'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': content}]})
    for attempt in range(8):
        request = urllib.request.Request('https://api.openai.com/v1/chat/completions', body.encode(), {
            'Authorization': f"Bearer {os.environ['OPENAI_API_KEY']}", 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                return json.load(response)['choices'][0]['message']['content']
        except OSError as error:
            if attempt == 7:
                raise
            # A rate limit is a minute's budget spent: wait it out, not a few seconds.
            limited = getattr(error, 'code', None) == 429
            time.sleep((60 if limited else 10) * (attempt + 1))


# Wrappers that add their own tools or hooks to codex stand aside, as they do for the actor.
NO_EXTRAS = {'CMUX_CLAUDE_HOOKS_DISABLED': '1', 'CMUX_CODEX_HOOKS_DISABLED': '1', 'CMUX_COMPUTER_USE_MCP_DISABLED': '1'}


def ask_codex(system, text, images):
    """One answer from a subscription model through codex exec, in a home of its own with no tools."""
    with tempfile.TemporaryDirectory(prefix='judge-') as tmp:
        home = Path(tmp) / 'codex'
        home.mkdir()
        (home / 'auth.json').symlink_to(Path.home() / '.codex' / 'auth.json')
        attached = [part for path in small_images(images, tmp) for part in ('--image', str(path))]
        last = Path(tmp) / 'last.txt'
        isolated = host.settings(argparse.Namespace(effort='medium', web_tools=False, auto_compact=None, subagents=False))
        command = ['codex', 'exec', '--skip-git-repo-check', '-m', os.environ['JUDGE_CODEX'], *isolated,
                   '--output-last-message', str(last), *attached, '-']
        failure = ''
        for attempt in range(4):
            try:
                done = subprocess.run(command, input=f'{system}\n\n{text}', text=True, capture_output=True, cwd=tmp,
                                      env={**os.environ, 'CODEX_HOME': str(home), **NO_EXTRAS}, timeout=1200)
            except subprocess.TimeoutExpired:
                failure = 'no answer within 20 minutes'
                continue
            if done.returncode == 0 and last.exists() and last.read_text().strip():
                return last.read_text()
            failure = done.stderr[-500:]
            time.sleep(30 * (attempt + 1))
        raise RuntimeError(f'codex judge failed: {failure}')


def small_images(images, tmp):
    """The screenshots as files, smaller: twenty full-size ones make a request too large to answer in time."""
    paths = []
    for index, data in enumerate(images):
        image = Path(tmp) / f'{index}.png'
        image.write_bytes(base64.b64decode(data))
        small = image.with_suffix('.jpg')
        subprocess.run(['sips', '-Z', '1280', '-s', 'format', 'jpeg', str(image), '--out', str(small)],
                       capture_output=True, check=True)
        paths.append(small)
    return paths


def ask_claude(system, text, images):
    """One answer from a Claude model through `claude -p`: no settings, plugins or MCP, only Read for the screenshots."""
    with tempfile.TemporaryDirectory(prefix='judge-') as tmp:
        paths = small_images(images, tmp)
        shown = ''.join(f'\n{path}' for path in paths)
        prompt = text + (f'\n\nThe screenshots, in order: read every one of these files with the Read tool before '
                         f'answering.{shown}' if paths else '')
        command = ['claude', '-p', '--model', os.environ['JUDGE_CLAUDE'], '--setting-sources', '',
                   '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}', '--no-session-persistence',
                   '--permission-mode', 'dontAsk', '--tools', 'Read', '--allowedTools', 'Read',
                   '--system-prompt', system, '--output-format', 'json']
        failure = ''
        for attempt in range(4):
            try:
                done = subprocess.run(command, input=prompt, text=True, capture_output=True, cwd=tmp,
                                      env={**os.environ, **NO_EXTRAS}, timeout=1200)
            except subprocess.TimeoutExpired:
                failure = 'no answer within 20 minutes'
                continue
            answer = json.loads(done.stdout or '{}') if done.returncode == 0 else {}
            if answer.get('result', '').strip() and not answer.get('is_error'):
                return answer['result']
            failure = (done.stderr or done.stdout)[-500:]
            time.sleep(30 * (attempt + 1))
        raise RuntimeError(f'claude judge failed: {failure}')


def judge_webvoyager(task, task_dir):
    """The pinned WebVoyager auto_eval prompts, read as text, over the answer and the final screenshot."""
    source = (Path(__file__).resolve().parent.parent / 'webvoyager' / '.judge' / 'auto_eval.py').read_text()
    system = re.search(r'SYSTEM_PROMPT = """(.*?)"""', source, re.S).group(1)
    user = re.search(r'USER_PROMPT = """(.*?)"""', source, re.S).group(1)
    answer = (task_dir / 'ANSWER.txt').read_text().strip() if (task_dir / 'ANSWER.txt').exists() else ''
    shots = [base64.b64encode((task_dir / 'final.png').read_bytes()).decode()] if (task_dir / 'final.png').exists() else []
    text = user.replace('<task>', task['ques']).replace('<answer>', answer).replace('<num>', str(len(shots)))
    raw = ask(system, text + '\nYour verdict:\n', shots)
    return {'pass': passed(raw), 'reasoning': raw}


def passed(raw):
    """The last stated verdict, wherever it stands: a judge may open with it and later say a point
    "doesn't change the verdict"."""
    stated = re.findall(r'verdict\W*(NOT SUCCESS|SUCCESS)', raw, re.I)
    verdict = stated[-1].upper() if stated else raw.upper()
    return 'NOT SUCCESS' not in verdict and 'SUCCESS' in verdict


def judge_bu(task, task_dir):
    text = (f"\n<task>\n{truncate(task['ques']) or 'No task provided'}\n</task>\n\n<agent_trajectory>\n"
            f"{truncate(trajectory(task_dir) + audited_tabs(task_dir)) or 'No agent trajectory provided'}\n</agent_trajectory>\n\n"
            'Evaluate this agent execution given the criteria and respond with the exact JSON structure requested.')
    raw = ask(BU_SYSTEM, text)
    verdict = json.loads(raw[raw.find('{'):raw.rfind('}') + 1])
    return {'pass': verdict.get('verdict') is True, **verdict}


def judge_bu_v1(task, task_dir, dataset):
    """The BU Bench V1 judge as published (judge.py beside the dataset): its prompts, the task's ground truth and
    the last ten screenshots. The trajectory keeps head and tail rather than the head: a shell trajectory is longer
    than a Browser Use one, and the published cut would hide how it ended."""
    source = (Path(dataset).parent / 'judge.py').read_text()
    gate = re.search(r'ground_truth_section = """(.*?)"""', source, re.S).group(1)
    system = re.search(r'system_prompt = f"""(.*?)"""', source, re.S).group(1)
    truth = {row['task_id']: row.get('answer') for row in json.loads(Path(dataset).read_text())}[task['id']]
    system = system.replace('{ground_truth_section}', gate if truth else '').replace('{{', '{').replace('}}', '}')
    shots = screenshots(task_dir)[-10:]
    answer = (task_dir / 'ANSWER.txt').read_text().strip() if (task_dir / 'ANSWER.txt').exists() else ''
    answer = answer.removeprefix('FINAL:').strip()
    block = f'\n<ground_truth>\n{truth}\n</ground_truth>\n' if truth else ''
    text = (f"\n<task>\n{task['ques'][:40_000]}\n</task>\n{block}\n<agent_trajectory>\n"
            f"{truncate(trajectory(task_dir)) or 'No agent trajectory provided'}\n</agent_trajectory>\n\n"
            f"<final_result>\n{answer[:40_000] or 'No final result provided'}\n</final_result>\n\n"
            f"{len(shots)} screenshots from execution are attached.\n\n"
            'Evaluate this agent execution given the criteria and respond with the exact JSON structure requested.')
    raw = ask(system, text, shots)
    verdict = json.loads(raw[raw.find('{'):raw.rfind('}') + 1])
    return {'pass': verdict.get('verdict') is True, **verdict}


def judge_odysseys(task, task_dir, rubrics):
    history = trajectory(task_dir).strip() or 'No actions recorded.'
    steps = len([line for line in history.split('\n') if line])
    history += audited_tabs(task_dir)
    images = screenshots(task_dir)

    def grade(item):
        rubric_id, rubric = item
        text = (f"User Task (context only): {task['ques'].strip()}\n\nEvaluate ONLY this rubric item:\n"
                f"Rubric ID: {rubric_id}\nRequirement: {rubric['requirement'].strip()}\n"
                f"Verification: {rubric['verification'].strip()}\n\nFull Action History:\n{history}\n\n"
                f"Screenshots attached below: {len(images)} (trajectory had {steps} total step(s)).\n\n"
                f"Decide whether the rubric ({rubric_id}) is satisfied. Use the required 'Thoughts:' / 'Status:' format.")
        raw = ask(ODYSSEYS_SYSTEM, text, images)
        status = re.search(r'Status:\s*["\']?(success|failure)', raw, re.I)
        return {'rubric_id': rubric_id, 'requirement': rubric['requirement'],
                'score': int(bool(status) and status.group(1).lower() == 'success'), 'reasoning': raw}

    if SUBSCRIPTION:
        results = grade_together(task, rubrics, history, steps, images)
    else:
        # Items are independent: graded side by side, kept in rubric order.
        with concurrent.futures.ThreadPoolExecutor(max_workers=RUBRICS_AT_ONCE) as pool:
            results = list(pool.map(grade, rubrics.items()))
    score = sum(result['score'] for result in results) / len(results)
    return {'pass': score == 1, 'average_rubric_score': score, 'rubric_results': results}


def rubrics_of(dataset):
    """Rubrics by task id: Odysseys' JSON list, or a task file whose rows carry their own."""
    text = Path(dataset).read_text()
    rows = json.loads(text) if text.lstrip().startswith('[') else [json.loads(line) for line in text.splitlines()
                                                                     if line.strip()]
    return {row.get('task_id', row.get('id')): row['rubrics'] for row in rows}


def grade_together(task, rubrics, history, steps, images):
    """Every rubric item of a task in one request, each with its own status: a subscription answers
    about once a minute, too slowly for one request per item."""
    items = '\n'.join(f"Rubric ID: {rubric_id}\nRequirement: {rubric['requirement'].strip()}\n"
                      f"Verification: {rubric['verification'].strip()}\n" for rubric_id, rubric in rubrics.items())
    text = (f"User Task (context only): {task['ques'].strip()}\n\nEvaluate EACH of these rubric items on its "
            f"own, ignoring the others:\n{items}\nFull Action History:\n{history}\n\n"
            f"Screenshots attached below: {len(images)} (trajectory had {steps} total step(s)).\n\n"
            "For every rubric item, in order, answer with 'Rubric ID: <id>', 'Thoughts: <reasoning>' and "
            "'Status: \"success\"' or 'Status: \"failure\"'.")
    raw = ask(ODYSSEYS_SYSTEM, text, images)
    results = []
    for rubric_id, rubric in rubrics.items():
        part = re.search(rf'Rubric ID:\s*{re.escape(str(rubric_id))}\b(.*?)(?=Rubric ID:|\Z)', raw, re.S)
        status = part and re.search(r'Status:\s*["\']?(success|failure)', part.group(1), re.I)
        results.append({'rubric_id': rubric_id, 'requirement': rubric['requirement'],
                        'score': int(bool(status) and status.group(1).lower() == 'success'),
                        'reasoning': part.group(1).strip() if part else raw})
    return results


SUBSCRIPTION = os.environ.get('JUDGE_CODEX') or os.environ.get('JUDGE_CLAUDE')


def main(run, bench, dataset=None):
    rubrics = rubrics_of(dataset) if dataset and bench != 'bu-v1' else {}
    # Verdicts already given survive a judge stopped part way, so a rerun asks only for the rest.
    # Each judge keeps its own verdicts: one judge's are never mixed with another's.
    name = 'validation_judge' + (f'.{SUBSCRIPTION}' if SUBSCRIPTION else '')
    partial = run / f'{name}.partial.json'
    verdicts = json.loads(partial.read_text()) if partial.exists() else {}
    for result in sorted(run.glob('task_*/result.json'), key=lambda p: int(p.parent.name.split('_')[1])):
        task = json.loads(result.read_text())['task']
        if task['id'] not in verdicts:
            verdicts[task['id']] = (judge_bu(task, result.parent) if bench == 'bu'
                                    else judge_bu_v1(task, result.parent, dataset) if bench == 'bu-v1'
                                    else judge_webvoyager(task, result.parent) if bench == 'webvoyager'
                                    else judge_odysseys(task, result.parent, rubrics[task['id']]))
            partial.write_text(json.dumps(verdicts, ensure_ascii=False))
        print(task['id'], verdicts[task['id']]['pass'], verdicts[task['id']].get('average_rubric_score', ''), flush=True)
    judge = SUBSCRIPTION or MODEL
    summary = {'judge': f'{bench} grader port on {judge}', 'tasks': len(verdicts),
               'pass': sum(v['pass'] for v in verdicts.values())}
    if bench not in ('bu', 'bu-v1', 'webvoyager'):
        summary['mean_rubric_score'] = sum(v['average_rubric_score'] for v in verdicts.values()) / len(verdicts)
    (run / f'{name}.json').write_text(json.dumps({'summary': summary, 'verdicts': verdicts},
                                                          ensure_ascii=False, indent=2))
    print(json.dumps(summary))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2], *sys.argv[3:])
