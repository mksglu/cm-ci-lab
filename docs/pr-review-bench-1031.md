# PR review benchmark (2026-10-31, clean re-run)

Area: pr-review, the `claude-code-review.yml` template (5,352 workflow files; 69 popular repos in the census). Headless `claude -p` (native installer), arms `direct-ts` (direct API + ENABLE_TOOL_SEARCH, the fair baseline) and `gateway`. Workflows `.github/workflows/pr-review.yml` and `pr-review-judge.yml`. Nothing here is published.

History: the first run of this bench (tags `a1031-*`) was invalid. The lab tenant `t_ci_lab_1` had used its 1,000 free requests and the gateway had paused it, so the gateway arm was a plain pass-through with no saving. This doc is the clean re-run with the tenant in full mode (tags `c1031-*`).

## Result vs the pass bar (fixed in advance)

| bar | Sonnet 5.5 (24 pairs, 12 PRs) | Opus 5.5 (12 pairs, 12 PRs) |
|---|---|---|
| task-resampled CI upper bound < 0 | YES: -19.0% (CI -26.4% to -11.5%) | NO: -8.5% (CI -17.8% to +2.1%) |
| quality not lower than direct-ts | not shown lower: judge score 6.33 vs 6.46, diff -0.13 (CI -0.54 to +0.29); 21 of 24 ties | not shown lower: 7.00 vs 7.17, diff -0.17 (CI -0.50 to +0.17); 11 of 12 ties |
| 0 errors | yes, 0 | yes, 0 |
| every round valid | yes | yes |
| net saving per run at $0.0009 per request | +$0.0092 | +$0.0102 (inside the CI, not proven) |

Sonnet MEETS the bar. Gateway was cheaper in 21 of 24 Sonnet pairs. Opus does not meet the bar: 8 of 12 pairs cheaper, upper bound +2.1%.

## Round validity (quota guard)

`used_paused` was 1,518 before round 1 and 1,518 after every round, so no run went through a paused tenant. Mean request-1 size (input + cache write + cache read of the first assistant message):

| model | direct-ts | gateway | difference |
|---|---|---|---|
| Sonnet (24 pairs) | 23,639 | 15,852 | -33% |
| Opus (12 pairs) | 23,686 | 15,899 | -33% |

The gateway cut request 1 by a third in every round, which is the full-mode signature (the invalid run showed 16,787 vs 16,788).

## Method

- Template: the most common census prompt (colinhacks/zod and 8 more files share the text): "Please review this pull request and provide feedback on: code quality and best practices, potential bugs or issues, performance considerations, security concerns, test coverage ... Use the repository's CLAUDE.md ... Be constructive and helpful". Allowed tools mirror the template (`Bash(gh pr diff:*)`, `gh pr view`, `gh pr list`, `gh issue view`, `gh issue list`, `gh search`) plus Read, Glob, Grep. `gh pr comment` is removed; the review is printed as the final answer. The lab never writes to the reviewed repo.
- Tasks: 12 merged PRs, 2 each from react, vscode, next.js, langchain, uv, deno.
- Runs: claude-sonnet-5-5, 2 rounds x 2 arms (48 runs); claude-opus-5-5, 1 round x 2 arms (24). `--output-format stream-json --verbose`, `--max-turns 30`. Per-message usage and every review text are in `lab/pr-review/results/runs.json`.
- Dispatch: batches of 4 PRs (8 runs). The arm order inside each pair is randomized (the first run had direct-ts first in every pair).
- Stats: pairs by (task, round); mean paired log-ratio gateway/direct-ts, shown as exp(mean)-1; 95% CI from a bootstrap that resamples tasks (rounds stay together), 10,000 resamples, seed 1. Script `lab/pr-review/stats.py`. Net per run = (mean direct-ts - mean gateway) - $0.0009 x mean gateway API requests.
- Errors: none (is_error false, cost > 0, no "Credit balance is too low").
- Quality: 36 blind judge jobs, one per pair, direct API. The judge reads the real diff plus REVIEW A and REVIEW B, checks each finding against the diff, scores 1-10, counts false claims, picks A, B or tie. A/B order is randomized (seed 7). The key is `lab/pr-review/results/judgekey.json` and is not in the judge files. The judge model is Sonnet 5.5: a model judge, not a human check.

## Cost numbers

| model | arm | mean cost | turns | API req | uncached | cache_write | cache_read | output |
|---|---|---|---|---|---|---|---|---|
| Sonnet | direct-ts | $0.0601 | 2.50 | 2.46 | 5 | 15,642 | 49,736 | 1,603 |
| Sonnet | gateway | $0.0489 | 2.25 | 2.25 | 585 | 12,293 | 27,591 | 1,421 |
| Opus | direct-ts | $0.2257 | 6.58 | 5.67 | 11 | 22,598 | 160,283 | 4,029 |
| Opus | gateway | $0.2094 | 7.25 | 6.67 | 592 | 19,813 | 140,698 | 3,993 |

Where the saving comes from: a smaller fixed prefix. Request 1 is a third smaller, so the first cache write is smaller (6.8k vs 10.3k tokens) and every later cache read is smaller. New tool results (the diff) are the same bytes on both arms. On Opus the gateway arm made one more request on average (6.67 vs 5.67), which eats part of the saving.

## Quality

| model | arm | judge score | false claims per review | findings per review |
|---|---|---|---|---|
| Sonnet | direct-ts | 6.46 | 0.62 | 6.08 |
| Sonnet | gateway | 6.33 | 0.75 | 5.88 |
| Opus | direct-ts | 7.17 | 0.17 | 6.17 |
| Opus | gateway | 7.00 | 0.25 | 6.50 |

Winners: Sonnet 21 ties, direct-ts 2, gateway 1. Opus 11 ties, gateway 1. The point estimates are slightly lower on the gateway, inside noise (CIs include 0).

## Caveats

- The per-message usage sums do not reproduce `total_cost_usd` exactly (seen in the first run too). We use the reported cost; the cause is not found.
- Opus has 1 round (12 pairs); its CI includes 0.
- Concurrent runs share the Anthropic cache within its TTL. Arm order is now randomized per pair, which removes the order bias of the first run.
- The judge is Sonnet 5.5, the model that wrote the Sonnet reviews. A human check of the 3 non-tie Sonnet pairs would be stronger.
- The Sonnet quality bar says "not lower": the CI of the score difference includes 0 but also -0.54, so a small quality loss is not ruled out.

## What to do with this

Sonnet PR review passes the bar: about -19% cost, net +$0.0092 per run after the per-request fee, quality equal within noise. Opus needs more rounds before any claim.

## Run ids

Spend: 72 matrix runs $7.84; 36 judge jobs $1.50; total $9.34, under the $15 cap. Tags `c1031-pr-review-sonnet-r1`, `c1031-pr-review-sonnet-r2`, `c1031-pr-review-opus-r1`; judge tag `c1031-pr-review-judge` (run [41203782130](https://github.com/mksglu/cm-ci-lab/actions/runs/41203782130)).

| model | PR | round | direct-ts cost / turns | gateway cost / turns | direct-ts run | gateway run |
|---|---|---|---|---|---|---|
| opus | astral-sh/uv#23009 | r1 | $0.2112 / 6 | $0.1842 / 5 | [41203451252](https://github.com/mksglu/cm-ci-lab/actions/runs/41203451252) | [41203446489](https://github.com/mksglu/cm-ci-lab/actions/runs/41203446489) |
| opus | astral-sh/uv#23017 | r1 | $0.1547 / 5 | $0.1643 / 6 | [41203441094](https://github.com/mksglu/cm-ci-lab/actions/runs/41203441094) | [41203436017](https://github.com/mksglu/cm-ci-lab/actions/runs/41203436017) |
| opus | denoland/deno#36944 | r1 | $0.2546 / 6 | $0.2029 / 4 | [41203465367](https://github.com/mksglu/cm-ci-lab/actions/runs/41203465367) | [41203470180](https://github.com/mksglu/cm-ci-lab/actions/runs/41203470180) |
| opus | denoland/deno#37046 | r1 | $0.1988 / 5 | $0.2358 / 6 | [41203460522](https://github.com/mksglu/cm-ci-lab/actions/runs/41203460522) | [41203455886](https://github.com/mksglu/cm-ci-lab/actions/runs/41203455886) |
| opus | facebook/react#38025 | r1 | $0.1562 / 7 | $0.1278 / 7 | [41202972102](https://github.com/mksglu/cm-ci-lab/actions/runs/41202972102) | [41202967327](https://github.com/mksglu/cm-ci-lab/actions/runs/41202967327) |
| opus | facebook/react#38034 | r1 | $0.2052 / 5 | $0.1331 / 4 | [41202957656](https://github.com/mksglu/cm-ci-lab/actions/runs/41202957656) | [41202962300](https://github.com/mksglu/cm-ci-lab/actions/runs/41202962300) |
| opus | langchain-ai/langchain#41512 | r1 | $0.1408 / 2 | $0.1609 / 4 | [41203289924](https://github.com/mksglu/cm-ci-lab/actions/runs/41203289924) | [41203294896](https://github.com/mksglu/cm-ci-lab/actions/runs/41203294896) |
| opus | langchain-ai/langchain#41520 | r1 | $0.1412 / 3 | $0.1355 / 3 | [41203285044](https://github.com/mksglu/cm-ci-lab/actions/runs/41203285044) | [41203280108](https://github.com/mksglu/cm-ci-lab/actions/runs/41203280108) |
| opus | microsoft/vscode#345283 | r1 | $0.3329 / 6 | $0.4152 / 18 | [41202988283](https://github.com/mksglu/cm-ci-lab/actions/runs/41202988283) | [41202993883](https://github.com/mksglu/cm-ci-lab/actions/runs/41202993883) |
| opus | microsoft/vscode#345293 | r1 | $0.2179 / 9 | $0.1640 / 7 | [41202977286](https://github.com/mksglu/cm-ci-lab/actions/runs/41202977286) | [41202982605](https://github.com/mksglu/cm-ci-lab/actions/runs/41202982605) |
| opus | vercel/next.js#100935 | r1 | $0.3001 / 9 | $0.2512 / 10 | [41203269327](https://github.com/mksglu/cm-ci-lab/actions/runs/41203269327) | [41203274857](https://github.com/mksglu/cm-ci-lab/actions/runs/41203274857) |
| opus | vercel/next.js#100956 | r1 | $0.3945 / 16 | $0.3382 / 13 | [41203264329](https://github.com/mksglu/cm-ci-lab/actions/runs/41203264329) | [41203259357](https://github.com/mksglu/cm-ci-lab/actions/runs/41203259357) |
| sonnet | astral-sh/uv#23009 | r1 | $0.0467 / 2 | $0.0345 / 2 | [41201600858](https://github.com/mksglu/cm-ci-lab/actions/runs/41201600858) | [41201595048](https://github.com/mksglu/cm-ci-lab/actions/runs/41201595048) |
| sonnet | astral-sh/uv#23009 | r2 | $0.0427 / 2 | $0.0358 / 2 | [41202790258](https://github.com/mksglu/cm-ci-lab/actions/runs/41202790258) | [41202795318](https://github.com/mksglu/cm-ci-lab/actions/runs/41202795318) |
| sonnet | astral-sh/uv#23017 | r1 | $0.0334 / 2 | $0.0278 / 2 | [41201584500](https://github.com/mksglu/cm-ci-lab/actions/runs/41201584500) | [41201589957](https://github.com/mksglu/cm-ci-lab/actions/runs/41201589957) |
| sonnet | astral-sh/uv#23017 | r2 | $0.0340 / 2 | $0.0268 / 2 | [41202785260](https://github.com/mksglu/cm-ci-lab/actions/runs/41202785260) | [41202780433](https://github.com/mksglu/cm-ci-lab/actions/runs/41202780433) |
| sonnet | denoland/deno#36944 | r1 | $0.0639 / 2 | $0.0516 / 2 | [41201622939](https://github.com/mksglu/cm-ci-lab/actions/runs/41201622939) | [41201617617](https://github.com/mksglu/cm-ci-lab/actions/runs/41201617617) |
| sonnet | denoland/deno#36944 | r2 | $0.0584 / 2 | $0.0469 / 2 | [41202810363](https://github.com/mksglu/cm-ci-lab/actions/runs/41202810363) | [41202815525](https://github.com/mksglu/cm-ci-lab/actions/runs/41202815525) |
| sonnet | denoland/deno#37046 | r1 | $0.0559 / 2 | $0.0618 / 2 | [41201606674](https://github.com/mksglu/cm-ci-lab/actions/runs/41201606674) | [41201612168](https://github.com/mksglu/cm-ci-lab/actions/runs/41201612168) |
| sonnet | denoland/deno#37046 | r2 | $0.0560 / 2 | $0.0603 / 2 | [41202805295](https://github.com/mksglu/cm-ci-lab/actions/runs/41202805295) | [41202800136](https://github.com/mksglu/cm-ci-lab/actions/runs/41202800136) |
| sonnet | facebook/react#38025 | r1 | $0.0303 / 2 | $0.0226 / 2 | [41200842001](https://github.com/mksglu/cm-ci-lab/actions/runs/41200842001) | [41200847209](https://github.com/mksglu/cm-ci-lab/actions/runs/41200847209) |
| sonnet | facebook/react#38025 | r2 | $0.0314 / 2 | $0.0233 / 2 | [41201870924](https://github.com/mksglu/cm-ci-lab/actions/runs/41201870924) | [41201876296](https://github.com/mksglu/cm-ci-lab/actions/runs/41201876296) |
| sonnet | facebook/react#38034 | r1 | $0.0686 / 2 | $0.0406 / 2 | [41200836881](https://github.com/mksglu/cm-ci-lab/actions/runs/41200836881) | [41200831651](https://github.com/mksglu/cm-ci-lab/actions/runs/41200831651) |
| sonnet | facebook/react#38034 | r2 | $0.0717 / 2 | $0.0407 / 2 | [41201861285](https://github.com/mksglu/cm-ci-lab/actions/runs/41201861285) | [41201866417](https://github.com/mksglu/cm-ci-lab/actions/runs/41201866417) |
| sonnet | langchain-ai/langchain#41512 | r1 | $0.0607 / 2 | $0.0519 / 2 | [41201268902](https://github.com/mksglu/cm-ci-lab/actions/runs/41201268902) | [41201264130](https://github.com/mksglu/cm-ci-lab/actions/runs/41201264130) |
| sonnet | langchain-ai/langchain#41512 | r2 | $0.0590 / 2 | $0.0502 / 2 | [41202387154](https://github.com/mksglu/cm-ci-lab/actions/runs/41202387154) | [41202392709](https://github.com/mksglu/cm-ci-lab/actions/runs/41202392709) |
| sonnet | langchain-ai/langchain#41520 | r1 | $0.0569 / 2 | $0.0511 / 2 | [41201251513](https://github.com/mksglu/cm-ci-lab/actions/runs/41201251513) | [41201258009](https://github.com/mksglu/cm-ci-lab/actions/runs/41201258009) |
| sonnet | langchain-ai/langchain#41520 | r2 | $0.0587 / 2 | $0.0519 / 2 | [41202376439](https://github.com/mksglu/cm-ci-lab/actions/runs/41202376439) | [41202381384](https://github.com/mksglu/cm-ci-lab/actions/runs/41202381384) |
| sonnet | microsoft/vscode#345283 | r1 | $0.0999 / 5 | $0.0617 / 4 | [41200867952](https://github.com/mksglu/cm-ci-lab/actions/runs/41200867952) | [41200862840](https://github.com/mksglu/cm-ci-lab/actions/runs/41200862840) |
| sonnet | microsoft/vscode#345283 | r2 | $0.1051 / 10 | $0.0674 / 5 | [41201896374](https://github.com/mksglu/cm-ci-lab/actions/runs/41201896374) | [41201891221](https://github.com/mksglu/cm-ci-lab/actions/runs/41201891221) |
| sonnet | microsoft/vscode#345293 | r1 | $0.0447 / 2 | $0.0386 / 2 | [41200857226](https://github.com/mksglu/cm-ci-lab/actions/runs/41200857226) | [41200852003](https://github.com/mksglu/cm-ci-lab/actions/runs/41200852003) |
| sonnet | microsoft/vscode#345293 | r2 | $0.0460 / 2 | $0.0368 / 2 | [41201886681](https://github.com/mksglu/cm-ci-lab/actions/runs/41201886681) | [41201881462](https://github.com/mksglu/cm-ci-lab/actions/runs/41201881462) |
| sonnet | vercel/next.js#100935 | r1 | $0.0763 / 2 | $0.0609 / 2 | [41201246355](https://github.com/mksglu/cm-ci-lab/actions/runs/41201246355) | [41201240498](https://github.com/mksglu/cm-ci-lab/actions/runs/41201240498) |
| sonnet | vercel/next.js#100935 | r2 | $0.0775 / 2 | $0.0705 / 3 | [41202370847](https://github.com/mksglu/cm-ci-lab/actions/runs/41202370847) | [41202366106](https://github.com/mksglu/cm-ci-lab/actions/runs/41202366106) |
| sonnet | vercel/next.js#100956 | r1 | $0.0758 / 2 | $0.0790 / 2 | [41201229411](https://github.com/mksglu/cm-ci-lab/actions/runs/41201229411) | [41201234743](https://github.com/mksglu/cm-ci-lab/actions/runs/41201234743) |
| sonnet | vercel/next.js#100956 | r2 | $0.0893 / 3 | $0.0802 / 2 | [41202355984](https://github.com/mksglu/cm-ci-lab/actions/runs/41202355984) | [41202361018](https://github.com/mksglu/cm-ci-lab/actions/runs/41202361018) |
