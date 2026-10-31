> **INVALID: do not use the numbers below.** The lab tenant `t_ci_lab_1` used up its 1,000 free requests and was paused at 2026-10-31 10:29:57 UTC. A paused tenant gets plain pass-through: the gateway forwards the request unchanged, with no savings. 7 of the 12 gateway-arm runs behind this doc started after that time and 4 were running across it, so this doc compares direct with a paused pass-through, not with the gateway. The tenant is back in full mode and a clean re-run is in progress. Note added 2026-10-31.

# Opus triage benchmark (2026-10-31)

CI failure fix on Opus (`claude-opus-5-5`), the 12 tasks of `triage.yml`, 1 round x 2 arms = 24 runs. Headless `claude -p` (native installer, `stream-json`), arms `direct-ts` (direct API + ENABLE_TOOL_SEARCH) and `gateway`. Workflow `.github/workflows/opus-triage.yml` (a copy of `triage.yml` with stream-json and a model default of Opus). Tag `a1031-opus-opus-r1`. Nothing here is published.

## Result vs the pass bar (fixed in advance): NOT MET

| bar | Opus (12 pairs, 12 tasks) |
|---|---|
| task-resampled CI upper bound < 0 | **NO**: gateway cost +15.9%, CI +2.7% to +32.4% (the whole interval is above zero) |
| quality not lower than direct-ts | **NO**: pass 11/12 vs 12/12 (black, gateway arm) |
| 0 errors | yes, 0 (no `is_error`, no zero cost, no "Credit balance is too low") |
| net saving > 0 | **NO**: -$0.0312 per run |

On Opus the gateway is dearer, not cheaper. It was cheaper in 4 of 12 pairs. This is the opposite of the Sonnet result on the same tasks (-22.3%).

## Numbers

Mean paired log-ratio gateway/direct-ts = +0.1473, shown as exp(mean)-1 = +15.9%. Bootstrap resamples the 12 tasks, 10,000 resamples, seed 1.

| arm | pass | errors | mean turns | mean cost | uncached | cache_write | cache_read | output |
|---|---|---|---|---|---|---|---|---|
| direct-ts | 12/12 | 0 | 8.58 | $0.1379 | 15 | 10,785 | 161,428 | 2,579 |
| gateway | 11/12 | 0 | 8.08 | $0.1617 | 181 | 15,168 | 139,942 | 2,859 |

Cost per turn: $0.0161 direct-ts, $0.0200 gateway. Gateway took fewer turns (8.08 vs 8.58) but each turn cost 25% more.

Net per run = (0.1379 - 0.1617) - 0.0009 x 8.08 = -$0.0312.

McNemar: 1 direct-only pass (black), 0 gateway-only passes. Total model spend $3.595 (cap $15).

## Extra line only: pooled with Sonnet

Not a bar result. Sonnet pairs are the 24 existing runs (round 1 + round 2 of `docs/triage-bench-1031.md`), Opus 12 pairs; 36 pairs, same 12 tasks, task-resampled: -11.2%, CI -18.0% to -2.5%, cheaper 25/36. This hides the split: Sonnet -22.3% (CI -29.4% to -13.6%), Opus +15.9%. Do not quote the pooled number as an Opus result.

## Per pair

| task | direct-ts cost / turns / pass | gateway cost / turns / pass | ratio | direct-ts run | gateway run |
|---|---|---|---|---|---|
| axios | $0.1292 / 7 / True | $0.1407 / 8 / True | 1.09 | [41193387841](https://github.com/mksglu/cm-ci-lab/actions/runs/41193387841) | [41193392004](https://github.com/mksglu/cm-ci-lab/actions/runs/41193392004) |
| black | $0.4325 / 27 / True | $0.4948 / 21 / False | 1.14 | [41193143844](https://github.com/mksglu/cm-ci-lab/actions/runs/41193143844) | [41193148731](https://github.com/mksglu/cm-ci-lab/actions/runs/41193148731) |
| chalk | $0.1548 / 8 / True | $0.1337 / 6 / True | 0.86 | [41193395934](https://github.com/mksglu/cm-ci-lab/actions/runs/41193395934) | [41193400174](https://github.com/mksglu/cm-ci-lab/actions/runs/41193400174) |
| cobra | $0.0831 / 7 / True | $0.0827 / 7 / True | 1.00 | [41193117179](https://github.com/mksglu/cm-ci-lab/actions/runs/41193117179) | [41193121518](https://github.com/mksglu/cm-ci-lab/actions/runs/41193121518) |
| express | $0.0753 / 6 / True | $0.0856 / 5 / True | 1.14 | [41192937662](https://github.com/mksglu/cm-ci-lab/actions/runs/41192937662) | [41192941116](https://github.com/mksglu/cm-ci-lab/actions/runs/41192941116) |
| fd | $0.1466 / 6 / True | $0.1965 / 10 / True | 1.34 | [41193405012](https://github.com/mksglu/cm-ci-lab/actions/runs/41193405012) | [41193409448](https://github.com/mksglu/cm-ci-lab/actions/runs/41193409448) |
| flask | $0.1551 / 8 / True | $0.2411 / 8 / True | 1.55 | [41192930725](https://github.com/mksglu/cm-ci-lab/actions/runs/41192930725) | [41192934128](https://github.com/mksglu/cm-ci-lab/actions/runs/41192934128) |
| gin | $0.1430 / 9 / True | $0.1396 / 7 / True | 0.98 | [41192740702](https://github.com/mksglu/cm-ci-lab/actions/runs/41192740702) | [41192743877](https://github.com/mksglu/cm-ci-lab/actions/runs/41192743877) |
| koa | $0.0902 / 8 / True | $0.1370 / 9 / True | 1.52 | [41192944032](https://github.com/mksglu/cm-ci-lab/actions/runs/41192944032) | [41192947334](https://github.com/mksglu/cm-ci-lab/actions/runs/41192947334) |
| requests | $0.0790 / 5 / True | $0.0684 / 5 / True | 0.87 | [41192923437](https://github.com/mksglu/cm-ci-lab/actions/runs/41192923437) | [41192927068](https://github.com/mksglu/cm-ci-lab/actions/runs/41192927068) |
| rich | $0.0689 / 5 / True | $0.1236 / 4 / True | 1.79 | [41193134523](https://github.com/mksglu/cm-ci-lab/actions/runs/41193134523) | [41193139437](https://github.com/mksglu/cm-ci-lab/actions/runs/41193139437) |
| ripgrep | $0.0963 / 7 / True | $0.0971 / 7 / True | 1.01 | [41193125989](https://github.com/mksglu/cm-ci-lab/actions/runs/41193125989) | [41193130262](https://github.com/mksglu/cm-ci-lab/actions/runs/41193130262) |

Ratio above 1 means the gateway cost more. Dearer on the gateway in 8 pairs (rich 1.79, flask 1.55, koa 1.52, fd 1.34, black 1.14, express 1.14, axios 1.09, ripgrep 1.01). Cheaper in 4 (chalk 0.86, requests 0.87, gin 0.98, cobra 1.00 to two decimals, $0.0827 vs $0.0831).

## Quality: pass rate and patch sanity

- Pass: 12/12 direct-ts, 11/12 gateway. The one miss is black (gateway). Verify restores the test files from the snapshot before the test run.
- No patch in any of the 24 runs edits a test file (checked by path).
- Black, gateway: the patch is plausible (early return when no lines are left, `is_changed_block=True`) but incomplete. After restore, 1 test fails: `test_line_ranges_at_start_of_file_stay_inside_joined_statement`, the same test that failed on both arms in the Sonnet round 2. The direct-ts Opus run passed it, after 27 turns ($0.4325) against 21 turns on the gateway ($0.4948).
- Gin: the arms chose different fixes. direct-ts replaced the reslice by `append` in `tree.go` (identical to the upstream fix). The gateway arm instead patched `Context.reset()` in `context.go` to reallocate `skippedNodes` when the capacity is below `maxSections`. It passes the real suite, but it is a workaround at another layer, not the upstream fix. I count it as a pass with a weaker patch.
- All other pairs touch the same files with equivalent small patches (rich: 1 file `rich/cells.py` on both; fd and flask: same 2 files).

## Anatomy (2 tasks, per request and per arm)

Tokens from the per-message usage of each run (`lab/opus/results.json`, field `pm`). "cache write" is new bytes the request put in the cache; "cache read" is bytes served from the cache; "uncached" is input paid at the full price.

### rich (gateway 1.79x dearer)

**rich, direct-ts** (run 41193134523, $0.0689)

| req | uncached | cache write | cache read | output | tool |
|---|---|---|---|---|---|
| 1 | 2 | 3746 | 14600 | 16 | Bash |
| 2 | 2 | 585 | 18346 | 16 | Bash |
| 3 | 2 | 954 | 18931 | 8 | Bash |
| 4 | 2 | 477 | 19885 | 59 | Bash |
| 5 | 2 | 414 | 20362 | 332 | final answer |

**rich, gateway** (run 41193139437, $0.1236)

| req | uncached | cache write | cache read | output | tool |
|---|---|---|---|---|---|
| 1 | 2 | 3747 | 14466 | 16 | Bash |
| 2 | 2 | 12095 | 18213 | 41 | Grep |
| 3 | 2 | 680 | 30308 | 8 | Bash |
| 4 | 2 | 831 | 30988 | 6 | final answer |

### requests (gateway 0.87x, cheaper)

**requests, direct-ts** (run 41192923437, $0.0790)

| req | uncached | cache write | cache read | output | tool |
|---|---|---|---|---|---|
| 1 | 2 | 3748 | 14600 | 16 | Bash |
| 2 | 2 | 3282 | 18348 | 21 | Bash |
| 3 | 2 | 1240 | 21630 | 8 | Bash |
| 4 | 2 | 592 | 22870 | 336 | final answer |

**requests, gateway** (run 41192927068, $0.0684)

| req | uncached | cache write | cache read | output | tool |
|---|---|---|---|---|---|
| 1 | 2 | 3745 | 14466 | 16 | Bash |
| 2 | 2 | 1663 | 18211 | 16 | Bash |
| 3 | 2 | 1306 | 19874 | 10 | Bash |
| 4 | 2 | 529 | 21180 | 317 | final answer |

### Where the gateway saves, and where it does not

Across the 12 tasks:

| | direct-ts | gateway |
|---|---|---|
| request 1 (the fixed prefix: tools + system), mean cache write | 4,187 | 3,775 |
| request 1, mean cache read | 14,472 | 12,031 |
| request 1, mean uncached | 2 | 166 |
| all requests, mean cache write | 1,471 | 2,141 |
| all requests, mean cache read | 22,013 | 19,757 |
| all requests, mean uncached | 2 | 25.5 |

- Saves: the fixed prefix is smaller. Request 1 reads about 2,400 fewer cached tokens and writes about 400 fewer. In `requests`, this is the whole saving: requests 2 to 4 are within a few hundred tokens of direct-ts, and the run is 13% cheaper.
- Does not save: the new content of each turn (tool results). The per-request cache write is HIGHER on the gateway (2,141 vs 1,471 tokens), not equal. Rich shows it: request 2 on the gateway wrote 12,095 tokens after a Grep call, against 585 in direct-ts after a Bash call. The model picked a different tool, and the result was bigger. That is a path effect, not a gateway cut, and one such step costs more than the prefix saving of the whole run.
- Costs: uncached input is 166 tokens on request 1 and about 25 per request after, against 2 in direct-ts. The gateway request carries a few hundred uncached tokens that the direct request does not; at Opus prices that is small, but it is never zero. The fee of $0.0009 per request adds $0.0073 per run.
- Why Opus differs from Sonnet: not tested. The numbers show the token shift (more cache write per request, a few uncached tokens per request), not its cause.

## Caveats

- 1 round only, 12 pairs. Per-run noise is large (rich $0.069 vs $0.124, 5 vs 4 turns). The CI lower bound is +2.7%, but only 8 of 12 pairs are dearer; a second round would narrow the CI.
- The black pair is the dearest by far ($0.43 and $0.49). Without black the mean ratio is +16.0%, so it does not drive the result.
- Opus turns in these tasks are few (4 to 10 for most), so the fixed prefix is a big share of the cost. This favours the gateway; it still lost.
- A different failure mode of the two arms (different tool choices at the same step) dominates the pairs. This lab cannot separate a gateway effect on tool choice from model randomness with 1 round.
- Gateway fee of $0.0009 per request is in the net saving.

## Files

- `lab/opus/results.json`: lab metrics and per-message usage of all 24 runs.
- `lab/opus/analyze.py`: paired stats (task bootstrap, seed 1, 10,000).
- `lab/opus/usage.py`: per-message usage from stream-json.
