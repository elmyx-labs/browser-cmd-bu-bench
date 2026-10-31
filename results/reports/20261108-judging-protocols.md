# BU Bench V1: browser-cmd under two judging protocols

8 November 2026. The same published browser-cmd run, `bu100-20261031-full2`, evaluated by four judges under two
prompt/input packages. Each score covers all 100 tasks; no browser tasks were rerun.

## Our scores

| Judge | BU prompts: counted / raw | Aside prompt: counted / raw |
| --- | ---: | ---: |
| GPT-5.5 | 96 / 97 | 97 / 98 |
| Gemini 2.5 Flash | 96 / 97 | 96 / 97 |
| gpt-5.6-sol | 94 / 95 | 96 / 97 |
| Claude Opus 5.5 | 89 / 89 | 95 / 96 |


Counted scores apply the same existing manual failure to task `7966e6bd-f197-43d0-9ee5-88fab61c8c36` in both evaluations.
The agent obtained its result through an internal site host past a bot challenge, which we do not count as completing
the task. Raw verdicts are preserved unchanged. Under the Aside prompt all four judges passed that task.

## Protocol and evidence differences

| Input or instruction | Our original BU evaluation | Aside prompt evaluation |
| --- | --- | --- |
| Task and available ground truth | Included; 40 tasks have ground truth | Included; same dataset |
| Trajectory truncation | Head and tail, about 40k characters each | Head and tail, about 40k characters each |
| Separate final-result block | Actual final answer included | Omitted |
| Screenshots | Last ten screenshots | None |
| Missing-screenshot instruction | Original published BU wording | Explicitly do not penalize missing screenshots by itself |
| Judge models | GPT-5.5, Gemini 2.5 Flash, Sol, Opus | Same four models |

Both prompt families retain a failure condition for missing output. The Aside prompt evaluates the trajectory
without requiring a separately supplied final-answer block or screenshots. It is a less demanding evidence
requirement, but does not establish a universal ordering of judge strictness. Changing the input package also
changes the available evidence: the measured differences do not isolate one prompt instruction or one block.

## Published comparison

| System | Judge | Prompt | Counted score |
| --- | --- | --- | ---: |
| browser-cmd + gpt-6.1-sol + gpt-6.1-terra | Gemini 2.5 Flash | Aside | **96 / 100** |
| Aside + GPT-5.5 | Gemini 2.5 Flash | Aside | **93 / 100**, self-reported |
| Aside + Kimi K2.6 | Gemini 2.5 Flash | Aside | **88 / 100**, self-reported |

Aside's numbers are [self-reported](https://github.com/at-inc/aside-benchmarks/tree/7cde728f6af4ba10065fc9e0557762d0e156d3dd); they are not results of our own evaluation.
With the same prompt and Gemini judge, browser-cmd's counted score is 96/100, versus their published 93/100 and
88/100. Actor models and dates differ, and the sites are live. This is a comparison of published numbers with a
shared judging prompt/model, not a controlled live-agent experiment.

## Changes and agreement between our evaluations

| Judge | Change in raw passes | Same task verdicts / 100 |
| --- | ---: | ---: |
| GPT-5.5 | 1 | 99 |
| Gemini 2.5 Flash | 0 | 100 |
| gpt-5.6-sol | 2 | 98 |
| Claude Opus 5.5 | 7 | 93 |

## Agreement across four judges

| Protocol | All pass, raw | All pass, counted | All fail | Disagree |
| --- | ---: | ---: | ---: | ---: |
| bu-v1 | 87 | 87 | 2 | 11 |
| aside | 95 | 94 | 2 | 3 |

## Our category scores

Every category contains 20 tasks. These are raw verdicts. The manual failure belongs to WebBenchREAD.

### bu-v1

| Category | GPT-5.5 | Gemini 2.5 Flash | gpt-5.6-sol | Claude Opus 5.5 |
| --- | ---: | ---: | ---: | ---: |
| BrowseComp | 20 | 19 | 20 | 19 |
| GAIA | 20 | 20 | 20 | 20 |
| InteractionTests | 20 | 20 | 20 | 18 |
| OM2W2 | 19 | 20 | 19 | 17 |
| WebBenchREAD | 18 | 18 | 16 | 15 |

### aside

| Category | GPT-5.5 | Gemini 2.5 Flash | gpt-5.6-sol | Claude Opus 5.5 |
| --- | ---: | ---: | ---: | ---: |
| BrowseComp | 20 | 19 | 20 | 19 |
| GAIA | 20 | 20 | 20 | 20 |
| InteractionTests | 20 | 20 | 20 | 20 |
| OM2W2 | 20 | 20 | 19 | 19 |
| WebBenchREAD | 18 | 18 | 18 | 18 |

## Impossible-task flags

Flags do not change the denominator.

| Judge | BU prompts | Aside prompt |
| --- | ---: | ---: |
| GPT-5.5 | 2 | 2 |
| Gemini 2.5 Flash | 1 | 2 |
| gpt-5.6-sol | 2 | 2 |
| Claude Opus 5.5 | 4 | 2 |

## Interpretation

Our saved run remains strong across the tested prompt/judge combinations: 89–97 raw passes under the original BU
evaluation and 96–98 under the Aside prompt. With the same manual failure applied, the ranges are 89–96 and 95–97.
All four judges agree that 87 tasks pass under BU prompts and 94 counted tasks pass under the Aside prompt.

These are two evaluations of the same saved run, not two independent agent runs. Neither evaluation establishes
which judge is correct on each disputed task. The protocol comparison changes instructions and evidence together;
separate experiments would be needed to isolate their effects.

## Source and verification

Aside prompt source: [`bu-bench-v1/runner/grader.ts` at 7cde728](https://github.com/at-inc/aside-benchmarks/tree/7cde728f6af4ba10065fc9e0557762d0e156d3dd/bu-bench-v1/runner/grader.ts).
The source manifest, our sanitized verdicts and computed summary are in [`../cross-judging/`](../cross-judging/).
Only our task IDs and boolean verdict flags are exported. Task text, trajectories, final answers, screenshots and
judge reasoning remain outside this repository. Source and export checksums are included. The evaluated-system
lock and original actor results are unchanged.

Run from the repository root:

```sh
python3 scripts/verify.py
```

The check validates all 100 task IDs per file, flag-only schemas and export hashes, and recomputes our raw/counted
scores, categories, impossible flags, consensus and cross-protocol agreement. Other systems' published scores
are attributed to their sources rather than verified by this script.
