<p align="center">
  <img alt="browser-cmd" src="docs/assets/logo.svg" width="360">
</p>

<p align="center">
  <strong>BU Bench V1 results: four judges, two evaluation protocols, per-task verdicts and an account of every miss.</strong>
</p>

<p align="center">
  <a href="#results"><img alt="BU protocol: best counted score 96/100" src="https://img.shields.io/badge/BU%20protocol-96%2F100-0B0D12"></a>
  <a href="#a-second-judging-protocol-aside"><img alt="Aside protocol: best counted score 97/100" src="https://img.shields.io/badge/Aside%20protocol-97%2F100-0B0D12"></a>
  <img alt="Four judges across both protocols: counted scores 89–97/100" src="https://img.shields.io/badge/4%20judges-89%E2%80%9397%2F100-0B0D12">
  <a href="https://github.com/elmyx-labs/browser-cmd"><img alt="browser-cmd" src="https://img.shields.io/badge/agent%20browser-browser--cmd-0B0D12"></a>
</p>

<p align="center">
  <a href="#results">Results</a> ·
  <a href="#a-second-judging-protocol-aside">Aside protocol</a> ·
  <a href="#where-this-stands">Position</a> ·
  <a href="#run-protocol">Protocol</a> ·
  <a href="#what-is-and-is-not-here">Published data</a> ·
  <a href="#verify-it">Verify</a> ·
  <a href="results/reports/20261031-codex-gpt-6.1-sol-report.md">Run report</a> ·
  <a href="results/reports/20261108-judging-protocols.md">Judging report</a>
</p>

---

A Codex gpt-6.1-sol agent, reviewed by gpt-6.1-terra and driving a real Chrome through
[browser-cmd](https://github.com/elmyx-labs/browser-cmd), scores up to **96/100** on
[BU Bench V1](https://github.com/browser-use/benchmark) with the benchmark's original judge prompts and **97/100**
with Aside's prompt. Across four judges, the counted scores are **89–96** and **95–97**, respectively, on the same
agent run. This is our own run, not an official entry: BU Bench V1 has no public leaderboard or submission process.

## Results

| Judge | BU prompts: passed | BU prompts: raw | Aside prompt: passed | Aside prompt: raw |
| --- | ---: | ---: | ---: | ---: |
| GPT-5.5 | **96** | 97 | **97** | 98 |
| Gemini 2.5 Flash | **96** | 97 | **96** | 97 |
| gpt-5.6-sol | **94** | 95 | **96** | 97 |
| Claude Opus 5.5 | **89** | 89 | **95** | 96 |

All scores are out of 100. The same manual failure rule is applied to both protocols.

The original evaluation uses the benchmark's published judge prompts, its ground truth where a task has one, and
the last ten screenshots. All four judges agree that 87 counted tasks pass under BU prompts and 94 under Aside's prompt.

**Passed** treats one task as failed whatever the judges said: the agent reached its result through a site's internal
host, past a bot challenge, which we do not count as completing the task. **Raw** is the judge's own count. No other verdict is changed.

Category results below are counted passes out of 20. Each cell shows **BU prompts → Aside prompt**.

| Category | GPT-5.5 | Gemini 2.5 Flash | gpt-5.6-sol | Claude Opus 5.5 |
| --- | ---: | ---: | ---: | ---: |
| BrowseComp | 20 → 20 | 19 → 19 | 20 → 20 | 19 → 19 |
| GAIA | 20 → 20 | 20 → 20 | 20 → 20 | 20 → 20 |
| InteractionTests | 20 → 20 | 20 → 20 | 20 → 20 | 18 → 20 |
| OM2W2 | 19 → 20 | 20 → 20 | 19 → 19 | 17 → 19 |
| WebBenchREAD | 17 → 17 | 17 → 17 | 15 → 17 | 15 → 17 |

The median task takes 263 seconds.

## A second judging protocol: Aside

The same published browser-cmd run was also evaluated with [Aside's BU grader prompt](https://github.com/at-inc/aside-benchmarks/tree/7cde728f6af4ba10065fc9e0557762d0e156d3dd/bu-bench-v1/runner/grader.ts),
using trajectory text alone. With our existing manual failure rule applied to both protocols, it scores
**97 / 96 / 96 / 95** under GPT-5.5 / Gemini / Sol / Opus. No browser tasks were rerun.

**Passed** (also called counted) applies the same existing manual failure to both protocols. **Raw** preserves the model's decision.
Under Aside's prompt all four judges passed that task, so each counted score is one below its raw score.

The two evaluations use different evidence packages. Our original BU evaluation supplies a separate final answer
and the last ten screenshots. Aside's prompt receives trajectory text, omits the separate final-result block and
explicitly says not to penalize missing screenshots by itself. This is a less demanding evidence requirement, but
it does not make every judge's decisions uniformly more lenient. All task counts remain out of 100.

Using Gemini 2.5 Flash and Aside's prompt, our run scores **96/100 counted** (97 raw).
For context, Aside's own published BU results use the same judge model and prompt:

| System | Judge | Prompt | Score |
| --- | --- | --- | ---: |
| browser-cmd + gpt-6.1-sol + gpt-6.1-terra | Gemini 2.5 Flash | Aside | **96 / 100** |
| Aside + GPT-5.5 | Gemini 2.5 Flash | Aside | **93 / 100**, self-reported |
| Aside + Kimi K2.6 | Gemini 2.5 Flash | Aside | **88 / 100**, self-reported |

Aside's scores are their [published results](https://github.com/at-inc/aside-benchmarks/tree/7cde728f6af4ba10065fc9e0557762d0e156d3dd), not evaluations by us.
Actor models and run dates differ, so this comparison does not establish a controlled live-agent win rate.
The [full report](results/reports/20261108-judging-protocols.md) covers our two evaluations, category scores,
judge agreement and protocol details. Our [per-task verdicts](results/cross-judging/) and checksums can be recounted offline.

## Where this stands

Our best counted scores, **96 with BU prompts** and **97 with Aside's prompt**, exceed the other published scores
listed below. The table separates the two evaluations.

| System | BU evaluation | Aside prompt | Source |
| --- | ---: | ---: | --- |
| browser-cmd + gpt-6.1-sol + gpt-6.1-terra | **89–96** by judge | **95–97** by judge | this repository, counted scores |
| Aside + GPT-5.5 | — | **93** | [self-reported](https://github.com/at-inc/aside-benchmarks) |
| Aside + Kimi K2.6 | — | **88** | [self-reported](https://github.com/at-inc/aside-benchmarks) |
| BrowserCode + Claude Opus 4.8 | 89.5 | — | [benchmark repository](https://github.com/browser-use/benchmark) |
| BrowserCode + Claude Fable 5 | 87 | — | [benchmark repository](https://github.com/browser-use/benchmark) |
| Browser Use Cloud v4 + Opus | 85 | — | [benchmark repository](https://github.com/browser-use/benchmark) |

All scores are out of 100. A dash means no score is listed for that protocol. For browser-cmd, the two columns
cover the same run evaluated by four judges. Under Gemini 2.5 Flash specifically, our counted score is **96** with
either prompt; the **97** under Aside's prompt comes from GPT-5.5. Other systems' scores are their published figures.

Other systems' figures were checked on 31 October 2026; our additional judging was completed on 8 November.
These scores are not directly comparable: models, browsers, dates and judges differ, and the sites are live.
The benchmark's own V1 runs use a Gemini-family judge; the exact version is not stated where we looked, so Gemini
2.5 Flash is our nearest reading rather than a confirmed match. The ranges show judge variation and should not be
read as scores obtained with the same judge across all systems.

## Run protocol

1. **Tasks.** All 100 tasks of BU Bench V1, unchanged, with a limit of 3,600 seconds each and three running at once.
2. **A clean start per task.** A fresh Codex CLI 0.166.0 session (gpt-6.1-sol, reasoning effort high) in its own empty
   working directory, with no user skills, plugins, MCP servers or sub-agents. A fresh browser-cmd daemon and a fresh
   headless Chrome profile, with no cookies or sign-ins.
3. **What the agent gets.** The browser-cmd skill (`harness/runner/skills/lean/SKILL.md`), the task, the time budget
   and the answer rules (`harness/runner/run.py`, `harness/runner/bu_rules.txt`). Codex's own web search is allowed.
4. **Review.** A second model, gpt-6.1-terra, that cannot browse reads the task, the answer, the notes and the
   screenshot, and names what to fix.
5. **Network.** Eight tasks go through a US residential proxy, as do three retail and sports-data sites wherever a
   task reaches them. The rest go direct from outside the US.
6. **Original judging.** `harness/validation/judge.py`, using the prompts of the benchmark's `judge.py`. A leading `FINAL:` label
   is removed from the answer before judging. Trajectories keep head and tail rather than the head alone, because a
   shell trajectory runs longer than a Browser Use one and the head alone would hide how it ended.
7. **Additional judging.** The same saved trajectories were evaluated under Aside's prompt by the same four judge
   models, with no screenshots or separate final-result block. These are additional evaluations of the original run.

The actor and original judging configuration are pinned in [`browser-cmd.lock.json`](browser-cmd.lock.json);
the additional evaluation is recorded in [`results/cross-judging/manifest.json`](results/cross-judging/manifest.json). The measured source in
`snapshot/` is the build measured on [WebVoyager](https://github.com/elmyx-labs/browser-cmd-webvoyager); what
[browser-cmd v0.1.0](https://github.com/elmyx-labs/browser-cmd/releases/tag/v0.1.0) changes on top of it is listed in
[those release notes](https://github.com/elmyx-labs/browser-cmd-webvoyager/releases/tag/v0.1.0).

## What is and is not here

The benchmark asks that decrypted tasks not be published, so unlike our
[WebVoyager results](https://github.com/elmyx-labs/browser-cmd-webvoyager) this repository publishes **no task texts, trajectories,
final answers, screenshots or judge reasoning**. It has per-task verdicts by task id,
the runner and the evaluated browser-cmd source. The full evidence is kept privately; its checksum is in
`browser-cmd.lock.json`. All **eight current score sets** (four judges × two protocols) have public per-task
verdicts: **800 decisions** in total. Only Aside's own published aggregate scores are cited for comparison.

| Path | Contents |
| --- | --- |
| `results/tasks.csv` | Original run: category, seconds, proxy, timeout, manual exclusion and the four original verdicts |
| `results/judges/` | Our four original BU-protocol evaluations, by task id |
| `results/reports/` | Run report and cross-evaluation report |
| `results/cross-judging/` | Our four Aside-prompt evaluations, manifest referencing all eight score sets, checksums and summary |
| `browser-cmd.lock.json` | The evaluated system, pinned by checksum |
| `harness/` | The runner, reviewer, answer rules and judge |
| `snapshot/` | The evaluated browser-cmd source with its checksum |

## Verify it

```sh
python3 scripts/verify.py
```

Recounts our scores under both protocols from the per-task verdicts, including categories, agreement and
checksums. Other systems' published comparison scores remain attributed to their sources. No API key or network required.

## License

`harness/` and `scripts/` are Apache-2.0. BU Bench V1 belongs to its authors at
[browser-use/benchmark](https://github.com/browser-use/benchmark) and is not redistributed here.
