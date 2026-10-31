# Triage benchmark, round 2 (2026-10-31)

Replication of the round 1 triage benchmark on 6 new tasks. Sonnet 5.5, headless `claude -p` (native installer), arms `direct-ts` (direct API + ENABLE_TOOL_SEARCH) and `gateway`. Workflow `.github/workflows/triage.yml`. Nothing here is published.

## Result vs the pass bar (fixed in advance)

| bar | round 2 (12 pairs) | pooled (24 pairs, 12 tasks) |
|---|---|---|
| CI upper bound < 0 | pair-resampled: yes (-28.0% to -1.5%). Task-resampled (6 tasks): NO (-29.4% to +0.4%) | yes, task-resampled: -29.5% to -13.7% (pair-resampled -28.8% to -14.7%) |
| net saving > 0 | yes, $0.0018 per run | yes, $0.0041 per run |
| pass rate not lower than baseline | yes, 11/12 vs 11/12 | yes, 23/24 vs 23/24 |
| 0 errors | yes, 0 | yes, 0 |

Round 2 alone is weaker than round 1: -15.7% against -28.3%. The pair-resampled CI clears zero, but the task-resampled CI touches it (upper +0.4%). Only the pooled result clears the bar on the stricter resampling. Gateway was cheaper in 9 of 12 pairs (21 of 24 pooled).

## Round 2 numbers

Paired log-ratio mean -0.1710 = -15.7% cost (gateway vs direct-ts). Bootstrap 95% CI, 10,000 resamples, seed 1.

| arm | pass | errors | mean turns | mean cost | uncached | cache_write | cache_read | output |
|---|---|---|---|---|---|---|---|---|
| direct-ts | 11/12 | 0 | 7.50 | $0.0649 | 14 | 11,379 | 147,876 | 2,159 |
| gateway | 11/12 | 0 | 7.83 | $0.0560 | 524 | 9,026 | 105,996 | 2,183 |

McNemar exact: 0 direct-only passes, 0 gateway-only passes, p = 1.000 (the one failing task, black n1, failed on both arms).

Net saving per run = (0.0649 - 0.0560) - 0.0009 x 7.83 = $0.0018.

## Pooled, round 1 + round 2

24 pairs, 12 tasks. Mean log-ratio -0.2517 = -22.3%. Task-resampled CI (resample the 12 tasks, 10,000, seed 1): -29.5% to -13.7%. Pair-resampled: -28.8% to -14.7%. Cheaper on gateway 21/24. Pass 23/24 vs 23/24, McNemar p = 1.000. Errors 0. Mean turns 6.71 vs 6.71. Mean cost $0.0523 vs $0.0422. Tokens direct-ts / gateway: uncached 12 / 519, cache_write 9,408 / 6,895, cache_read 127,234 / 81,067, output 1,602 / 1,579. Net saving $0.0041 per run.

## Tasks (all new, none from round 1)

| task | repo (stars) | lang | PR | files reverted | baseline log |
|---|---|---|---|---|---|
| rich | Textualize/rich (57.7k) | Python | #3180 | rich/_wrap.py, rich/cells.py | 76.7 KB |
| black | psf/black (42.1k) | Python | #5484 | src/black/__init__.py, src/black/ranges.py | 61.7 KB |
| axios | axios/axios (109k) | JS | #11038 | lib/helpers/combineURLs.js | 16.1 KB |
| chalk | chalk/chalk (23.3k) | JS | #688 | source/vendor/supports-color/index.js | 7.3 KB |
| gin | gin-gonic/gin (89.5k) | Go | #4852 | tree.go | 65.3 KB |
| fd | sharkdp/fd (44.9k) | Rust | #2193 | src/cli.rs, src/main.rs | 20.6 KB |

Longer-task condition: black and fd are multi-file fixes (both arms patched 2 files). No log passed 100 KB (largest 76.7 KB), so the log-size route was not met; the multi-file route was met by 2 tasks. Rich reverted 2 files but every patch needed only `rich/cells.py`.

## Task validity (baseline must fail, control must pass)

Each task fails at baseline and passes in a control run with the fix kept (`control=true`). Lab changes needed: rich pins `setuptools<81` and `pygments==2.17.2` (newer pygments changed ANSI output in 10 unrelated tests); black pins `pytest<9` (INTERNALERROR in its plugin); axios skips `tests/unit/adapters/fetch.test.js` (2 tests fail with the fix in place too).

| task | baseline run (fails) | control run (passes) |
|---|---|---|
| rich | [41188332807](https://github.com/mksglu/cm-ci-lab/actions/runs/41188332807) | [41188338013](https://github.com/mksglu/cm-ci-lab/actions/runs/41188338013) |
| black | [41187998225](https://github.com/mksglu/cm-ci-lab/actions/runs/41187998225) | [41188001225](https://github.com/mksglu/cm-ci-lab/actions/runs/41188001225) |
| axios | [41188003983](https://github.com/mksglu/cm-ci-lab/actions/runs/41188003983) | [41188006652](https://github.com/mksglu/cm-ci-lab/actions/runs/41188006652) |
| chalk | [41187768864](https://github.com/mksglu/cm-ci-lab/actions/runs/41187768864) | [41187771335](https://github.com/mksglu/cm-ci-lab/actions/runs/41187771335) |
| gin | [41187775215](https://github.com/mksglu/cm-ci-lab/actions/runs/41187775215) | [41187778063](https://github.com/mksglu/cm-ci-lab/actions/runs/41187778063) |
| fd | [41187781965](https://github.com/mksglu/cm-ci-lab/actions/runs/41187781965) | [41187784804](https://github.com/mksglu/cm-ci-lab/actions/runs/41187784804) |

## Per pair

| task | round | direct-ts cost / turns / pass | gateway cost / turns / pass | direct-ts run | gateway run |
|---|---|---|---|---|---|
| axios | n1 | $0.0409 / 5 / True | $0.0331 / 5 / True | [41188524293](https://github.com/mksglu/cm-ci-lab/actions/runs/41188524293) | [41188531671](https://github.com/mksglu/cm-ci-lab/actions/runs/41188531671) |
| axios | n2 | $0.0407 / 5 / True | $0.0364 / 5 / True | [41188611050](https://github.com/mksglu/cm-ci-lab/actions/runs/41188611050) | [41188617605](https://github.com/mksglu/cm-ci-lab/actions/runs/41188617605) |
| black | n1 | $0.1181 / 12 / False | $0.1297 / 20 / False | [41188506992](https://github.com/mksglu/cm-ci-lab/actions/runs/41188506992) | [41188516574](https://github.com/mksglu/cm-ci-lab/actions/runs/41188516574) |
| black | n2 | $0.1288 / 15 / True | $0.1218 / 15 / True | [41188600153](https://github.com/mksglu/cm-ci-lab/actions/runs/41188600153) | [41188606142](https://github.com/mksglu/cm-ci-lab/actions/runs/41188606142) |
| chalk | n1 | $0.0528 / 5 / True | $0.0535 / 8 / True | [41188540316](https://github.com/mksglu/cm-ci-lab/actions/runs/41188540316) | [41188548180](https://github.com/mksglu/cm-ci-lab/actions/runs/41188548180) |
| chalk | n2 | $0.0555 / 5 / True | $0.0479 / 7 / True | [41188624741](https://github.com/mksglu/cm-ci-lab/actions/runs/41188624741) | [41188629624](https://github.com/mksglu/cm-ci-lab/actions/runs/41188629624) |
| fd | n1 | $0.0771 / 7 / True | $0.0578 / 7 / True | [41188572366](https://github.com/mksglu/cm-ci-lab/actions/runs/41188572366) | [41188581486](https://github.com/mksglu/cm-ci-lab/actions/runs/41188581486) |
| fd | n2 | $0.0900 / 10 / True | $0.0516 / 6 / True | [41188644304](https://github.com/mksglu/cm-ci-lab/actions/runs/41188644304) | [41188650852](https://github.com/mksglu/cm-ci-lab/actions/runs/41188650852) |
| gin | n1 | $0.0437 / 6 / True | $0.0331 / 5 / True | [41188555561](https://github.com/mksglu/cm-ci-lab/actions/runs/41188555561) | [41188563975](https://github.com/mksglu/cm-ci-lab/actions/runs/41188563975) |
| gin | n2 | $0.0645 / 11 / True | $0.0312 / 5 / True | [41188634615](https://github.com/mksglu/cm-ci-lab/actions/runs/41188634615) | [41188639455](https://github.com/mksglu/cm-ci-lab/actions/runs/41188639455) |
| rich | n1 | $0.0324 / 4 / True | $0.0479 / 5 / True | [41188493167](https://github.com/mksglu/cm-ci-lab/actions/runs/41188493167) | [41188499717](https://github.com/mksglu/cm-ci-lab/actions/runs/41188499717) |
| rich | n2 | $0.0339 / 5 / True | $0.0282 / 6 / True | [41188590167](https://github.com/mksglu/cm-ci-lab/actions/runs/41188590167) | [41188594448](https://github.com/mksglu/cm-ci-lab/actions/runs/41188594448) |

Spend: round 2 model cost $1.451 (24 runs); baseline, control and cause runs call no model. Under the $20 cap.

## Round 1 runs (reused, from the earlier attempt)

Tags r1 and r2, tasks requests, flask, express, koa, cobra, ripgrep.

| task | tag | direct-ts | gateway |
|---|---|---|---|
| cobra | r1 | [41153100681](https://github.com/mksglu/cm-ci-lab/actions/runs/41153100681) | [41153106717](https://github.com/mksglu/cm-ci-lab/actions/runs/41153106717) |
| cobra | r2 | [41153609820](https://github.com/mksglu/cm-ci-lab/actions/runs/41153609820) | [41153615867](https://github.com/mksglu/cm-ci-lab/actions/runs/41153615867) |
| express | r1 | [41153077087](https://github.com/mksglu/cm-ci-lab/actions/runs/41153077087) | [41153082953](https://github.com/mksglu/cm-ci-lab/actions/runs/41153082953) |
| express | r2 | [41153584840](https://github.com/mksglu/cm-ci-lab/actions/runs/41153584840) | [41153592471](https://github.com/mksglu/cm-ci-lab/actions/runs/41153592471) |
| flask | r1 | [41153066380](https://github.com/mksglu/cm-ci-lab/actions/runs/41153066380) | [41153071640](https://github.com/mksglu/cm-ci-lab/actions/runs/41153071640) |
| flask | r2 | [41153571154](https://github.com/mksglu/cm-ci-lab/actions/runs/41153571154) | [41153578219](https://github.com/mksglu/cm-ci-lab/actions/runs/41153578219) |
| koa | r1 | [41153088504](https://github.com/mksglu/cm-ci-lab/actions/runs/41153088504) | [41153094763](https://github.com/mksglu/cm-ci-lab/actions/runs/41153094763) |
| koa | r2 | [41153598736](https://github.com/mksglu/cm-ci-lab/actions/runs/41153598736) | [41153604110](https://github.com/mksglu/cm-ci-lab/actions/runs/41153604110) |
| requests | r1 | [41153056243](https://github.com/mksglu/cm-ci-lab/actions/runs/41153056243) | [41153061281](https://github.com/mksglu/cm-ci-lab/actions/runs/41153061281) |
| requests | r2 | [41153556970](https://github.com/mksglu/cm-ci-lab/actions/runs/41153556970) | [41153564255](https://github.com/mksglu/cm-ci-lab/actions/runs/41153564255) |
| ripgrep | r1 | [41153112215](https://github.com/mksglu/cm-ci-lab/actions/runs/41153112215) | [41153118724](https://github.com/mksglu/cm-ci-lab/actions/runs/41153118724) |
| ripgrep | r2 | [41153621806](https://github.com/mksglu/cm-ci-lab/actions/runs/41153621806) | [41153627890](https://github.com/mksglu/cm-ci-lab/actions/runs/41153627890) |

## Cause check (rich task, 76,347 B failing log)

Run [41188770129](https://github.com/mksglu/cm-ci-lab/actions/runs/41188770129) (arm `cause`, no model call). The real `claude -p` request was captured on a local tee proxy (6 requests, 25 tools, no key sent). The Bash tool_use and a tool_result holding the real log were appended, then the body was replayed to the gateway with `x-cm-dry-run: 1`. Bytes of compact JSON (tool_results = result text only):

| block | client | forwarded, is_error=true | forwarded, is_error=false |
|---|---|---|---|
| tools | 71,557 | 27,481 | 27,481 |
| system | 6,357 | 6,357 | 6,357 |
| messages (non-result) | 10,897 | 2,983 | 2,983 |
| tool_results | 76,347 | 16,855 | 6,586 |
| total | 167,267 | 54,995 | 44,237 |

The same numbers hold when 8 small exchanges follow the log (older turn): tools, system and the result deltas are identical.

Findings:

- A failing tool_result with `is_error=true` does NOT stay whole. 76,347 B became 16,855 B (-78%). The `is_error` flag itself is kept. The head is verbatim; the tail is a fold note: `... folded - full output: context-mode-search {docid ...} (76347 B archived ...)`.
- Context for that: `src/code-mode/deinline-swap.ts` lines 255-257 on origin/main of context-mode-sandbox read `if (!raw || raw.length < CM_TAIL_HARD_CAP) continue;`, the idempotence check, and `if (deps.cmIsErrorResult(b, raw)) continue; // errors are the insight window's job`. So the hard-cap loop (cap 24,576 B, head 4,096, tail 2,048) skips error results on purpose. The 16,855 B result therefore came from another path, the one that line 257 hands errors to; I did not trace it (read only).
- Without `is_error`, the log goes to 6,586 B and ends with the real summary line (`4 failed, 798 passed`), so exit-code evidence survives.
- Most of the byte saving is tools (-44,076 B, 71,557 to 27,481), not tool_results. System is untouched.
- Caveat: this is a synthetic replay of the first turn plus an appended log, not a capture of a full live gateway run. `is_error=true` is what Claude Code sets for a non-zero Bash exit, which I assumed and did not capture.

## Blind patch check (24 patches, arm labels hidden)

Each pair was shuffled to X/Y with seed 7 and read before the arm was known. `package-lock.json` noise from `npm install` was ignored; the 3 test-file edits check was done by file path.

- axios n1, n2: real fix of the regex (`/\/?\/$/` to `/\/+$/`); one n2 patch uses a charCode loop, also real.
- black n1, n2: both add an early return when no lines are left and flip `is_changed_block`; n2 also ignores indentation in the diff (real). Black n1 failed on BOTH arms with the same test.
- chalk n1, n2: six patches treat a numeric FORCE_COLOR as exact level; all real, with different guards.
- fd n1, n2: the upstream design (`bool` options plus `rg_alias_hidden`), real. One n2 patch uses a helper `ignore_hidden()`, real.
- gin n1, n2: all four replace the reslice by `append`, identical to upstream; real.
- rich n1, n2: all four remove the `reversed()` in `chop_cells`; real, minimal.

One test hack found: black n1, gateway arm, edited `tests/test_black.py` (changed the expected indentation in the new test). Verify restores the test files from the snapshot, so the edit has no effect, and that run did not pass anyway. Its source patch matches the direct-ts one. No other patch touches a test file. After restore, both black n1 runs fail the same 1 test (`test_line_ranges_at_start_of_file_stay_inside_joined_statement`), so this is a shared miss, not an arm effect.

## Caveats

- Round 2 alone does not clear the bar on task resampling; the claim rests on pooling.
- Gateway used more turns in 5 pairs, including black n1 (20 vs 12) and chalk n1 (8 vs 5); rich n1 was dearer on the gateway ($0.0479 vs $0.0324).
- Both arms are noisy per run (direct-ts black 0.118 to 0.129; gin 0.044 to 0.065).
- Gateway pays $0.0009 per request; this is in the net saving.
