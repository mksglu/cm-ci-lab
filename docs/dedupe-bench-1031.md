> **INVALID: do not use the numbers below.** The lab tenant `t_ci_lab_1` used up its 1,000 free requests and was paused at 2026-10-31 10:29:57 UTC. A paused tenant gets plain pass-through: the gateway forwards the request unchanged, with no savings. 25 of the 25 gateway-arm runs behind this doc started after that time, so this doc compares direct with a paused pass-through, not with the gateway. The tenant is back in full mode and a clean re-run is in progress. Note added 2026-10-31.

# Issue dedupe benchmark (2026-10-31)

Area: issue dedupe. Sonnet 5.5, headless `claude -p` (native installer), arms `direct-ts` (direct API + ENABLE_TOOL_SEARCH) and `gateway`. Workflow `.github/workflows/dedupe.yml`. Nothing here is published.

## Result: the pass bar is NOT met

Bar, fixed in advance: task-resampled CI upper bound < 0, quality not lower than direct-ts, 0 errors.

| bar | result |
|---|---|
| CI upper bound < 0 | NO. Cost change +0.8%, task-resampled 95% CI -14.0% to +17.4% (12 tasks, 10,000 resamples, seed 1). Cheaper in 12 of 24 pairs. |
| quality not lower | yes. Original in the agent's top 3: gateway 19/24, direct-ts 17/24. McNemar exact p = 0.727 (3 direct-only, 5 gateway-only). |
| 0 errors | yes, 0 errors, no "Credit balance is too low". |
| net per run > 0 | NO. Net = 0.2302 - 0.2327 - 0.0009 x 26.1 requests = -$0.0260 per run (-$0.0076 if the fee is counted per Claude turn, 5.7, instead of per request). |

Honest reading: for issue dedupe the gateway does not save money in this lab. The data does not show a cost increase either: the CI spans zero, and per-task results range from -41% to +68%. With 12 tasks the CI is about 16 points wide each side, so a true saving smaller than that cannot be shown.

## Numbers

Pairs are (task, round). Paired log-ratio mean = 0.0078, shown as exp(mean)-1.

| arm | top-3 hit | errors | mean cost | requests / run | turns / run | uncached | cache_write | cache_read | output |
|---|---|---|---|---|---|---|---|---|---|
| direct-ts | 17/24 | 0 | $0.2302 | 23.5 | 5.83 | 47 | 51,758 | 315,966 | 2,346 |
| gateway | 19/24 | 0 | $0.2327 | 26.1 | 5.71 | 52 | 54,325 | 364,922 | 1,822 |

Tokens are mean per run summed over every API request, main agent and subagents (from the per-message usage list, de-duplicated by message id). Cost is the `total_cost_usd` that Claude Code reports.

Total model spend: $11.11 for the 48 runs plus $0.33 for one smoke run = $11.44, under the $15 cap.

## Method

- Template mirrored: anthropics/claude-code `claude-dedupe-issues.yml` (154k stars, the most-starred dedupe template). Same command file `.claude/commands/dedupe.md` (copied verbatim, `lab/dedupe/commands/dedupe.md`), same prompt `/dedupe <repo>/issues/<n>`, same tools (`./scripts/gh.sh`, `./scripts/comment-on-duplicates.sh`) and same disallowed tools (WebFetch, WebSearch, Write, Edit, MultiEdit, NotebookEdit). Differences: `claude -p` instead of claude-code-action (that action cannot use this key), model claude-sonnet-5-5 instead of claude-sonnet-4-6, no `--permission-mode auto`, `--max-turns 60 --max-budget-usd 2`.
- Time box: `lab/dedupe/scripts/gh.sh` shows only the world before the target. Search and list queries get `created:<DATE`, results at or after DATE are dropped, comments at or after DATE are dropped (this hides the maintainer verdict), and the target shows as OPEN with title and body only. A request for a later issue returns "not found".
- Posting is stubbed: `comment-on-duplicates.sh` prints the action and writes the numbers to a file. The lab writes to no other repo.
- Quality is objective: the maintainer-confirmed original is in the agent's top 3 (the order the agent passed to the comment script). No judge is needed, so no label hiding is needed; the score is read from a file by script.
- Stats: `lab/dedupe/analyze.py`. Pairs by (task, round). Bootstrap resamples tasks, all rounds of a task together.
- Arms and headers: `lab/path-env.sh` (the lines `ci init` writes). Tags `a1031-dedupe-sonnet-r1`, `r2`.

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
| bun-36967 | r1 | $0.1580 / 36 / yes | $0.2548 / 24 / yes | [41193641690](https://github.com/mksglu/cm-ci-lab/actions/runs/41193641690) | [41193650982](https://github.com/mksglu/cm-ci-lab/actions/runs/41193650982) |
| bun-36967 | r2 | $0.2150 / 25 / yes | $0.1774 / 20 / no | [41194627318](https://github.com/mksglu/cm-ci-lab/actions/runs/41194627318) | [41194638177](https://github.com/mksglu/cm-ci-lab/actions/runs/41194638177) |
| bun-37028 | r1 | $0.1758 / 17 / no | $0.1877 / 18 / yes | [41193623213](https://github.com/mksglu/cm-ci-lab/actions/runs/41193623213) | [41193632566](https://github.com/mksglu/cm-ci-lab/actions/runs/41193632566) |
| bun-37028 | r2 | $0.2267 / 22 / yes | $0.2100 / 21 / yes | [41194605993](https://github.com/mksglu/cm-ci-lab/actions/runs/41194605993) | [41194616541](https://github.com/mksglu/cm-ci-lab/actions/runs/41194616541) |
| bun-37251 | r1 | $0.1748 / 40 / yes | $0.2858 / 30 / yes | [41193603122](https://github.com/mksglu/cm-ci-lab/actions/runs/41193603122) | [41193613533](https://github.com/mksglu/cm-ci-lab/actions/runs/41193613533) |
| bun-37251 | r2 | $0.2208 / 24 / yes | $0.3824 / 29 / yes | [41194586473](https://github.com/mksglu/cm-ci-lab/actions/runs/41194586473) | [41194596088](https://github.com/mksglu/cm-ci-lab/actions/runs/41194596088) |
| claude-code-103645 | r1 | $0.2164 / 20 / yes | $0.2229 / 21 / yes | [41193945937](https://github.com/mksglu/cm-ci-lab/actions/runs/41193945937) | [41193956013](https://github.com/mksglu/cm-ci-lab/actions/runs/41193956013) |
| claude-code-103645 | r2 | $0.2260 / 24 / no | $0.1869 / 20 / no | [41194889324](https://github.com/mksglu/cm-ci-lab/actions/runs/41194889324) | [41194899984](https://github.com/mksglu/cm-ci-lab/actions/runs/41194899984) |
| claude-code-103661 | r1 | $0.1944 / 17 / yes | $0.1405 / 33 / yes | [41193927311](https://github.com/mksglu/cm-ci-lab/actions/runs/41193927311) | [41193936712](https://github.com/mksglu/cm-ci-lab/actions/runs/41193936712) |
| claude-code-103661 | r2 | $0.1985 / 20 / yes | $0.2974 / 22 / yes | [41194866378](https://github.com/mksglu/cm-ci-lab/actions/runs/41194866378) | [41194879706](https://github.com/mksglu/cm-ci-lab/actions/runs/41194879706) |
| claude-code-104074 | r1 | $0.1927 / 17 / yes | $0.2627 / 28 / yes | [41193660428](https://github.com/mksglu/cm-ci-lab/actions/runs/41193660428) | [41193670538](https://github.com/mksglu/cm-ci-lab/actions/runs/41193670538) |
| claude-code-104074 | r2 | $0.2219 / 19 / yes | $0.1737 / 30 / yes | [41194647609](https://github.com/mksglu/cm-ci-lab/actions/runs/41194647609) | [41194657703](https://github.com/mksglu/cm-ci-lab/actions/runs/41194657703) |
| codex-50880 | r1 | $0.3071 / 25 / yes | $0.2181 / 22 / no | [41193986045](https://github.com/mksglu/cm-ci-lab/actions/runs/41193986045) | [41193995330](https://github.com/mksglu/cm-ci-lab/actions/runs/41193995330) |
| codex-50880 | r2 | $0.3352 / 24 / yes | $0.1894 / 31 / no | [41194930453](https://github.com/mksglu/cm-ci-lab/actions/runs/41194930453) | [41194939719](https://github.com/mksglu/cm-ci-lab/actions/runs/41194939719) |
| codex-52463 | r1 | $0.3387 / 29 / yes | $0.2360 / 25 / yes | [41193966027](https://github.com/mksglu/cm-ci-lab/actions/runs/41193966027) | [41193975850](https://github.com/mksglu/cm-ci-lab/actions/runs/41193975850) |
| codex-52463 | r2 | $0.2316 / 23 / yes | $0.2915 / 34 / yes | [41194909949](https://github.com/mksglu/cm-ci-lab/actions/runs/41194909949) | [41194921062](https://github.com/mksglu/cm-ci-lab/actions/runs/41194921062) |
| codex-53191 | r1 | $0.1887 / 18 / no | $0.2203 / 20 / yes | [41194240720](https://github.com/mksglu/cm-ci-lab/actions/runs/41194240720) | [41194251074](https://github.com/mksglu/cm-ci-lab/actions/runs/41194251074) |
| codex-53191 | r2 | $0.2515 / 27 / yes | $0.2500 / 23 / yes | [41195153822](https://github.com/mksglu/cm-ci-lab/actions/runs/41195153822) | [41195165247](https://github.com/mksglu/cm-ci-lab/actions/runs/41195165247) |
| gemini-cli-25559 | r1 | $0.1891 / 20 / no | $0.1860 / 39 / yes | [41194261867](https://github.com/mksglu/cm-ci-lab/actions/runs/41194261867) | [41194271739](https://github.com/mksglu/cm-ci-lab/actions/runs/41194271739) |
| gemini-cli-25559 | r2 | $0.2169 / 21 / yes | $0.2830 / 17 / yes | [41195175614](https://github.com/mksglu/cm-ci-lab/actions/runs/41195175614) | [41195185859](https://github.com/mksglu/cm-ci-lab/actions/runs/41195185859) |
| gemini-cli-25618 | r1 | $0.3754 / 27 / no | $0.1436 / 42 / yes | [41194281142](https://github.com/mksglu/cm-ci-lab/actions/runs/41194281142) | [41194290887](https://github.com/mksglu/cm-ci-lab/actions/runs/41194290887) |
| gemini-cli-25618 | r2 | $0.2783 / 30 / no | $0.2526 / 25 / no | [41195196602](https://github.com/mksglu/cm-ci-lab/actions/runs/41195196602) | [41195207001](https://github.com/mksglu/cm-ci-lab/actions/runs/41195207001) |
| uptime-kuma-6474 | r1 | $0.1895 / 19 / no | $0.2289 / 28 / yes | [41194300701](https://github.com/mksglu/cm-ci-lab/actions/runs/41194300701) | [41194310722](https://github.com/mksglu/cm-ci-lab/actions/runs/41194310722) |
| uptime-kuma-6474 | r2 | $0.2024 / 20 / yes | $0.3040 / 25 / yes | [41195217434](https://github.com/mksglu/cm-ci-lab/actions/runs/41195217434) | [41195228816](https://github.com/mksglu/cm-ci-lab/actions/runs/41195228816) |

Per-run files, with the per-message usage list, are in `lab/dedupe/results/<run id>.json`. Full analysis output: `lab/dedupe/analysis.txt`.

## Anatomy (2 tasks, per request and per arm)

Full per-request tables: `lab/dedupe/anatomy-bun-37251-r2.txt` and `lab/dedupe/anatomy-gemini-cli-25618-r1.txt`. Totals, with list-price dollars by token class:

```
== bun-37251 r2 direct-ts run 41194586473 cost $0.2208 requests 24 (sub 14)
    main totals {'in': 20, 'cw': 17513, 'cr': 223382, 'out': 553}  list-price $ uncached=0.0001 write=0.0657 read=0.0670 output=0.0083
    sub  totals {'in': 28, 'cw': 27729, 'cr': 113461, 'out': 2049}  list-price $ uncached=0.0001 write=0.1040 read=0.0340 output=0.0307
== bun-37251 r2 gateway run 41194596088 cost $0.3824 requests 29 (sub 24)
    main totals {'in': 10, 'cw': 14355, 'cr': 98861, 'out': 431}  list-price $ uncached=0.0000 write=0.0538 read=0.0297 output=0.0065
    sub  totals {'in': 48, 'cw': 36702, 'cr': 248933, 'out': 513}  list-price $ uncached=0.0001 write=0.1376 read=0.0747 output=0.0077
== gemini-cli-25618 r1 direct-ts run 41194281142 cost $0.3754 requests 27 (sub 19)
    main totals {'in': 16, 'cw': 18745, 'cr': 186740, 'out': 486}  list-price $ uncached=0.0000 write=0.0703 read=0.0560 output=0.0073
    sub  totals {'in': 38, 'cw': 49679, 'cr': 193537, 'out': 2110}  list-price $ uncached=0.0001 write=0.1863 read=0.0581 output=0.0316
== gemini-cli-25618 r1 gateway run 41194290887 cost $0.1436 requests 42 (sub 30)
    main totals {'in': 24, 'cw': 20587, 'cr': 294743, 'out': 533}  list-price $ uncached=0.0001 write=0.0772 read=0.0884 output=0.0080
    sub  totals {'in': 60, 'cw': 66087, 'cr': 322637, 'out': 231}  list-price $ uncached=0.0002 write=0.2478 read=0.0968 output=0.0035
```

What the data shows:

- The dedupe command fans out. The main agent starts 5 parallel subagents. Subagent requests ran on Sonnet 5.5 (602 requests) and Haiku 5.5 (149 requests); the main agent ran on Sonnet 5.5 (440 requests). A run is 17 to 42 API requests, and about two thirds are subagent requests.
- Where the gateway did NOT save: the first request is the same in both arms (cache write median 4,388, write plus read median 16,653 in both). The client prefix here is small, about 16.7k tokens, so there was no big prefix to shrink. Each subagent also starts with the same small prefix in both arms (cache write about 3.3k, cache read about 6.1k).
- Where the money goes: cache writes of new tool results in the subagent loops (search output, issue bodies) and cache reads of the growing history. These bytes are the same in both arms.
- The gateway arm made more requests (26.1 vs 23.5 per run) and read more cache (365k vs 316k). It wrote less output (1,822 vs 2,346), because its subagents answered with fewer tokens. These two effects cancel, which gives +0.8%.
- Cost varies more between runs of the same arm than between arms. The number of subagent requests per run ranges from 11 to 26 on direct-ts and from 11 to 30 on gateway. That variance is why the CI is wide.

## What this means for selling

- Issue dedupe is not an area where we show a saving today. The earlier areas that did show one (CI failure fix, PR review on Haiku) had a large fixed prefix or a large tool result; dedupe has neither.
- Quality is not hurt, and the top-3 hit rate was higher on the gateway (19/24 vs 17/24, not significant).
- The fee ($0.0009 per request) is costly here because the fan-out gives about 26 requests per run. If the fee is per request, net is negative in this area.

## Limits

- 12 tasks, 2 rounds. Not enough to rule out a saving of 10% or less.
- Model differs from the real template (Sonnet 5.5, not 4.6). The real template runs on an egress-firewall runner and posts a comment; this lab does neither.
- Cost is the client-reported `total_cost_usd` for both arms; the Haiku subagent share is included.
