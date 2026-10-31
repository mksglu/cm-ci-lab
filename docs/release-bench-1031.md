# Release notes and changelog benchmark (2026-10-31, clean re-run)

Area: release notes. Claude Code headless (`claude -p`, native installer), Sonnet 5.5, arms `direct-ts` (direct API + ENABLE_TOOL_SEARCH) and `gateway`. Workflow `.github/workflows/release.yml`, judge workflow `.github/workflows/release-judge.yml`, files under `lab/release/`. Tags `c1031-release-sonnet-r1`, `-r2`. Nothing here is published.

History: the first run of this bench (tag `a1031-release-sonnet-r1`/`-r2`) was invalid. The lab tenant `t_ci_lab_1` was paused (free quota used up) at 2026-10-31 10:29:57 UTC, so its gateway arm was plain pass-through. This is the clean re-run on the same 12 releases, with the tenant in full mode (50,000 requests granted).

## Validity check

- Quota guard before and after the 48 runs: mode `full`, `used_paused` 1518 both times (it did not grow). The round is valid.
- Request 1 (fixed prefix, input + cache_write + cache_read of the first API request), mean over 24 runs per arm: direct-ts 24,943 tokens, gateway 17,150 tokens (-31%). In the invalid run the gap was 134 tokens.

## Result vs the pass bar (fixed in advance)

| bar | result |
|---|---|
| task-resampled CI upper bound < 0 | YES. Cost change -13.9%, CI -20.1% to -8.4% (24 pairs, 12 tasks, 10,000 resamples, seed 1). Cheaper in 19 of 24 pairs. Round 1: -14.5% (CI -22.0..-7.4). Round 2: -13.3% (CI -22.4..-3.0). |
| quality not lower than direct-ts | NOT CLEARLY. Judge score 6.42 vs 6.67 (diff -0.25 of 10, task-resampled CI -0.54 to 0.00); coverage and false claims equal in the judge; scripted coverage 0.830 vs 0.850 (diff -0.020, CI -0.110 to +0.042). The point estimates are lower and the judge CI touches zero. See Quality. |
| 0 errors | YES, 0 of 48 (no is_error, no zero cost, no "Credit balance is too low", every run wrote notes). |
| every round valid | YES (`used_paused` unchanged). |
| net saving per run > 0 | YES. (0.1111 - 0.0969) - 0.0009 x 7.00 = +$0.0080 per run. |

Cost, errors and validity pass. The quality bar is not met cleanly: the gateway notes score 0.25 points lower on a 10-point judge scale, a difference that is at the edge of noise. Do not claim "same quality" for this area from these data; the honest claim is "cheaper by about 14%, quality not shown to differ, point estimate slightly lower".

## Numbers

| arm | errors | mean API requests | mean cost | uncached | cache_write | cache_read | output |
|---|---|---|---|---|---|---|---|
| direct-ts | 0 | 7.33 | $0.1111 | 15 | 21,229 | 211,444 | 3,690 |
| gateway | 0 | 7.00 | $0.0969 | 681 | 19,078 | 145,742 | 3,325 |

Mean turns (CLI `num_turns`): 8.46 direct-ts, 8.12 gateway; gateway minus direct-ts CI -1.21 to +0.50 (turn counts do not differ systematically). Cost per API request: $0.0152 direct-ts, $0.0138 gateway (176 and 168 requests). The fee ($0.0009 x 7.00 = $0.0063 per run) is smaller than the gross saving ($0.0143 per run). Gateway uncached input is higher (681 vs 15) because the gateway rewrites the prefix on some requests; cache reads fall by 31%.

Per task (mean of 2 rounds, gateway vs direct-ts cost): gemini-65 -15%, gemini-66 -17%, mcp-21 -8%, mcp-22 +4%, rg-141 -5%, rg-152 -23%, ruff-171 -37%, ruff-173 -10%, uv-1222 -18%, uv-135 -14%, zod-465 -12%, zod-466 -5%. Eleven of 12 tasks cheaper by mean.

## Method

- Template mirrored: CherryHQ/cherry-studio `prepare-release.yml` (53k stars, claude-code-action): notes from the final user-visible differences between the previous tag and the release, not one entry per commit; tools `Bash(git:*)`, Read, Write, Glob, Grep. PR titles through `gh`, as NVIDIA/OpenShell `release-notes.yml` does. The prompt text is ours; the action is not used (its entrypoint is rejected for this key).
- Tasks (12 real releases, 2 from each of 6 repos): google-gemini/gemini-cli v0.66.0, v0.65.0; astral-sh/uv 0.13.5, 0.12.22; modelcontextprotocol/servers v2.1.0, v2.2.0; BurntSushi/ripgrep 15.2.0, 14.1.1; colinhacks/zod v4.6.6, v4.6.5; astral-sh/ruff 0.17.3, 0.17.1. Defined in `lab/release/tasks.sh`.
- Repo state (`lab/release/prep.sh`): only the new tag and the previous tag are fetched, the remote is removed, and every changelog / release-notes file is pinned to its previous-tag content in each commit of prev..tag, so the published notes cannot be read from the tree. gh is a read-only shim (`lab/release/gh`).
- Notes are written to a file and uploaded as an artifact; nothing is posted or pushed.
- Stats: pairs by (task, round); cost = mean paired log-ratio gateway/direct-ts, shown as exp(mean)-1; 95% CI by bootstrap resampling tasks (rounds stay together), 10,000 resamples, seed 1. Per-message usage is in each artifact (`usage.json`); the run table is `lab/release/results/c1031-runs.json`.
- Spend: $4.99 for 48 runs, $0.93 for 24 judge jobs. Total $5.92 (cap $15).

## Quality (limits stated)

Two checks, both blind to the arm label.

1. Scripted coverage (as in the invalid run): share of PR/issue numbers cited in the published notes that the generated notes also cite. direct-ts 0.850, gateway 0.830 (diff -0.020, CI -0.110 to +0.042). Unmatched references (cited by the notes, absent from the published notes and from the commit subjects): 65 direct-ts, 77 gateway in total; an upper bound on wrong references, since agents also read PR numbers through gh. Mean notes size 3,797 B direct-ts, 3,481 B gateway.
2. Blind model judge (`release-judge.yml`, run 41202597359, 24 jobs, one per pair, direct API with no gateway). The judge reads the published notes, the commit subjects and two candidates labelled A and B (order randomized, seed 7; the key is not in the repo), then gives coverage (0 to 1), false claims, and a usefulness score 1 to 10.

| arm | judge coverage | false claims per notes | usefulness score |
|---|---|---|---|
| direct-ts | 0.861 | 2.08 | 6.67 |
| gateway | 0.859 | 2.08 | 6.42 |

Differences (gateway minus direct-ts, task-resampled CI): score -0.25 (-0.54 to 0.00), coverage -0.002 (-0.017 to +0.014), false claims 0.00 (-0.46 to +0.54). Winner counts: direct-ts 8, gateway 3, tie 13. The judge is Sonnet 5.5, the model that wrote the notes, so this is a model judge, not a human check.

## Anatomy (2 tasks, round 1, per request)

Tokens per API request. "cache_write" is new content written to cache, "cache_read" is the prefix and history read back.

```
## anatomy rg-152 round 1
direct-ts run 41201260722 cost 0.1193 requests 9
 req | uncached | cache_write | cache_read | tools
 1 | 2 | 4168 | 14547 | Bash
 2 | 2 | 3539 | 18715 | Bash
 3 | 2 | 1856 | 22254 | Bash
 4 | 2 | 3799 | 24110 | Bash
 5 | 2 | 2868 | 27909 | Bash
 6 | 2 | 362 | 30777 | Bash
 7 | 2 | 1536 | 31139 | Bash
 8 | 2 | 759 | 32675 | Write
 9 | 2 | 1943 | 33434 | 
gateway run 41201268625 cost 0.1017 requests 11
 req | uncached | cache_write | cache_read | tools
 1 | 498 | 927 | 9495 | Bash
 2 | 4 | 4050 | 10422 | Bash
 3 | 4 | 4142 | 14472 | Bash
 4 | 4 | 428 | 18614 | Bash
 5 | 4 | 620 | 19042 | Bash
 6 | 4 | 337 | 19662 | Bash
 7 | 4 | 533 | 19999 | Bash
 8 | 4 | 682 | 20532 | Bash
 9 | 4 | 1156 | 21214 | Bash
 10 | 4 | 372 | 22370 | Write
 11 | 4 | 1723 | 22742 | 
## anatomy mcp-21 round 1
direct-ts run 41200984345 cost 0.1682 requests 8
 req | uncached | cache_write | cache_read | tools
 1 | 2 | 23935 | 14547 | Bash
 2 | 2 | 2960 | 38482 | Bash
 3 | 2 | 243 | 41442 | Bash
 4 | 2 | 471 | 41685 | Bash
 5 | 2 | 8748 | 42156 | Bash
 6 | 2 | 340 | 50904 | Bash
 7 | 2 | 571 | 51244 | Write
 8 | 2 | 1976 | 51815 | 
gateway run 41201073748 cost 0.1717 requests 8
 req | uncached | cache_write | cache_read | tools
 1 | 1252 | 25535 | 3914 | Bash
 2 | 4 | 2690 | 29449 | Bash
 3 | 4 | 1577 | 32139 | Bash
 4 | 4 | 5413 | 33716 | Bash
 5 | 4 | 391 | 39129 | Bash
 6 | 4 | 1105 | 39520 | Bash
 7 | 4 | 4969 | 40625 | Write
 8 | 4 | 1807 | 45594 | 
```

Where the gateway saves: the fixed prefix. Request 1 is 31% smaller (17,150 vs 24,943 tokens on average), and every later request reads that prefix from cache, so cache reads fall from 211k to 146k per run. It does not shrink new tool results (git log, diffs, PR bodies): those writes are the same on both arms. Run-to-run turn counts vary a lot (rg-152 and mcp-21 above), which is why the CI is resampled by task.

## Per pair

Cells are cost / API requests / scripted coverage.

| task | round | direct-ts | gateway | direct-ts run | gateway run |
|---|---|---|---|---|---|
| gemini-65 | r1 | $0.0765 / 7 / 0.87 | $0.0477 / 5 / 0.87 | [41200852661](https://github.com/mksglu/cm-ci-lab/actions/runs/41200852661) | [41200861188](https://github.com/mksglu/cm-ci-lab/actions/runs/41200861188) |
| gemini-65 | r2 | $0.0597 / 6 / 0.87 | $0.0687 / 6 / 0.90 | [41201729576](https://github.com/mksglu/cm-ci-lab/actions/runs/41201729576) | [41201737804](https://github.com/mksglu/cm-ci-lab/actions/runs/41201737804) |
| gemini-66 | r1 | $0.0583 / 5 / 0.96 | $0.0602 / 6 / 0.96 | [41200836862](https://github.com/mksglu/cm-ci-lab/actions/runs/41200836862) | [41200844867](https://github.com/mksglu/cm-ci-lab/actions/runs/41200844867) |
| gemini-66 | r2 | $0.0780 / 6 / 0.88 | $0.0525 / 6 / 0.96 | [41201713100](https://github.com/mksglu/cm-ci-lab/actions/runs/41201713100) | [41201721186](https://github.com/mksglu/cm-ci-lab/actions/runs/41201721186) |
| mcp-21 | r1 | $0.1682 / 8 / 0.90 | $0.1717 / 8 / 0.67 | [41200984345](https://github.com/mksglu/cm-ci-lab/actions/runs/41200984345) | [41201073748](https://github.com/mksglu/cm-ci-lab/actions/runs/41201073748) |
| mcp-21 | r2 | $0.2116 / 11 / 0.95 | $0.1752 / 10 / 0.29 | [41201865189](https://github.com/mksglu/cm-ci-lab/actions/runs/41201865189) | [41201898274](https://github.com/mksglu/cm-ci-lab/actions/runs/41201898274) |
| mcp-22 | r1 | $0.1974 / 7 / 0.52 | $0.1742 / 7 / 0.55 | [41201082968](https://github.com/mksglu/cm-ci-lab/actions/runs/41201082968) | [41201118903](https://github.com/mksglu/cm-ci-lab/actions/runs/41201118903) |
| mcp-22 | r2 | $0.1929 / 8 / 0.58 | $0.2375 / 12 / 0.58 | [41201906669](https://github.com/mksglu/cm-ci-lab/actions/runs/41201906669) | [41201915770](https://github.com/mksglu/cm-ci-lab/actions/runs/41201915770) |
| rg-141 | r1 | $0.0844 / 6 / 1.00 | $0.0707 / 5 / 1.00 | [41201276415](https://github.com/mksglu/cm-ci-lab/actions/runs/41201276415) | [41201284429](https://github.com/mksglu/cm-ci-lab/actions/runs/41201284429) |
| rg-141 | r2 | $0.0712 / 6 / 1.00 | $0.0761 / 6 / 1.00 | [41201991783](https://github.com/mksglu/cm-ci-lab/actions/runs/41201991783) | [41201999686](https://github.com/mksglu/cm-ci-lab/actions/runs/41201999686) |
| rg-152 | r1 | $0.1193 / 9 / 0.67 | $0.1017 / 11 / 0.33 | [41201260722](https://github.com/mksglu/cm-ci-lab/actions/runs/41201260722) | [41201268625](https://github.com/mksglu/cm-ci-lab/actions/runs/41201268625) |
| rg-152 | r2 | $0.1356 / 11 / 0.33 | $0.0946 / 7 / 1.00 | [41201950454](https://github.com/mksglu/cm-ci-lab/actions/runs/41201950454) | [41201983481](https://github.com/mksglu/cm-ci-lab/actions/runs/41201983481) |
| ruff-171 | r1 | $0.1426 / 8 / 1.00 | $0.0919 / 8 / 1.00 | [41201671319](https://github.com/mksglu/cm-ci-lab/actions/runs/41201671319) | [41201705248](https://github.com/mksglu/cm-ci-lab/actions/runs/41201705248) |
| ruff-171 | r2 | $0.1477 / 10 / 1.00 | $0.0920 / 6 / 1.00 | [41202128838](https://github.com/mksglu/cm-ci-lab/actions/runs/41202128838) | [41202165337](https://github.com/mksglu/cm-ci-lab/actions/runs/41202165337) |
| ruff-173 | r1 | $0.1153 / 7 / 1.00 | $0.0993 / 7 / 1.00 | [41201571418](https://github.com/mksglu/cm-ci-lab/actions/runs/41201571418) | [41201663007](https://github.com/mksglu/cm-ci-lab/actions/runs/41201663007) |
| ruff-173 | r2 | $0.1199 / 7 / 1.00 | $0.1123 / 7 / 1.00 | [41202087264](https://github.com/mksglu/cm-ci-lab/actions/runs/41202087264) | [41202094810](https://github.com/mksglu/cm-ci-lab/actions/runs/41202094810) |
| uv-1222 | r1 | $0.0996 / 8 / 1.00 | $0.0870 / 9 / 0.94 | [41200886948](https://github.com/mksglu/cm-ci-lab/actions/runs/41200886948) | [41200894758](https://github.com/mksglu/cm-ci-lab/actions/runs/41200894758) |
| uv-1222 | r2 | $0.1005 / 9 / 1.00 | $0.0773 / 7 / 0.94 | [41201849249](https://github.com/mksglu/cm-ci-lab/actions/runs/41201849249) | [41201857352](https://github.com/mksglu/cm-ci-lab/actions/runs/41201857352) |
| uv-135 | r1 | $0.1152 / 10 / 0.93 | $0.0971 / 9 / 1.00 | [41200869723](https://github.com/mksglu/cm-ci-lab/actions/runs/41200869723) | [41200878128](https://github.com/mksglu/cm-ci-lab/actions/runs/41200878128) |
| uv-135 | r2 | $0.1231 / 10 / 1.00 | $0.1071 / 11 / 1.00 | [41201831648](https://github.com/mksglu/cm-ci-lab/actions/runs/41201831648) | [41201841017](https://github.com/mksglu/cm-ci-lab/actions/runs/41201841017) |
| zod-465 | r1 | $0.0632 / 5 / 0.67 | $0.0582 / 5 / 0.67 | [41201357040](https://github.com/mksglu/cm-ci-lab/actions/runs/41201357040) | [41201563423](https://github.com/mksglu/cm-ci-lab/actions/runs/41201563423) |
| zod-465 | r2 | $0.0592 / 4 / 0.67 | $0.0502 / 4 / 0.67 | [41202071709](https://github.com/mksglu/cm-ci-lab/actions/runs/41202071709) | [41202080084](https://github.com/mksglu/cm-ci-lab/actions/runs/41202080084) |
| zod-466 | r1 | $0.0623 / 4 / 0.80 | $0.0611 / 3 / 0.80 | [41201292049](https://github.com/mksglu/cm-ci-lab/actions/runs/41201292049) | [41201299747](https://github.com/mksglu/cm-ci-lab/actions/runs/41201299747) |
| zod-466 | r2 | $0.0658 / 4 / 0.80 | $0.0607 / 3 / 0.80 | [41202007354](https://github.com/mksglu/cm-ci-lab/actions/runs/41202007354) | [41202038460](https://github.com/mksglu/cm-ci-lab/actions/runs/41202038460) |

## Caveats

- One model (Sonnet 5.5), 12 tasks, 2 rounds, arms run in fixed order within a pair (direct-ts first), not randomized.
- Quality: point estimates for the gateway are slightly lower on both the judge score and scripted coverage. More rounds and a human check of the non-tie pairs are needed before any claim of equal quality.
- The fee used is the flat $0.0009 per request. The net saving is +$0.0080 per run at that fee.
