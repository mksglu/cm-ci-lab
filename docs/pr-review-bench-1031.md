> **INVALID: do not use the numbers below.** The lab tenant `t_ci_lab_1` used up its 1,000 free requests and was paused at 2026-10-31 10:29:57 UTC. A paused tenant gets plain pass-through: the gateway forwards the request unchanged, with no savings. 32 of the 37 gateway-arm runs behind this doc started after that time and 1 were running across it, so this doc compares direct with a paused pass-through, not with the gateway. The tenant is back in full mode and a clean re-run is in progress. Note added 2026-10-31.

# PR review benchmark (2026-10-31)

Area: pr-review, the `claude-code-review.yml` template (5,352 workflow files; 69 popular repos in the census). Headless `claude -p` (native installer), arms `direct-ts` (direct API + ENABLE_TOOL_SEARCH, the fair baseline) and `gateway`. Workflows `.github/workflows/pr-review.yml` and `pr-review-judge.yml`. Nothing here is published.

## Result vs the pass bar (fixed in advance): NOT MET

| bar | Sonnet 5.5 (24 pairs, 12 PRs) | Opus 5.5 (12 pairs, 12 PRs) |
|---|---|---|
| task-resampled CI upper bound < 0 | NO: +11.2% (CI -4.7% to +31.1%) | NO: -3.9% (CI -12.1% to +5.9%) |
| quality not lower than direct-ts | not shown lower, but the point estimate is lower: judge score 6.29 vs 6.42 | point estimate lower: 6.75 vs 7.00 |
| 0 errors | yes, 0 | yes, 0 |
| net saving per run > 0 | NO: $-0.0038 | yes: $+0.0058 (inside the CI, not proven) |

Gateway was cheaper in 11 of 24 Sonnet pairs and 7 of 12 Opus pairs. On this area the data show no saving that we can sell. The Opus point estimate is -3.9%, the Sonnet point estimate is +11.2% (more expensive).

## Method

- Template: the most common census prompt (colinhacks/zod and 8 more files share the text): "Please review this pull request and provide feedback on: code quality and best practices, potential bugs or issues, performance considerations, security concerns, test coverage ... Use the repository's CLAUDE.md ... Be constructive and helpful". Allowed tools mirror the template (`Bash(gh pr diff:*)`, `gh pr view`, `gh pr list`, `gh issue view`, `gh issue list`, `gh search`) plus Read, Glob, Grep. `gh pr comment` is removed; the review is printed as the final answer. The lab never writes to the reviewed repo.
- Tasks: 12 merged PRs, 2 each from react, vscode, next.js, langchain, uv, deno (58 to 330 changed lines, 2 to 8 files). The PR head is checked out; the model reads the PR with `gh pr diff` and `gh pr view`.
- Runs: claude-sonnet-5-5, 2 rounds x 2 arms (48 runs); claude-opus-5-5, 1 round x 2 arms (24). `--output-format stream-json --verbose`, `--max-turns 30`. Per-message usage is saved in `lab/pr-review/results/runs.json` with every review text.
- Stats: pairs by (task, round); mean paired log-ratio gateway/direct-ts, shown as exp(mean)-1; 95% CI from a bootstrap that resamples tasks (rounds stay together), 10,000 resamples, seed 1. Script: `lab/pr-review/stats.py`. Net per run = (mean direct-ts - mean gateway) - $0.0009 x gateway API requests.
- Errors: none (is_error false, cost > 0, no "Credit balance is too low" in any run).
- Quality: 36 blind judge jobs (one per pair, direct API). The judge reads the real diff plus REVIEW A and REVIEW B, checks each finding against the diff, scores 1-10, counts false claims, picks A, B or tie. A/B order is randomized (seed 7); the key is `lab/pr-review/results/judgekey.json` and is not in the judge files (`lab/pr-review/judge/`). The judge read the diff from a file; it did not call `gh pr diff` itself. The judge model is Sonnet 5.5, the same model as the Sonnet runs, so this is a model judge, not a human check.

## Cost numbers

Bootstrap 95% CI, 10,000 resamples, seed 1. Columns: mean cost, mean turns, mean API requests, tokens (uncached input, cache write, cache read, output).

| model | arm | mean cost | turns | API req | uncached | cache_write | cache_read | output |
|---|---|---|---|---|---|---|---|---|
| Sonnet | direct-ts | $0.0435 | 2.79 | 2.79 | 6 | 8,234 | 68,222 | 1,611 |
| Sonnet | gateway | $0.0452 | 2.42 | 2.42 | 100 | 10,063 | 51,228 | 1,467 |
| Opus | direct-ts | $0.2311 | 7.25 | 6.25 | 12 | 22,321 | 179,929 | 4,170 |
| Opus | gateway | $0.2203 | 6.33 | 5.50 | 11 | 22,147 | 150,930 | 3,967 |

Net per run at the $0.0009 fee: Sonnet $-0.0038; Opus $+0.0058 ($+0.0050 if the fee is charged per turn).

Sonnet by round: round 1 -5.8%, round 2 +31.3%. The sign flips between rounds on the same 12 PRs, so the Sonnet result is noise-dominated.

## Quality (blind judge, arm labels hidden)

| model | arm | mean score | false claims per review | findings per review |
|---|---|---|---|---|
| Sonnet | direct-ts | 6.42 | 0.42 | 6.54 |
| Sonnet | gateway | 6.29 | 0.58 | 6.54 |
| Opus | direct-ts | 7.00 | 0.25 | 6.58 |
| Opus | gateway | 6.75 | 0.33 | 6.50 |

Winners over 36 pairs: tie 25, direct-ts 7, gateway 4. Mean score difference gateway minus direct-ts: -0.17 (task-resampled CI -0.58 to +0.22). Quality is equal within the noise; the gateway point estimate is slightly lower. Review length is the same (Sonnet 3,486 vs 3,627 chars; Opus 5,001 vs 5,104).

## Anatomy: where the gateway saves and where it does not

Why the area is hard: 20 of 24 direct-ts and 22 of 24 gateway Sonnet runs make 3 requests or fewer (read the diff, then write the review). With 2 requests there is no long tool-result chain to shrink. Cost depends mostly on the fixed prefix and on whether it is already in the Anthropic cache.

Request 0 prefix (tools + system + prompt), mean over runs:

| model | arm | prefix tokens | cache write at request 0 | runs with request-0 write > 1,000 |
|---|---|---|---|---|
| Sonnet | direct-ts | 23,639 | 4,921 | 11 of 24 |
| Sonnet | gateway | 22,226 | 6,300 | 17 of 24 |
| Opus | direct-ts | 23,686 | 9,207 | 12 of 12 |
| Opus | gateway | 23,552 | 10,287 | 12 of 12 |

Observation: the gateway prefix is about 1.4k tokens smaller on average (Sonnet min 11,174 vs 18,971), so cache reads fall (Sonnet 51k vs 68k per run). But the gateway arm wrote to cache at request 0 more often. Direct-ts hit a warm cache in round 2 (12 of 12 first requests read from cache, mean write 0); the gateway arm still wrote 3.0k on average. Cache writes cost 12.5x a cache read per token, so a re-write erases the saving from a smaller prefix. We did not test why the gateway prefix is cold more often (a changed prefix, a different cache key, or timing); this is a hypothesis to test, not a finding.

Task 1: astral-sh/uv#23017, Sonnet, round 1 (direct-ts run 41193094947, gateway run 41193097861). Gateway more expensive ($0.0372 vs $0.0156).

| arm | request | uncached | cache write | cache read | output | tool |
|---|---|---|---|---|---|---|
| direct-ts | 0 | 2 | 0 | 20,039 | 16 | Bash |
| direct-ts | 1 | 2 | 0 | 22,227 | 662 | none (review) |
| gateway | 0 | 2 | 5,492 | 14,413 | 16 | Bash |
| gateway | 1 | 2 | 2,188 | 19,905 | n/a | none (review) |

Direct-ts read the whole prefix from a warm cache. The gateway wrote 5.5k at request 0 (prefix part not warm) and 2.2k at request 1 (the new diff). The new-content write at request 1 is about the same size on both arms in other runs (about 2.2k to 2.9k); the extra cost here is the request-0 re-write. The per-message output field of the gateway arm reads 9 here for what is probably a 600+ token review (we did not check why, possibly a streaming placeholder), so use the run totals for output.

Task 2: microsoft/vscode#345283, Sonnet, round 2 (direct-ts run 41193219625, gateway run 41193222592). Gateway slightly cheaper ($0.1009 vs $0.1074), 8 requests vs 12.

| arm | requests | request-0 write | writes in requests 1+ | total cache read | tools |
|---|---|---|---|---|---|
| direct-ts | 12 | 0 | 13.8k (largest 8.4k, one large tool result at request 3) | 320k | Bash x5, Grep, Read |
| gateway | 8 | 4.4k | 16.4k (largest 10.8k, one large tool result at request 4) | 197k | Bash x4 |

Here the saving comes from fewer turns (8 vs 12), so fewer re-reads of the 19k to 34k context. It is not a smaller write: the big new tool results (the 43 KB diff) are the same bytes in both arms, and the gateway wrote slightly more. Turn count differs from run to run at random on both arms (direct-ts 5 vs 12 turns between rounds on this PR), so one pair does not show a gateway effect.

Where the gateway saves: a smaller fixed prefix (cache reads, long runs), and sometimes fewer turns on long reviews (Opus 6.33 vs 7.25 turns). Where it does not: new tool results (identical bytes), output tokens (equal), and short 2-request reviews, where one cold request-0 write outweighs the smaller prefix.

## Caveats

- The per-message usage sums do not reproduce `total_cost_usd` exactly at Sonnet list prices (sum is 1.35x the reported cost for Sonnet; 0.99x for Opus). We use the reported cost for all tables and did not find the cause; token columns are the result-line totals.
- Opus has 1 round (12 pairs, 12 tasks); the CI is wide (-12.1% to +5.9%).
- Concurrent runs share the Anthropic cache within its TTL, so cache state at request 0 depends on dispatch order (batches of 8, direct-ts first in each pair). This may favor direct-ts in round 2. A fix would be to randomize arm order per pair; not done.
- The judge is Sonnet 5.5, the model that wrote the Sonnet reviews. It saw no arm labels, but a human check of the 11 non-tie pairs would be stronger.

## What to do with this

The pr-review area does not pass the bar with this template. Opus is the only candidate (-3.9%, 7 of 12 cheaper, net +$0.0058 per run) and needs more rounds with randomized arm order before any claim. Do not sell a PR-review saving from this data.

## Run ids

Spend: 72 matrix runs $7.54; smoke pair $0.09; 36 judge jobs $1.51. Under the $15 cap. Tags `a1031-pr-review-sonnet-r1`, `-sonnet-r2`, `-opus-r1`; judge tag `a1031-pr-review-judge` (run 41194263661). Smoke runs 41192784126 and 41192786584 are not in the stats.

| model | round | PR | direct-ts cost / turns | gateway cost / turns | direct-ts run | gateway run |
|---|---|---|---|---|---|---|
| sonnet | astral-sh/uv#23009 | r1 | $0.0430 / 2 | $0.0416 / 2 | [41193103202](https://github.com/mksglu/cm-ci-lab/actions/runs/41193103202) | [41193105930](https://github.com/mksglu/cm-ci-lab/actions/runs/41193105930) |
| sonnet | astral-sh/uv#23009 | r2 | $0.0152 / 2 | $0.0187 / 2 | [41193457224](https://github.com/mksglu/cm-ci-lab/actions/runs/41193457224) | [41193459921](https://github.com/mksglu/cm-ci-lab/actions/runs/41193459921) |
| sonnet | astral-sh/uv#23017 | r1 | $0.0156 / 2 | $0.0372 / 2 | [41193094947](https://github.com/mksglu/cm-ci-lab/actions/runs/41193094947) | [41193097861](https://github.com/mksglu/cm-ci-lab/actions/runs/41193097861) |
| sonnet | astral-sh/uv#23017 | r2 | $0.0153 / 2 | $0.0280 / 2 | [41193450129](https://github.com/mksglu/cm-ci-lab/actions/runs/41193450129) | [41193452666](https://github.com/mksglu/cm-ci-lab/actions/runs/41193452666) |
| sonnet | denoland/deno#36944 | r1 | $0.0570 / 2 | $0.0581 / 2 | [41193119123](https://github.com/mksglu/cm-ci-lab/actions/runs/41193119123) | [41193122511](https://github.com/mksglu/cm-ci-lab/actions/runs/41193122511) |
| sonnet | denoland/deno#36944 | r2 | $0.0225 / 2 | $0.0255 / 2 | [41193473330](https://github.com/mksglu/cm-ci-lab/actions/runs/41193473330) | [41193476448](https://github.com/mksglu/cm-ci-lab/actions/runs/41193476448) |
| sonnet | denoland/deno#37046 | r1 | $0.0548 / 2 | $0.0530 / 2 | [41193110591](https://github.com/mksglu/cm-ci-lab/actions/runs/41193110591) | [41193113473](https://github.com/mksglu/cm-ci-lab/actions/runs/41193113473) |
| sonnet | denoland/deno#37046 | r2 | $0.0214 / 2 | $0.0186 / 2 | [41193465380](https://github.com/mksglu/cm-ci-lab/actions/runs/41193465380) | [41193467929](https://github.com/mksglu/cm-ci-lab/actions/runs/41193467929) |
| sonnet | facebook/react#38025 | r1 | $0.0303 / 2 | $0.0237 / 2 | [41192878978](https://github.com/mksglu/cm-ci-lab/actions/runs/41192878978) | [41192881546](https://github.com/mksglu/cm-ci-lab/actions/runs/41192881546) |
| sonnet | facebook/react#38025 | r2 | $0.0142 / 2 | $0.0293 / 2 | [41193204796](https://github.com/mksglu/cm-ci-lab/actions/runs/41193204796) | [41193207672](https://github.com/mksglu/cm-ci-lab/actions/runs/41193207672) |
| sonnet | facebook/react#38034 | r1 | $0.0707 / 2 | $0.0382 / 2 | [41192871801](https://github.com/mksglu/cm-ci-lab/actions/runs/41192871801) | [41192874251](https://github.com/mksglu/cm-ci-lab/actions/runs/41192874251) |
| sonnet | facebook/react#38034 | r2 | $0.0168 / 2 | $0.0680 / 2 | [41193197181](https://github.com/mksglu/cm-ci-lab/actions/runs/41193197181) | [41193199711](https://github.com/mksglu/cm-ci-lab/actions/runs/41193199711) |
| sonnet | langchain-ai/langchain#41512 | r1 | $0.0613 / 2 | $0.0573 / 2 | [41193019500](https://github.com/mksglu/cm-ci-lab/actions/runs/41193019500) | [41193022553](https://github.com/mksglu/cm-ci-lab/actions/runs/41193022553) |
| sonnet | langchain-ai/langchain#41512 | r2 | $0.0217 / 2 | $0.0234 / 2 | [41193376096](https://github.com/mksglu/cm-ci-lab/actions/runs/41193376096) | [41193379220](https://github.com/mksglu/cm-ci-lab/actions/runs/41193379220) |
| sonnet | langchain-ai/langchain#41520 | r1 | $0.0575 / 2 | $0.0585 / 2 | [41193011762](https://github.com/mksglu/cm-ci-lab/actions/runs/41193011762) | [41193014204](https://github.com/mksglu/cm-ci-lab/actions/runs/41193014204) |
| sonnet | langchain-ai/langchain#41520 | r2 | $0.0172 / 2 | $0.0175 / 2 | [41193368312](https://github.com/mksglu/cm-ci-lab/actions/runs/41193368312) | [41193370920](https://github.com/mksglu/cm-ci-lab/actions/runs/41193370920) |
| sonnet | microsoft/vscode#345283 | r1 | $0.0810 / 5 | $0.0390 / 3 | [41192892267](https://github.com/mksglu/cm-ci-lab/actions/runs/41192892267) | [41192894477](https://github.com/mksglu/cm-ci-lab/actions/runs/41192894477) |
| sonnet | microsoft/vscode#345283 | r2 | $0.1074 / 12 | $0.1009 / 8 | [41193219625](https://github.com/mksglu/cm-ci-lab/actions/runs/41193219625) | [41193222592](https://github.com/mksglu/cm-ci-lab/actions/runs/41193222592) |
| sonnet | microsoft/vscode#345293 | r1 | $0.0461 / 2 | $0.0387 / 2 | [41192885751](https://github.com/mksglu/cm-ci-lab/actions/runs/41192885751) | [41192887801](https://github.com/mksglu/cm-ci-lab/actions/runs/41192887801) |
| sonnet | microsoft/vscode#345293 | r2 | $0.0166 / 2 | $0.0450 / 2 | [41193212362](https://github.com/mksglu/cm-ci-lab/actions/runs/41193212362) | [41193214807](https://github.com/mksglu/cm-ci-lab/actions/runs/41193214807) |
| sonnet | vercel/next.js#100935 | r1 | $0.0810 / 2 | $0.1012 / 5 | [41193004027](https://github.com/mksglu/cm-ci-lab/actions/runs/41193004027) | [41193006714](https://github.com/mksglu/cm-ci-lab/actions/runs/41193006714) |
| sonnet | vercel/next.js#100935 | r2 | $0.0456 / 5 | $0.0321 / 2 | [41193358779](https://github.com/mksglu/cm-ci-lab/actions/runs/41193358779) | [41193363301](https://github.com/mksglu/cm-ci-lab/actions/runs/41193363301) |
| sonnet | vercel/next.js#100956 | r1 | $0.1032 / 5 | $0.1089 / 2 | [41192995317](https://github.com/mksglu/cm-ci-lab/actions/runs/41192995317) | [41192998503](https://github.com/mksglu/cm-ci-lab/actions/runs/41192998503) |
| sonnet | vercel/next.js#100956 | r2 | $0.0292 / 2 | $0.0215 / 2 | [41193349794](https://github.com/mksglu/cm-ci-lab/actions/runs/41193349794) | [41193353189](https://github.com/mksglu/cm-ci-lab/actions/runs/41193353189) |
| opus | astral-sh/uv#23009 | r1 | $0.2280 / 7 | $0.2047 / 5 | [41193915486](https://github.com/mksglu/cm-ci-lab/actions/runs/41193915486) | [41193917843](https://github.com/mksglu/cm-ci-lab/actions/runs/41193917843) |
| opus | astral-sh/uv#23017 | r1 | $0.1971 / 9 | $0.1415 / 5 | [41193908370](https://github.com/mksglu/cm-ci-lab/actions/runs/41193908370) | [41193910647](https://github.com/mksglu/cm-ci-lab/actions/runs/41193910647) |
| opus | denoland/deno#36944 | r1 | $0.2741 / 7 | $0.2293 / 5 | [41193929556](https://github.com/mksglu/cm-ci-lab/actions/runs/41193929556) | [41193931822](https://github.com/mksglu/cm-ci-lab/actions/runs/41193931822) |
| opus | denoland/deno#37046 | r1 | $0.2034 / 6 | $0.2249 / 7 | [41193922320](https://github.com/mksglu/cm-ci-lab/actions/runs/41193922320) | [41193924785](https://github.com/mksglu/cm-ci-lab/actions/runs/41193924785) |
| opus | facebook/react#38025 | r1 | $0.1506 / 7 | $0.1550 / 7 | [41193562138](https://github.com/mksglu/cm-ci-lab/actions/runs/41193562138) | [41193564474](https://github.com/mksglu/cm-ci-lab/actions/runs/41193564474) |
| opus | facebook/react#38034 | r1 | $0.1301 / 4 | $0.1836 / 3 | [41193554831](https://github.com/mksglu/cm-ci-lab/actions/runs/41193554831) | [41193557175](https://github.com/mksglu/cm-ci-lab/actions/runs/41193557175) |
| opus | langchain-ai/langchain#41512 | r1 | $0.1858 / 4 | $0.1650 / 3 | [41193765516](https://github.com/mksglu/cm-ci-lab/actions/runs/41193765516) | [41193767746](https://github.com/mksglu/cm-ci-lab/actions/runs/41193767746) |
| opus | langchain-ai/langchain#41520 | r1 | $0.1951 / 6 | $0.1821 / 5 | [41193758865](https://github.com/mksglu/cm-ci-lab/actions/runs/41193758865) | [41193761157](https://github.com/mksglu/cm-ci-lab/actions/runs/41193761157) |
| opus | microsoft/vscode#345283 | r1 | $0.3188 / 6 | $0.3486 / 8 | [41193575420](https://github.com/mksglu/cm-ci-lab/actions/runs/41193575420) | [41193577858](https://github.com/mksglu/cm-ci-lab/actions/runs/41193577858) |
| opus | microsoft/vscode#345293 | r1 | $0.1804 / 6 | $0.1840 / 7 | [41193568924](https://github.com/mksglu/cm-ci-lab/actions/runs/41193568924) | [41193571145](https://github.com/mksglu/cm-ci-lab/actions/runs/41193571145) |
| opus | vercel/next.js#100935 | r1 | $0.3285 / 10 | $0.2779 / 8 | [41193751541](https://github.com/mksglu/cm-ci-lab/actions/runs/41193751541) | [41193754028](https://github.com/mksglu/cm-ci-lab/actions/runs/41193754028) |
| opus | vercel/next.js#100956 | r1 | $0.3808 / 15 | $0.3472 / 13 | [41193743494](https://github.com/mksglu/cm-ci-lab/actions/runs/41193743494) | [41193746226](https://github.com/mksglu/cm-ci-lab/actions/runs/41193746226) |
