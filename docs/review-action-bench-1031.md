# PR review through the official claude-code-action (2026-10-31)

Area: PR review with `anthropics/claude-code-action@v1` (22,720 public workflow files use this client). Prompt and read-only tools are the community `claude-code-review.yml` template, the same as the pr-review lane (`docs/pr-review-bench-1031.md`). Workflows `.github/workflows/review-action.yml` and `review-action-judge.yml`. Nothing here is published.

History: the six area benches run earlier on 2026-10-31 were invalid, because the lab tenant `t_ci_lab_1` was paused and the gateway forwarded requests unchanged. This lane was run only after the tenant was back in full mode (50,000 requests granted), so there is no invalid run for this lane. Every round below passed the quota guard.

## Result vs the pass bar (fixed in advance): MET

| bar | Sonnet 5.5 (24 pairs, 12 PRs) | Opus 5.5 (12 pairs, 12 PRs) | Sonnet, extra arm `direct` (12 pairs) |
|---|---|---|---|
| task-resampled CI upper bound < 0 | YES: -11.6% (CI -20.8% to -2.2%) | YES: -13.6% (CI -22.4% to -3.9%) | YES: -19.9% (CI -32.0% to -7.5%) |
| quality not lower | YES: judge diff 0.00 (CI -0.42 to +0.38) | YES: +0.08 (CI -0.25 to +0.42) | YES: -0.08 (CI -0.67 to +0.42) |
| 0 errors | yes, 0 of 96 runs | yes | yes |
| every round valid | yes (see below) | yes | yes |
| net per run at $0.0009 per request | +$0.0047 | +$0.0238 | +$0.0094 |

The pass bar uses `direct-ts` as baseline (first two columns). The `direct` column (no ENABLE_TOOL_SEARCH) is an extra line.
Gateway was cheaper in 16 of 24 Sonnet pairs, 7 of 12 Opus pairs, 9 of 12 `direct` pairs.

## Round validity (quota guard)

`used_paused` was 1518 before the first round and 1518 after the last run of every round (8 readings). The tenant stayed in full mode. Request 1 (input + cache write + cache read of the first assistant message) is smaller on the gateway arm in every round:

| round | direct baseline | gateway | change |
|---|---|---|---|
| Sonnet r1 (direct-ts) | 24,049 | 15,917 | -33.8% |
| Sonnet r2 (direct-ts) | 24,049 | 15,917 | -33.8% |
| Opus r1 (direct-ts) | 24,096 | 15,964 | -33.8% |
| Sonnet r1 (direct) | 24,049 | 15,917 | -33.8% |

(Each row is the mean over 12 runs. Request-1 size depends on the PR and prompt, so the means repeat across rounds. The `direct` arm has the same request-1 size as `direct-ts` in this client.)

## Method

- Client: `anthropics/claude-code-action@v1` with `anthropic_api_key` from `ANTHROPIC_API_KEY_C` (the only key whose org accepts this entrypoint). No entrypoint spoofing. The gateway arm sets `ANTHROPIC_BASE_URL` and the CI headers that `ci init` writes (`lab/path-env.sh`).
- Prompt: the community template text (code quality, bugs, performance, security, test coverage; use CLAUDE.md; be constructive). Tools: `Bash(gh issue view/list, gh search, gh pr diff/view/list)`, Read, Glob, Grep. `gh pr comment` is not available; the review is the final answer. The lab never writes to the reviewed repo.
- Tasks: the same 12 merged PRs as the pr-review lane (react 38034 38025, vscode 345293 345283, next.js 100956 100935, langchain 41520 41512, uv 23017 23009, deno 37046 36944).
- Runs: claude-sonnet-5-5 2 rounds x 2 arms (48), claude-opus-5-5 1 round x 2 arms (24), claude-sonnet-5-5 `direct` vs gateway 1 round (24). `--max-turns 30`. Arm order was random per PR; dispatch in batches of 4 PRs.
- Stats (`lab/review-action/stats.py`): pairs by (task, round); mean paired log-ratio gateway/baseline shown as exp(mean)-1; 95% CI from a bootstrap that resamples tasks (rounds stay together), 10,000 resamples, seed 1. Net per run = (mean baseline - mean gateway) - $0.0009 x mean gateway API requests.
- Errors: none (is_error false, cost > 0, no "Credit balance is too low" in any of the 96 runs).
- Quality: 48 blind judge jobs, one per pair (`lab/review-action/judge/`, workflow `review-action-judge.yml`, run 41204329983). The judge reads the real diff plus REVIEW A and REVIEW B, checks each finding against the diff, scores 1-10, counts false claims and picks A, B or tie. A/B order is random (seed 7); the key is `lab/review-action/results/judgekey.json` and is not in the judge files. The judge model is Sonnet 5.5, the same model as the Sonnet runs, so this is a model judge, not a human check.

## Cost numbers

Mean cost, mean API requests, tokens per run (uncached input, cache write, cache read, output).

| comparison | arm | mean cost | API req | uncached | cache_write | cache_read | output |
|---|---|---|---|---|---|---|---|
| Sonnet | direct-ts | $0.0621 | 2.25 | 5 | 16,735 | 45,287 | 1,559 |
| Sonnet | gateway | $0.0553 | 2.38 | 537 | 13,627 | 30,760 | 1,490 |
| Opus | direct-ts | $0.2370 | 5.92 | 12 | 23,879 | 170,470 | 4,165 |
| Opus | gateway | $0.2079 | 5.92 | 542 | 19,821 | 118,937 | 3,919 |
| Sonnet (extra) | direct | $0.0647 | 2.33 | 5 | 17,325 | 45,166 | 1,669 |
| Sonnet (extra) | gateway | $0.0533 | 2.25 | 537 | 13,117 | 26,289 | 1,459 |

Sonnet by round (direct-ts baseline): round 1 -10.2%, round 2 -13.0%. The sign is the same in both rounds. The Sonnet saving here is stable, unlike the pr-review lane with `claude -p` (round 1 -5.8%, round 2 +31.3%).

Where the saving comes from: the gateway request 1 is about 8.1k tokens (34%) smaller, so the first cache write is about 3k tokens smaller (7.8k vs 10.8k) and cache reads fall by 32% (Sonnet) and 30% (Opus). Output tokens are equal within noise. Turn counts are equal: the saving is the smaller prefix, not fewer turns. The gateway arm shows about 540 uncached input tokens per run against about 5 on direct; we did not check why. Cost still falls, as the table shows.

## Quality (blind judge, arm labels hidden)

| comparison | arm | mean score | false claims per review | findings per review |
|---|---|---|---|---|
| Sonnet (24) | direct-ts | 6.29 | 0.67 | 6.54 |
| Sonnet (24) | gateway | 6.29 | 0.54 | 6.62 |
| Opus (12) | direct-ts | 7.00 | 0.50 | 6.92 |
| Opus (12) | gateway | 7.08 | 0.25 | 6.83 |
| Sonnet extra (12) | direct | 6.25 | 1.08 | 6.67 |
| Sonnet extra (12) | gateway | 6.17 | 0.75 | 7.08 |

Winners: Sonnet tie 19, gateway 3, direct-ts 2. Opus tie 11, gateway 1. Extra arm tie 10, gateway 1, direct 1. Quality is equal within the noise.

## Caveats

- One round for Opus and for the `direct` arm: 12 pairs each, so those CIs are wide (Opus -22.4% to -3.9%; direct -32.0% to -7.5%).
- Concurrent runs share the Anthropic cache within its TTL, so cache state at request 1 depends on dispatch order. Arm order was randomized per PR in this lane, which removes the bias seen in the pr-review lane. In all runs the first request wrote to cache on both arms (no warm hit at request 1).
- The judge is Sonnet 5.5, the model that wrote the Sonnet reviews; a human check of the non-tie pairs would be stronger.
- Reviews are short (2 to 6 requests), so the fixed-prefix saving dominates. A long agent run with large new tool results saves less, because those bytes are the same on both arms.
- Results are for these 12 PRs and this prompt only.

## What to do with this

This area passes the pass bar on Sonnet and Opus against the fair baseline, and the saving is larger against the common `direct` setup (373 of 374 popular agent workflows). The numbers can back a CI claim for the official action with the community review prompt: about 12 to 14% cheaper, quality equal. Do not extend the claim to other prompts or to long agent runs without a bench.

## Run ids

Spend from usage: 96 matrix runs $9.57; 48 judge jobs $2.00; total $11.57, under the $15 cap. Tags `c1031-review-action-sonnet-r1`, `-sonnet-r2`, `-opus-r1`, `-sonnet-direct-r1`; judge tag `c1031-review-action-judge` (run 41204329983). Smoke runs 41194356596 and 41194359750 are not in the stats. In the table, "base" is `direct-ts` for sonnet and opus rows and `direct` for sonnet-direct rows. Cells are cost / turns.

| comparison | PR | round | base | gateway | base run | gateway run |
|---|---|---|---|---|---|---|
| opus | astral-sh/uv#23009 | r1 | $0.2187 / 6 | $0.2369 / 9 | [41203352207](https://github.com/mksglu/cm-ci-lab/actions/runs/41203352207) | [41203357376](https://github.com/mksglu/cm-ci-lab/actions/runs/41203357376) |
| opus | astral-sh/uv#23017 | r1 | $0.1497 / 5 | $0.1607 / 6 | [41203347008](https://github.com/mksglu/cm-ci-lab/actions/runs/41203347008) | [41203341889](https://github.com/mksglu/cm-ci-lab/actions/runs/41203341889) |
| opus | denoland/deno#36944 | r1 | $0.2705 / 8 | $0.2735 / 8 | [41203372369](https://github.com/mksglu/cm-ci-lab/actions/runs/41203372369) | [41203377230](https://github.com/mksglu/cm-ci-lab/actions/runs/41203377230) |
| opus | denoland/deno#37046 | r1 | $0.2545 / 8 | $0.1980 / 6 | [41203367185](https://github.com/mksglu/cm-ci-lab/actions/runs/41203367185) | [41203362082](https://github.com/mksglu/cm-ci-lab/actions/runs/41203362082) |
| opus | facebook/react#38025 | r1 | $0.1408 / 6 | $0.1001 / 5 | [41202949068](https://github.com/mksglu/cm-ci-lab/actions/runs/41202949068) | [41202954032](https://github.com/mksglu/cm-ci-lab/actions/runs/41202954032) |
| opus | facebook/react#38034 | r1 | $0.2249 / 5 | $0.1711 / 5 | [41202939672](https://github.com/mksglu/cm-ci-lab/actions/runs/41202939672) | [41202944514](https://github.com/mksglu/cm-ci-lab/actions/runs/41202944514) |
| opus | langchain-ai/langchain#41512 | r1 | $0.1956 / 4 | $0.1344 / 2 | [41203195373](https://github.com/mksglu/cm-ci-lab/actions/runs/41203195373) | [41203190808](https://github.com/mksglu/cm-ci-lab/actions/runs/41203190808) |
| opus | langchain-ai/langchain#41520 | r1 | $0.1793 / 5 | $0.1649 / 5 | [41203180941](https://github.com/mksglu/cm-ci-lab/actions/runs/41203180941) | [41203185787](https://github.com/mksglu/cm-ci-lab/actions/runs/41203185787) |
| opus | microsoft/vscode#345283 | r1 | $0.3222 / 6 | $0.3342 / 10 | [41202973045](https://github.com/mksglu/cm-ci-lab/actions/runs/41202973045) | [41202968138](https://github.com/mksglu/cm-ci-lab/actions/runs/41202968138) |
| opus | microsoft/vscode#345293 | r1 | $0.2045 / 6 | $0.1667 / 4 | [41202963271](https://github.com/mksglu/cm-ci-lab/actions/runs/41202963271) | [41202958450](https://github.com/mksglu/cm-ci-lab/actions/runs/41202958450) |
| opus | vercel/next.js#100935 | r1 | $0.3836 / 13 | $0.2397 / 7 | [41203170869](https://github.com/mksglu/cm-ci-lab/actions/runs/41203170869) | [41203176086](https://github.com/mksglu/cm-ci-lab/actions/runs/41203176086) |
| opus | vercel/next.js#100956 | r1 | $0.2995 / 12 | $0.3141 / 9 | [41203160428](https://github.com/mksglu/cm-ci-lab/actions/runs/41203160428) | [41203165559](https://github.com/mksglu/cm-ci-lab/actions/runs/41203165559) |
| sonnet | astral-sh/uv#23009 | r1 | $0.0435 / 2 | $0.0393 / 2 | [41201450157](https://github.com/mksglu/cm-ci-lab/actions/runs/41201450157) | [41201455713](https://github.com/mksglu/cm-ci-lab/actions/runs/41201455713) |
| sonnet | astral-sh/uv#23009 | r2 | $0.0440 / 2 | $0.0371 / 2 | [41202777909](https://github.com/mksglu/cm-ci-lab/actions/runs/41202777909) | [41202772608](https://github.com/mksglu/cm-ci-lab/actions/runs/41202772608) |
| sonnet | astral-sh/uv#23017 | r1 | $0.0358 / 2 | $0.0301 / 2 | [41201444984](https://github.com/mksglu/cm-ci-lab/actions/runs/41201444984) | [41201439590](https://github.com/mksglu/cm-ci-lab/actions/runs/41201439590) |
| sonnet | astral-sh/uv#23017 | r2 | $0.0368 / 2 | $0.0299 / 2 | [41202767568](https://github.com/mksglu/cm-ci-lab/actions/runs/41202767568) | [41202762389](https://github.com/mksglu/cm-ci-lab/actions/runs/41202762389) |
| sonnet | denoland/deno#36944 | r1 | $0.0606 / 2 | $0.0532 / 2 | [41201478050](https://github.com/mksglu/cm-ci-lab/actions/runs/41201478050) | [41201472388](https://github.com/mksglu/cm-ci-lab/actions/runs/41201472388) |
| sonnet | denoland/deno#36944 | r2 | $0.0607 / 2 | $0.0658 / 2 | [41202793022](https://github.com/mksglu/cm-ci-lab/actions/runs/41202793022) | [41202798272](https://github.com/mksglu/cm-ci-lab/actions/runs/41202798272) |
| sonnet | denoland/deno#37046 | r1 | $0.0574 / 2 | $0.0664 / 2 | [41201461134](https://github.com/mksglu/cm-ci-lab/actions/runs/41201461134) | [41201466477](https://github.com/mksglu/cm-ci-lab/actions/runs/41201466477) |
| sonnet | denoland/deno#37046 | r2 | $0.0562 / 2 | $0.0480 / 2 | [41202783271](https://github.com/mksglu/cm-ci-lab/actions/runs/41202783271) | [41202787996](https://github.com/mksglu/cm-ci-lab/actions/runs/41202787996) |
| sonnet | facebook/react#38025 | r1 | $0.0361 / 3 | $0.0270 / 2 | [41200878855](https://github.com/mksglu/cm-ci-lab/actions/runs/41200878855) | [41200873400](https://github.com/mksglu/cm-ci-lab/actions/runs/41200873400) |
| sonnet | facebook/react#38025 | r2 | $0.0349 / 2 | $0.0252 / 2 | [41201900186](https://github.com/mksglu/cm-ci-lab/actions/runs/41201900186) | [41201905332](https://github.com/mksglu/cm-ci-lab/actions/runs/41201905332) |
| sonnet | facebook/react#38034 | r1 | $0.0714 / 2 | $0.0545 / 2 | [41200861788](https://github.com/mksglu/cm-ci-lab/actions/runs/41200861788) | [41200867623](https://github.com/mksglu/cm-ci-lab/actions/runs/41200867623) |
| sonnet | facebook/react#38034 | r2 | $0.0698 / 2 | $0.0455 / 2 | [41201895295](https://github.com/mksglu/cm-ci-lab/actions/runs/41201895295) | [41201889670](https://github.com/mksglu/cm-ci-lab/actions/runs/41201889670) |
| sonnet | langchain-ai/langchain#41512 | r1 | $0.0598 / 2 | $0.0529 / 2 | [41201249752](https://github.com/mksglu/cm-ci-lab/actions/runs/41201249752) | [41201244529](https://github.com/mksglu/cm-ci-lab/actions/runs/41201244529) |
| sonnet | langchain-ai/langchain#41512 | r2 | $0.0647 / 2 | $0.0510 / 2 | [41202301329](https://github.com/mksglu/cm-ci-lab/actions/runs/41202301329) | [41202295958](https://github.com/mksglu/cm-ci-lab/actions/runs/41202295958) |
| sonnet | langchain-ai/langchain#41520 | r1 | $0.0618 / 2 | $0.0539 / 2 | [41201238733](https://github.com/mksglu/cm-ci-lab/actions/runs/41201238733) | [41201232941](https://github.com/mksglu/cm-ci-lab/actions/runs/41201232941) |
| sonnet | langchain-ai/langchain#41520 | r2 | $0.0603 / 2 | $0.0694 / 2 | [41202290812](https://github.com/mksglu/cm-ci-lab/actions/runs/41202290812) | [41202285612](https://github.com/mksglu/cm-ci-lab/actions/runs/41202285612) |
| sonnet | microsoft/vscode#345283 | r1 | $0.1085 / 4 | $0.0676 / 4 | [41200900045](https://github.com/mksglu/cm-ci-lab/actions/runs/41200900045) | [41200894848](https://github.com/mksglu/cm-ci-lab/actions/runs/41200894848) |
| sonnet | microsoft/vscode#345283 | r2 | $0.1196 / 5 | $0.0675 / 5 | [41201922390](https://github.com/mksglu/cm-ci-lab/actions/runs/41201922390) | [41201927533](https://github.com/mksglu/cm-ci-lab/actions/runs/41201927533) |
| sonnet | microsoft/vscode#345293 | r1 | $0.0545 / 2 | $0.0570 / 2 | [41200889806](https://github.com/mksglu/cm-ci-lab/actions/runs/41200889806) | [41200884567](https://github.com/mksglu/cm-ci-lab/actions/runs/41200884567) |
| sonnet | microsoft/vscode#345293 | r2 | $0.0496 / 2 | $0.0558 / 2 | [41201911588](https://github.com/mksglu/cm-ci-lab/actions/runs/41201911588) | [41201917255](https://github.com/mksglu/cm-ci-lab/actions/runs/41201917255) |
| sonnet | vercel/next.js#100935 | r1 | $0.0769 / 2 | $0.0846 / 5 | [41201227396](https://github.com/mksglu/cm-ci-lab/actions/runs/41201227396) | [41201221860](https://github.com/mksglu/cm-ci-lab/actions/runs/41201221860) |
| sonnet | vercel/next.js#100935 | r2 | $0.0787 / 2 | $0.0730 / 3 | [41202275041](https://github.com/mksglu/cm-ci-lab/actions/runs/41202275041) | [41202280345](https://github.com/mksglu/cm-ci-lab/actions/runs/41202280345) |
| sonnet | vercel/next.js#100956 | r1 | $0.0753 / 2 | $0.0858 / 2 | [41201210413](https://github.com/mksglu/cm-ci-lab/actions/runs/41201210413) | [41201216014](https://github.com/mksglu/cm-ci-lab/actions/runs/41201216014) |
| sonnet | vercel/next.js#100956 | r2 | $0.0741 / 2 | $0.0869 / 2 | [41202269584](https://github.com/mksglu/cm-ci-lab/actions/runs/41202269584) | [41202264392](https://github.com/mksglu/cm-ci-lab/actions/runs/41202264392) |
| sonnet-direct | astral-sh/uv#23009 | r1 | $0.0523 / 2 | $0.0373 / 2 | [41204060348](https://github.com/mksglu/cm-ci-lab/actions/runs/41204060348) | [41204065432](https://github.com/mksglu/cm-ci-lab/actions/runs/41204065432) |
| sonnet-direct | astral-sh/uv#23017 | r1 | $0.0400 / 2 | $0.0289 / 2 | [41204055607](https://github.com/mksglu/cm-ci-lab/actions/runs/41204055607) | [41204050124](https://github.com/mksglu/cm-ci-lab/actions/runs/41204050124) |
| sonnet-direct | denoland/deno#36944 | r1 | $0.0595 / 2 | $0.0515 / 2 | [41204086375](https://github.com/mksglu/cm-ci-lab/actions/runs/41204086375) | [41204081216](https://github.com/mksglu/cm-ci-lab/actions/runs/41204081216) |
| sonnet-direct | denoland/deno#37046 | r1 | $0.0599 / 2 | $0.0662 / 2 | [41204070829](https://github.com/mksglu/cm-ci-lab/actions/runs/41204070829) | [41204076115](https://github.com/mksglu/cm-ci-lab/actions/runs/41204076115) |
| sonnet-direct | facebook/react#38025 | r1 | $0.0671 / 2 | $0.0268 / 2 | [41203702589](https://github.com/mksglu/cm-ci-lab/actions/runs/41203702589) | [41203707928](https://github.com/mksglu/cm-ci-lab/actions/runs/41203707928) |
| sonnet-direct | facebook/react#38034 | r1 | $0.0702 / 2 | $0.0521 / 2 | [41203696086](https://github.com/mksglu/cm-ci-lab/actions/runs/41203696086) | [41203690460](https://github.com/mksglu/cm-ci-lab/actions/runs/41203690460) |
| sonnet-direct | langchain-ai/langchain#41512 | r1 | $0.0659 / 2 | $0.0522 / 2 | [41203928140](https://github.com/mksglu/cm-ci-lab/actions/runs/41203928140) | [41203922991](https://github.com/mksglu/cm-ci-lab/actions/runs/41203922991) |
| sonnet-direct | langchain-ai/langchain#41520 | r1 | $0.0598 / 2 | $0.0542 / 2 | [41203912131](https://github.com/mksglu/cm-ci-lab/actions/runs/41203912131) | [41203917666](https://github.com/mksglu/cm-ci-lab/actions/runs/41203917666) |
| sonnet-direct | microsoft/vscode#345283 | r1 | $0.0944 / 6 | $0.0631 / 5 | [41203724557](https://github.com/mksglu/cm-ci-lab/actions/runs/41203724557) | [41203730237](https://github.com/mksglu/cm-ci-lab/actions/runs/41203730237) |
| sonnet-direct | microsoft/vscode#345293 | r1 | $0.0526 / 2 | $0.0576 / 2 | [41203719183](https://github.com/mksglu/cm-ci-lab/actions/runs/41203719183) | [41203713608](https://github.com/mksglu/cm-ci-lab/actions/runs/41203713608) |
| sonnet-direct | vercel/next.js#100935 | r1 | $0.0782 / 2 | $0.0643 / 2 | [41203901532](https://github.com/mksglu/cm-ci-lab/actions/runs/41203901532) | [41203906867](https://github.com/mksglu/cm-ci-lab/actions/runs/41203906867) |
| sonnet-direct | vercel/next.js#100956 | r1 | $0.0763 / 2 | $0.0854 / 2 | [41203896270](https://github.com/mksglu/cm-ci-lab/actions/runs/41203896270) | [41203891173](https://github.com/mksglu/cm-ci-lab/actions/runs/41203891173) |
