# Opus triage benchmark (2026-10-31)

CI failure fix on Opus (`claude-opus-5-5`), the 12 tasks of `triage.yml`, 2 rounds x 2 arms = 48 runs. Headless `claude -p` (native installer, `stream-json`), arms `direct-ts` (direct API + ENABLE_TOOL_SEARCH, the fair baseline) and `gateway` (ANTHROPIC_BASE_URL + the CI headers `ci init` writes). Workflow `.github/workflows/opus-triage.yml`. Tags `c1031-opus-opus-r1` and `c1031-opus-opus-r2`. Nothing here is published.

History: the first run of this bench (tag `a1031-opus-opus-r1`, 1 round) was invalid. The lab tenant `t_ci_lab_1` was paused at 2026-10-31 10:29:57 UTC, so the gateway arm ran as plain pass-through. This is the clean re-run, with the tenant in full mode.

## Validity

- Quota guard before round 1 and after round 2: mode `full`, `used_paused` = 1518 both times. It did not grow, so no request ran paused. Both rounds are valid.
- Request 1 (input + cache write + cache read of the first assistant message), mean of 24 runs: direct-ts 18,661 tokens, gateway 10,864 tokens (-41.8%). In the invalid run the two were equal. The gateway cut is visible in every run.

## Result vs the pass bar (fixed in advance): MET

| bar | Opus (24 pairs, 12 tasks x 2 rounds) |
|---|---|
| task-resampled CI upper bound < 0 | **yes**: gateway cost -16.8%, CI -23.6% to -10.0% |
| quality not lower than direct-ts | **yes**: pass 24/24 vs 24/24, McNemar exact p = 1.000 (0 vs 0 discordant); no patch edits a test file; patch note on gin below |
| 0 errors | yes, 0 (no `is_error`, no zero cost, no "Credit balance is too low") |
| every round valid | yes (`used_paused` unchanged at 1518) |
| net saving > 0 | yes: +$0.0128 per run |

Gateway was cheaper in 21 of 24 pairs. Per round: round 1 -18.1% (12 pairs, cheaper 10/12), round 2 -15.4% (cheaper 11/12).

## Numbers

Mean paired log-ratio gateway/direct-ts, shown as exp(mean)-1 = -16.8%. Pairs are (task, round). Bootstrap resamples the 12 tasks, 10,000 resamples, seed 1.

| arm | pass | errors | mean turns | mean cost | uncached | cache_write | cache_read | output |
|---|---|---|---|---|---|---|---|---|
| direct-ts | 24/24 | 0 | 8.12 | $0.1368 | 14 | 10,872 | 154,068 | 2,576 |
| gateway | 24/24 | 0 | 7.29 | $0.1174 | 518 | 9,076 | 104,742 | 2,452 |

Net per run = (0.1368 - 0.1174) - 0.0009 x 7.29 = +$0.0128 (fee counted on `num_turns`). Counting the 6.96 assistant messages per run found in the per-message usage instead gives +$0.0131. Total model spend $6.10 for the 48 runs (cap $15).

Sonnet on the same tasks (`docs/triage-bench-1031.md`): -22.3%. Opus saves less in percent, more in dollars per run ($0.0194 before fee vs $0.0101).

## Per pair

| task | round | direct-ts cost / turns / pass | gateway cost / turns / pass | ratio | direct-ts run | gateway run |
|---|---|---|---|---|---|---|
| axios | r1 | $0.1094 / 5 / True | $0.0919 / 5 / True | 0.84 | [41200887759](https://github.com/mksglu/cm-ci-lab/actions/runs/41200887759) | [41200891912](https://github.com/mksglu/cm-ci-lab/actions/runs/41200891912) |
| axios | r2 | $0.1243 / 7 / True | $0.0997 / 6 / True | 0.80 | [41202094244](https://github.com/mksglu/cm-ci-lab/actions/runs/41202094244) | [41202098061](https://github.com/mksglu/cm-ci-lab/actions/runs/41202098061) |
| black | r1 | $0.4428 / 28 / True | $0.3435 / 14 / True | 0.78 | [41200879845](https://github.com/mksglu/cm-ci-lab/actions/runs/41200879845) | [41200883750](https://github.com/mksglu/cm-ci-lab/actions/runs/41200883750) |
| black | r2 | $0.3711 / 21 / True | $0.3460 / 21 / True | 0.93 | [41202086607](https://github.com/mksglu/cm-ci-lab/actions/runs/41202086607) | [41202090473](https://github.com/mksglu/cm-ci-lab/actions/runs/41202090473) |
| chalk | r1 | $0.1259 / 5 / True | $0.1236 / 6 / True | 0.98 | [41200895715](https://github.com/mksglu/cm-ci-lab/actions/runs/41200895715) | [41200899709](https://github.com/mksglu/cm-ci-lab/actions/runs/41200899709) |
| chalk | r2 | $0.1321 / 7 / True | $0.1205 / 8 / True | 0.91 | [41202101571](https://github.com/mksglu/cm-ci-lab/actions/runs/41202101571) | [41202104913](https://github.com/mksglu/cm-ci-lab/actions/runs/41202104913) |
| cobra | r1 | $0.0840 / 7 / True | $0.0531 / 7 / True | 0.63 | [41200853883](https://github.com/mksglu/cm-ci-lab/actions/runs/41200853883) | [41200858093](https://github.com/mksglu/cm-ci-lab/actions/runs/41200858093) |
| cobra | r2 | $0.0741 / 5 / True | $0.0593 / 7 / True | 0.80 | [41202063301](https://github.com/mksglu/cm-ci-lab/actions/runs/41202063301) | [41202067477](https://github.com/mksglu/cm-ci-lab/actions/runs/41202067477) |
| express | r1 | $0.0751 / 5 / True | $0.0556 / 5 / True | 0.74 | [41200838976](https://github.com/mksglu/cm-ci-lab/actions/runs/41200838976) | [41200842629](https://github.com/mksglu/cm-ci-lab/actions/runs/41200842629) |
| express | r2 | $0.0793 / 5 / True | $0.0685 / 6 / True | 0.86 | [41202048232](https://github.com/mksglu/cm-ci-lab/actions/runs/41202048232) | [41202052178](https://github.com/mksglu/cm-ci-lab/actions/runs/41202052178) |
| fd | r1 | $0.2593 / 12 / True | $0.1343 / 6 / True | 0.52 | [41200911485](https://github.com/mksglu/cm-ci-lab/actions/runs/41200911485) | [41200915369](https://github.com/mksglu/cm-ci-lab/actions/runs/41200915369) |
| fd | r2 | $0.1955 / 8 / True | $0.2769 / 12 / True | 1.42 | [41202115803](https://github.com/mksglu/cm-ci-lab/actions/runs/41202115803) | [41202120608](https://github.com/mksglu/cm-ci-lab/actions/runs/41202120608) |
| flask | r1 | $0.1513 / 7 / True | $0.1701 / 7 / True | 1.12 | [41200831151](https://github.com/mksglu/cm-ci-lab/actions/runs/41200831151) | [41200835330](https://github.com/mksglu/cm-ci-lab/actions/runs/41200835330) |
| flask | r2 | $0.1419 / 7 / True | $0.1299 / 8 / True | 0.92 | [41202040495](https://github.com/mksglu/cm-ci-lab/actions/runs/41202040495) | [41202044379](https://github.com/mksglu/cm-ci-lab/actions/runs/41202044379) |
| gin | r1 | $0.1413 / 9 / True | $0.0912 / 8 / True | 0.65 | [41200903493](https://github.com/mksglu/cm-ci-lab/actions/runs/41200903493) | [41200907530](https://github.com/mksglu/cm-ci-lab/actions/runs/41200907530) |
| gin | r2 | $0.1185 / 9 / True | $0.1096 / 9 / True | 0.93 | [41202108717](https://github.com/mksglu/cm-ci-lab/actions/runs/41202108717) | [41202112324](https://github.com/mksglu/cm-ci-lab/actions/runs/41202112324) |
| koa | r1 | $0.0900 / 8 / True | $0.0849 / 8 / True | 0.94 | [41200846308](https://github.com/mksglu/cm-ci-lab/actions/runs/41200846308) | [41200849805](https://github.com/mksglu/cm-ci-lab/actions/runs/41200849805) |
| koa | r2 | $0.0973 / 9 / True | $0.0789 / 6 / True | 0.81 | [41202055895](https://github.com/mksglu/cm-ci-lab/actions/runs/41202055895) | [41202059616](https://github.com/mksglu/cm-ci-lab/actions/runs/41202059616) |
| requests | r1 | $0.0722 / 5 / True | $0.0613 / 5 / True | 0.85 | [41200823284](https://github.com/mksglu/cm-ci-lab/actions/runs/41200823284) | [41200827151](https://github.com/mksglu/cm-ci-lab/actions/runs/41200827151) |
| requests | r2 | $0.0849 / 6 / True | $0.0650 / 5 / True | 0.77 | [41202033641](https://github.com/mksglu/cm-ci-lab/actions/runs/41202033641) | [41202037190](https://github.com/mksglu/cm-ci-lab/actions/runs/41202037190) |
| rich | r1 | $0.0651 / 4 / True | $0.1015 / 4 / True | 1.56 | [41200872054](https://github.com/mksglu/cm-ci-lab/actions/runs/41200872054) | [41200875804](https://github.com/mksglu/cm-ci-lab/actions/runs/41200875804) |
| rich | r2 | $0.0610 / 4 / True | $0.0419 / 4 / True | 0.69 | [41202079693](https://github.com/mksglu/cm-ci-lab/actions/runs/41202079693) | [41202083234](https://github.com/mksglu/cm-ci-lab/actions/runs/41202083234) |
| ripgrep | r1 | $0.0905 / 6 / True | $0.0583 / 4 / True | 0.64 | [41200863851](https://github.com/mksglu/cm-ci-lab/actions/runs/41200863851) | [41200867935](https://github.com/mksglu/cm-ci-lab/actions/runs/41200867935) |
| ripgrep | r2 | $0.0952 / 6 / True | $0.0527 / 4 / True | 0.55 | [41202071587](https://github.com/mksglu/cm-ci-lab/actions/runs/41202071587) | [41202075787](https://github.com/mksglu/cm-ci-lab/actions/runs/41202075787) |

Ratio above 1 means the gateway cost more. Dearer on the gateway in 3 pairs: rich r1 1.56, fd r2 1.42, flask r1 1.12. Cheaper in the other 21.

## Quality: pass rate and patch sanity

- Pass: 24/24 on both arms. After each run the test files are restored from the snapshot, then the real test command runs.
- No patch edits a test file. Checked by path against the snapshot test list. The only path with "test" in it is `src/flask/testing.py`, which is a source file the task reverts, edited on both arms.
- 22 of 24 pairs touched the same files on both arms. The two other pairs are gin:
  - r1: direct-ts patched `gin.go` (re-allocates a pooled context when its buffers are too small); gateway patched `context.go` (`reset()` re-makes `skippedNodes` when capacity is low).
  - r2: direct-ts patched `tree.go` with `append` instead of the reslice, the same change as the upstream fix; gateway patched `gin.go` (`handleHTTPRequest` re-makes `skippedNodes`).
  - All four pass the real suite. On gin, direct-ts matched the upstream fix in 1 of 2 rounds and the gateway in 0 of 2; the other three patches are workarounds at another layer. Every other task has equivalent small patches on both arms. With 1 task this is a note, not a result.

## Where the gateway saves

Per-message usage (`lab/opus/results.json`, field `pm`), 167 assistant messages per arm.

| | direct-ts | gateway |
|---|---|---|
| request 1, mean size | 18,661 | 10,864 |
| request 1, mean cache write | 4,123 | 1,219 |
| request 1, mean cache read | 14,536 | 9,150 |
| request 1, mean uncached | 2 | 494 |
| all requests, mean cache write | 1,562 | 1,304 |
| all requests, mean cache read | 22,141 | 15,053 |
| all requests, mean uncached | 2.0 | 74.4 |
| cost per turn | $0.0168 | $0.0161 |

- Saves: the fixed prefix. Request 1 is about 7,800 tokens smaller, and every later request reads a smaller cached prefix (22,141 vs 15,053 mean). This is the whole saving; new tool results are the same bytes on both arms.
- Costs: a few hundred uncached tokens on request 1 (494 vs 2) and 74 per request on average, plus the $0.0009 fee per request.
- Path noise: the saving per pair is large when the run is short (fd r1 0.52, ripgrep r2 0.55) and can flip when the model takes more turns on the gateway (fd r2: 12 turns vs 8, 1.42). Rich r1 (1.56) has equal turns (4 vs 4), so that pair is a different tool choice, not the prefix.

## Caveats

- 2 rounds, 24 pairs, 12 tasks. The CI resamples tasks, so it reflects task variance; it does not include model sampling noise beyond the 2 rounds.
- Gateway fee of $0.0009 per request is in the net saving.
- Quality is pass/fail on the real suite plus a patch check. No blind judge on the patch text.
- Opus turns in these tasks are few (4 to 28), so the fixed prefix is a large share of the cost.

## Files

- `lab/opus/results.json`: lab metrics and per-message usage of the runs.
- `lab/opus/analyze2.py`: paired stats for N rounds (task bootstrap, seed 1, 10,000; exact McNemar; request-1 size).
- `lab/opus/analyze.py`: the 1-round version used for the invalid run.
- `lab/opus/usage.py`: per-message usage from stream-json.
