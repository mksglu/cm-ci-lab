# Issue dedupe benchmark (2026-10-31, clean re-run)

Area: issue dedupe. Sonnet 5.5, headless `claude -p` (native installer), arms `direct-ts` (direct API + ENABLE_TOOL_SEARCH) and `gateway`. Workflow `.github/workflows/dedupe.yml`. Nothing here is published.

History: the first run of this bench (tags `a1031-dedupe-sonnet-r1`, `r2`) was invalid, because the lab tenant `t_ci_lab_1` was paused at 2026-10-31 10:29:57 UTC and the gateway arm ran as plain pass-through. This doc is the clean re-run (tags `c1031-dedupe-sonnet-r1`, `r2`) with the tenant in full mode.

## Result: the pass bar is NOT met

Bar, fixed in advance: task-resampled CI upper bound < 0, quality not lower than direct-ts, 0 errors, every round valid.

| bar | result |
|---|---|
| every round valid | yes. `used_paused` was 1518 before round 1, between the rounds and after round 2 (unchanged). Request 1 on the gateway arm is 37% smaller than on direct-ts (10,556 vs 16,655 tokens, all 24 runs on each side within 14 tokens of the mean), so the gateway was in full mode. |
| CI upper bound < 0 | NO. Cost change -24.1%, task-resampled 95% CI -48.2% to +2.6% (12 tasks, 10,000 resamples, seed 1). Cheaper in 16 of 24 pairs. |
| quality not lower | yes. Original in the agent's top 3: 19/24 on both arms. McNemar exact p = 1.000 (2 direct-only, 2 gateway-only). |
| 0 errors | yes, 0 errors, no "Credit balance is too low". |
| net per run > 0 | point estimate yes, not proven. Net = 0.2443 - 0.1975 - 0.0009 x 28.0 requests = +$0.0215 per run (+$0.0428 if the fee is counted per Claude turn, 4.5, instead of per request). The CI for the cost change includes zero, so this net is not shown to be real. |

Honest reading: the point estimate is a saving, and the first request is clearly smaller. But the CI crosses zero, so by the fixed bar issue dedupe is not proven. The headline is helped by one task: on bun-36967 both gateway runs (r1 and r2) skipped the subagent fan-out (6 requests, no subagent, $0.03 each), while direct-ts used 19 to 23 requests and $0.19 to $0.24. Without that task (22 pairs) the change is -11.6%, 95% CI -26.9% to +10.2%. Both numbers are in the data; neither passes the bar. Per-pair results range from -86% to +118%, and the CI is about 25 points wide each side, so a true saving of 10 to 25% cannot be separated from zero with 12 tasks.

## Numbers

Pairs are (task, round). Paired log-ratio mean = -0.2757, shown as exp(mean)-1.

| arm | top-3 hit | errors | mean cost | requests / run | turns / run | uncached | cache_write | cache_read | output |
|---|---|---|---|---|---|---|---|---|---|
| direct-ts | 19/24 | 0 | $0.2443 | 26.0 | 6.29 | 55 | 61,772 | 372,085 | 9,810 |
| gateway | 19/24 | 0 | $0.1975 | 28.0 | 4.46 | 3,249 | 37,558 | 302,619 | 8,793 |

Tokens are the mean per run from `modelUsage` in the final result (main agent and subagents, the same source as `total_cost_usd`). Cost is the `total_cost_usd` that Claude Code reports. Note: the streamed per-message usage shows `output_tokens` 0 on every gateway-arm message (the stream carries the start-of-message value only), so `lab/dedupe/analyze.py` now takes tokens from `modelUsage` instead.

Request 1 (first main-agent request, input + cache_write + cache_read): direct-ts 16,655 tokens (2 + 4,444 + 12,209), gateway 10,556 tokens (499 + 1,499 + 8,558). Script: `lab/dedupe/req1.py`.

Total model spend: $10.60 for the 48 runs, under the $15 cap.

## Method

- Template mirrored: anthropics/claude-code `claude-dedupe-issues.yml` (the most-starred dedupe template). Same command file `.claude/commands/dedupe.md` (`lab/dedupe/commands/dedupe.md`), same prompt `/dedupe <repo>/issues/<n>`, same tools (`./scripts/gh.sh`, `./scripts/comment-on-duplicates.sh`) and same disallowed tools. Differences: `claude -p` instead of claude-code-action, model claude-sonnet-5-5 instead of claude-sonnet-4-6, no `--permission-mode auto`, `--max-turns 60 --max-budget-usd 2`.
- Time box: `lab/dedupe/scripts/gh.sh` shows only the world before the target. Search and list queries get `created:<DATE`, results at or after DATE are dropped, comments at or after DATE are dropped (this hides the maintainer verdict), and the target shows as OPEN with title and body only.
- Posting is stubbed: `comment-on-duplicates.sh` prints the action and writes the numbers to a file. The lab writes to no other repo.
- Quality is objective: the maintainer-confirmed original is in the agent's top 3 (the order passed to the comment script). The score is read from a file by script.
- Stats: `lab/dedupe/analyze.py`. Pairs by (task, round). Bootstrap resamples tasks, all rounds of a task together.
- Arms and headers: `lab/path-env.sh` (the lines `ci init` writes).
- Validity: `python3 /tmp/ci-quota-guard.py --need 3000` before each round and after round 2. Mode full, `used_paused` 1518 each time.

## Tasks (12 real closed-as-duplicate issues, 5 repos, all above 93k stars)

Source: GitHub search `reason:duplicate`, then the closing comment by a human maintainer names the original (bot closers excluded). Every original was created before its duplicate. For uptime-kuma GraphQL `duplicateOf` was also set.

| task | repo (stars) | duplicate | true original | original created | closed by |
|---|---|---|---|---|---|
| bun-37251 | oven-sh/bun (96.5k) | #37251 | #16834 | 2025-01-28 | Jarred-Sumner |
| bun-37028 | oven-sh/bun (96.5k) | #37028 | #19059 | 2025-04-16 | Jarred-Sumner |
| bun-36967 | oven-sh/bun (96.5k) | #36967 | #23420 | 2025-10-10 | Jarred-Sumner |
| claude-code-104074 | anthropics/claude-code (154.0k) | #104074 | #93201 | 2026-09-09 | bpasero-ant |
| claude-code-103661 | anthropics/claude-code (154.0k) | #103661 | #89673 | 2026-08-26 | bpasero-ant |
| claude-code-103645 | anthropics/claude-code (154.0k) | #103645 | #99395 | 2026-10-04 | bpasero-ant |
| codex-52463 | openai/codex (132.3k) | #52463 | #48664 | 2026-09-27 | etraut-openai |
| codex-50880 | openai/codex (132.3k) | #50880 | #35177 | 2026-07-24 | etraut-openai |
| codex-53191 | openai/codex (132.3k) | #53191 | #33240 | 2026-07-15 | etraut-openai |
| gemini-cli-25559 | google-gemini/gemini-cli (108.6k) | #25559 | #21622 | 2026-03-08 | Adib234 |
| gemini-cli-25618 | google-gemini/gemini-cli (108.6k) | #25618 | #22029 | 2026-03-11 | Adib234 |
| uptime-kuma-6474 | louislam/uptime-kuma (93.1k) | #6474 | #1888 | 2022-07-12 | CommanderStorm |

## Per pair

Cost / API requests / original in top 3.

| task | round | direct-ts | gateway | direct-ts run | gateway run |
|---|---|---|---|---|---|
| bun-36967 | r1 | $0.2360 / 23 / yes | $0.0324 / 6 / yes | [41200834063](https://github.com/mksglu/cm-ci-lab/actions/runs/41200834063) | [41200837935](https://github.com/mksglu/cm-ci-lab/actions/runs/41200837935) |
| bun-36967 | r2 | $0.1900 / 19 / no | $0.0279 / 6 / yes | [41201848699](https://github.com/mksglu/cm-ci-lab/actions/runs/41201848699) | [41201852515](https://github.com/mksglu/cm-ci-lab/actions/runs/41201852515) |
| bun-37028 | r1 | $0.1056 / 23 / yes | $0.2303 / 33 / yes | [41200826183](https://github.com/mksglu/cm-ci-lab/actions/runs/41200826183) | [41200829939](https://github.com/mksglu/cm-ci-lab/actions/runs/41200829939) |
| bun-37028 | r2 | $0.1224 / 38 / yes | $0.2390 / 37 / yes | [41201840690](https://github.com/mksglu/cm-ci-lab/actions/runs/41201840690) | [41201844721](https://github.com/mksglu/cm-ci-lab/actions/runs/41201844721) |
| bun-37251 | r1 | $0.4742 / 36 / yes | $0.2861 / 34 / yes | [41200818554](https://github.com/mksglu/cm-ci-lab/actions/runs/41200818554) | [41200822437](https://github.com/mksglu/cm-ci-lab/actions/runs/41200822437) |
| bun-37251 | r2 | $0.1356 / 29 / yes | $0.1667 / 23 / yes | [41201832444](https://github.com/mksglu/cm-ci-lab/actions/runs/41201832444) | [41201836485](https://github.com/mksglu/cm-ci-lab/actions/runs/41201836485) |
| claude-code-103645 | r1 | $0.2860 / 26 / yes | $0.1050 / 32 / no | [41200857173](https://github.com/mksglu/cm-ci-lab/actions/runs/41200857173) | [41200861075](https://github.com/mksglu/cm-ci-lab/actions/runs/41200861075) |
| claude-code-103645 | r2 | $0.2308 / 19 / yes | $0.2691 / 25 / yes | [41201871499](https://github.com/mksglu/cm-ci-lab/actions/runs/41201871499) | [41201875697](https://github.com/mksglu/cm-ci-lab/actions/runs/41201875697) |
| claude-code-103661 | r1 | $0.2515 / 24 / yes | $0.2685 / 35 / yes | [41200849190](https://github.com/mksglu/cm-ci-lab/actions/runs/41200849190) | [41200853217](https://github.com/mksglu/cm-ci-lab/actions/runs/41200853217) |
| claude-code-103661 | r2 | $0.3072 / 33 / yes | $0.2647 / 29 / yes | [41201864277](https://github.com/mksglu/cm-ci-lab/actions/runs/41201864277) | [41201867951](https://github.com/mksglu/cm-ci-lab/actions/runs/41201867951) |
| claude-code-104074 | r1 | $0.2286 / 23 / no | $0.1000 / 29 / yes | [41200841721](https://github.com/mksglu/cm-ci-lab/actions/runs/41200841721) | [41200845363](https://github.com/mksglu/cm-ci-lab/actions/runs/41200845363) |
| claude-code-104074 | r2 | $0.2768 / 26 / yes | $0.2446 / 33 / yes | [41201856366](https://github.com/mksglu/cm-ci-lab/actions/runs/41201856366) | [41201860111](https://github.com/mksglu/cm-ci-lab/actions/runs/41201860111) |
| codex-50880 | r1 | $0.2119 / 20 / no | $0.1886 / 26 / no | [41200873282](https://github.com/mksglu/cm-ci-lab/actions/runs/41200873282) | [41200877395](https://github.com/mksglu/cm-ci-lab/actions/runs/41200877395) |
| codex-50880 | r2 | $0.2071 / 22 / no | $0.2329 / 27 / no | [41201888422](https://github.com/mksglu/cm-ci-lab/actions/runs/41201888422) | [41201893109](https://github.com/mksglu/cm-ci-lab/actions/runs/41201893109) |
| codex-52463 | r1 | $0.4967 / 40 / yes | $0.2314 / 26 / yes | [41200865053](https://github.com/mksglu/cm-ci-lab/actions/runs/41200865053) | [41200869144](https://github.com/mksglu/cm-ci-lab/actions/runs/41200869144) |
| codex-52463 | r2 | $0.2159 / 20 / yes | $0.2079 / 30 / yes | [41201879696](https://github.com/mksglu/cm-ci-lab/actions/runs/41201879696) | [41201883659](https://github.com/mksglu/cm-ci-lab/actions/runs/41201883659) |
| codex-53191 | r1 | $0.2347 / 23 / yes | $0.1909 / 28 / yes | [41200881571](https://github.com/mksglu/cm-ci-lab/actions/runs/41200881571) | [41200885513](https://github.com/mksglu/cm-ci-lab/actions/runs/41200885513) |
| codex-53191 | r2 | $0.2627 / 27 / yes | $0.2092 / 27 / yes | [41201897286](https://github.com/mksglu/cm-ci-lab/actions/runs/41201897286) | [41201901319](https://github.com/mksglu/cm-ci-lab/actions/runs/41201901319) |
| gemini-cli-25559 | r1 | $0.2565 / 25 / yes | $0.1791 / 25 / yes | [41200889688](https://github.com/mksglu/cm-ci-lab/actions/runs/41200889688) | [41200893578](https://github.com/mksglu/cm-ci-lab/actions/runs/41200893578) |
| gemini-cli-25559 | r2 | $0.2164 / 20 / yes | $0.2900 / 43 / yes | [41201905239](https://github.com/mksglu/cm-ci-lab/actions/runs/41201905239) | [41201910409](https://github.com/mksglu/cm-ci-lab/actions/runs/41201910409) |
| gemini-cli-25618 | r1 | $0.2467 / 25 / no | $0.2195 / 29 / no | [41200897716](https://github.com/mksglu/cm-ci-lab/actions/runs/41200897716) | [41200901402](https://github.com/mksglu/cm-ci-lab/actions/runs/41200901402) |
| gemini-cli-25618 | r2 | $0.1494 / 38 / yes | $0.2459 / 31 / yes | [41201914387](https://github.com/mksglu/cm-ci-lab/actions/runs/41201914387) | [41201918651](https://github.com/mksglu/cm-ci-lab/actions/runs/41201918651) |
| uptime-kuma-6474 | r1 | $0.3240 / 25 / yes | $0.2002 / 30 / yes | [41200905167](https://github.com/mksglu/cm-ci-lab/actions/runs/41200905167) | [41200908778](https://github.com/mksglu/cm-ci-lab/actions/runs/41200908778) |
| uptime-kuma-6474 | r2 | $0.1958 / 20 / yes | $0.1103 / 29 / no | [41201922180](https://github.com/mksglu/cm-ci-lab/actions/runs/41201922180) | [41201926169](https://github.com/mksglu/cm-ci-lab/actions/runs/41201926169) |

Per-run files, with the per-message usage list and `modelUsage`, are in `lab/dedupe/results/<run id>.json`. Full analysis output: `lab/dedupe/analysis.txt`.

## Anatomy (2 tasks, per request and per arm)

Full tables: `lab/dedupe/anatomy-bun-36967-r1.txt` and `lab/dedupe/anatomy-bun-37251-r1.txt`. The output column of the gateway arm in these files reads 0 for the stream reason above; use the `modelUsage` totals for output.

- bun-36967 r1: direct-ts run 41200834063, $0.2360, 23 requests (13 subagent). Gateway run 41200837935, $0.0324, 6 requests, no subagent. The gateway main agent answered after a few searches without launching the parallel subagents that the dedupe command asks for. Quality was the same (original found in both). This is agent behavior, not a gateway saving on bytes, and it repeated in r2.
- bun-37251 r1: direct-ts $0.4742, 36 requests (26 subagent). Gateway $0.2861, 34 requests (21 subagent). Main cache write 27,126 vs 28,500 and main cache read 258,174 vs 233,425 tokens; the subagent loops write 72,967 vs 27,732 cache tokens.

What the data shows:

- The dedupe command fans out. The main agent starts parallel subagents, and about 60% of requests are subagent requests (about 16.5 of 26 on direct-ts, 16.8 of 28 on gateway). Subagents ran on Sonnet 5.5 and Haiku 5.5.
- Where the gateway saves: the fixed prefix. Request 1 is 37% smaller (10.6k vs 16.7k), and cache write falls from 61.8k to 37.6k tokens per run, cache read from 372k to 303k. The gateway arm sends more uncached input (3.2k vs 55 tokens per run), which costs little.
- Where it does not: new tool results (search output, issue bodies) are the same bytes in both arms. The gateway arm made 2 more requests per run, so the fee is larger there.
- Cost varies more between runs of one arm than between arms (direct-ts $0.11 to $0.50, gateway $0.03 to $0.29). That variance is why the CI is wide.

## What this means for selling

- Dedupe is an area with a likely saving (point estimate -24%, request 1 -37%) that this bench cannot prove. Do not publish a number from it. A bench with more tasks or more rounds is needed: about 4x the pairs would narrow the CI to roughly half its width.
- Quality is not hurt: 19/24 on both arms.
- At $0.0009 per request, net is +$0.0215 per run at the point estimate, and negative if the true saving is below about 10%, because the gateway arm makes about 28 requests per run.

## Limits

- 12 tasks, 2 rounds. Not enough to rule out a zero saving.
- Model differs from the real template (Sonnet 5.5, not 4.6). The real template runs on an egress-firewall runner and posts a comment; this lab does neither.
- Cost is the client-reported `total_cost_usd` for both arms; the Haiku subagent share is included.
- Agent behavior varies: two of 24 gateway runs skipped the fan-out.
