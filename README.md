<p align="center">
  <img alt="browser-cmd" src="docs/assets/logo.svg" width="360">
</p>

<p align="center">
  <strong>BU Bench V1 results: per-task verdicts of four judges and an account of every miss.</strong>
</p>

<p align="center">
  <img alt="BU Bench V1 96/100" src="https://img.shields.io/badge/BU%20Bench%20V1-96%2F100-0B0D12">
  <img alt="Four judges" src="https://img.shields.io/badge/4%20judges-89%E2%80%9396-0B0D12">
  <a href="https://github.com/elmyx-labs/browser-cmd"><img alt="browser-cmd" src="https://img.shields.io/badge/agent%20browser-browser--cmd-0B0D12"></a>
</p>

<p align="center">
  <a href="#results">Results</a> ·
  <a href="#where-this-stands">Position</a> ·
  <a href="#run-protocol">Protocol</a> ·
  <a href="#what-is-and-is-not-here">Published data</a> ·
  <a href="#verify-it">Verify</a> ·
  <a href="results/reports/20261031-codex-gpt-6.1-sol-report.md">Full report</a>
</p>

---

A Codex gpt-6.1-sol agent, reviewed by gpt-6.1-terra and driving a real Chrome through
[browser-cmd](https://github.com/elmyx-labs/browser-cmd), scores **96/100** on
[BU Bench V1](https://github.com/browser-use/benchmark) under GPT-5.5 and Gemini 2.5 Flash, 94/100 under gpt-5.6-sol
and 89/100 under Claude Opus 5.5. This is our own run, not an official entry: BU Bench V1 has no public leaderboard
or submission process.

## Results

| Judge | Passed | As judged |
| --- | ---: | ---: |
| GPT-5.5 | **96 / 100** | 97 |
| Gemini 2.5 Flash | **96 / 100** | 97 |
| gpt-5.6-sol | **94 / 100** | 95 |
| Claude Opus 5.5 | **89 / 100** | 89 |

All four judges use the benchmark's published judge prompts, its ground truth where a task has one, and the last ten
screenshots. They agree that 87 tasks pass.

**Passed** treats one task as failed whatever the judges said: the agent reached its result through a site's internal
host, past a bot challenge, which we do not count as completing the task. **As judged** is the judge's own count. No
other verdict is changed.

| Category | GPT-5.5 | Gemini 2.5 Flash | gpt-5.6-sol | Claude Opus 5.5 |
| --- | ---: | ---: | ---: | ---: |
| BrowseComp | 20 / 20 | 19 / 20 | 20 / 20 | 19 / 20 |
| GAIA | 20 / 20 | 20 / 20 | 20 / 20 | 20 / 20 |
| InteractionTests | 20 / 20 | 20 / 20 | 20 / 20 | 18 / 20 |
| OM2W2 | 19 / 20 | 20 / 20 | 19 / 20 | 17 / 20 |
| WebBenchREAD | 17 / 20 | 17 / 20 | 15 / 20 | 15 / 20 |

The median task takes 263 seconds.

## Where this stands

To our knowledge this is the highest score published for BU Bench V1. Treat that as a cautious reading, not a ranking.

| System | Score | Source |
| --- | ---: | --- |
| browser-cmd + gpt-6.1-sol + gpt-6.1-terra | 89–96 by judge | this repository |
| Aside + GPT-5.5 | 93 | [self-reported](https://github.com/at-inc/aside-benchmarks) |
| BrowserCode + Claude Opus 4.8 | 89.5 | [benchmark repository](https://github.com/browser-use/benchmark) |
| BrowserCode + Claude Fable 5 | 87 | [benchmark repository](https://github.com/browser-use/benchmark) |
| Browser Use Cloud v4 + Opus | 85 | [benchmark repository](https://github.com/browser-use/benchmark) |

Numbers were checked on 31 October 2026 and others may have appeared since. These scores are not directly comparable:
models, browsers, dates and judges differ, and the sites are live. The benchmark's own V1 runs use a Gemini-family
judge; the exact version is not stated where we looked, so Gemini 2.5 Flash is our nearest reading rather than a
confirmed match. The Opus score should not be set against the others: it comes from a judge they were not scored with.

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
6. **Judging.** `harness/validation/judge.py`, using the prompts of the benchmark's `judge.py`. A leading `FINAL:` label
   is removed from the answer before judging. Trajectories keep head and tail rather than the head alone, because a
   shell trajectory runs longer than a Browser Use one and the head alone would hide how it ended.

The exact configuration is pinned in [`browser-cmd.lock.json`](browser-cmd.lock.json). The measured source in
`snapshot/` is the build measured on [WebVoyager](https://github.com/elmyx-labs/browser-cmd-webvoyager); what
[browser-cmd v0.1.0](https://github.com/elmyx-labs/browser-cmd/releases/tag/v0.1.0) changes on top of it is listed in
[those release notes](https://github.com/elmyx-labs/browser-cmd-webvoyager/releases/tag/v0.1.0).

## What is and is not here

The benchmark asks that decrypted tasks not be published, so unlike our
[WebVoyager results](https://github.com/elmyx-labs/browser-cmd-webvoyager) this repository has **no trajectories,
prompts, answers, screenshots or judge reasoning**: all of them quote the tasks. It has per-task verdicts by task id,
the runner and the evaluated browser-cmd source. The full evidence is kept privately; its checksum is in
`browser-cmd.lock.json`.

| Path | Contents |
| --- | --- |
| `results/tasks.csv` | One row per task: category, seconds, proxy, timeout and each judge's verdict |
| `results/judges/` | Each judge's verdict by task id |
| `results/reports/` | The full report |
| `browser-cmd.lock.json` | The evaluated system, pinned by checksum |
| `harness/` | The runner, reviewer, answer rules and judge |
| `snapshot/` | The evaluated browser-cmd source with its checksum |

## Verify it

```sh
python3 scripts/verify.py
```

Recounts every score above from the per-judge verdicts. No API key, no network, a few seconds.

## License

`harness/` and `scripts/` are Apache-2.0. BU Bench V1 belongs to its authors at
[browser-use/benchmark](https://github.com/browser-use/benchmark) and is not redistributed here.
