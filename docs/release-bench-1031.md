# Release notes and changelog benchmark (2026-10-31)

Area: release notes. Claude Code headless (`claude -p`, native installer), Sonnet 5.5, arms `direct-ts` (direct API + ENABLE_TOOL_SEARCH) and `gateway`. Workflow `.github/workflows/release.yml`, files under `lab/release/`. Tags `a1031-release-sonnet-r1`, `-r2`. Nothing here is published.

## Result vs the pass bar (fixed in advance): NOT MET

| bar | result |
|---|---|
| task-resampled CI upper bound < 0 | NO. Cost change -6.2%, CI -13.2% to +1.6% (24 pairs, 12 tasks, 10,000 resamples, seed 1). Cheaper in 13 of 24 pairs. |
| quality not lower than direct-ts | yes on the proxy below (coverage 0.901 vs 0.874; diff +0.027, CI 0.000 to +0.072). Not a full judge, see Quality. |
| 0 errors | yes, 0 of 48 (no is_error, no zero cost, no "Credit balance is too low", every run wrote notes) |
| net saving per run > 0 | NO. (0.1179 - 0.1127) - 0.0009 x 9.12 = -$0.0030 per run. |

Round 1 alone: -9.1%. Round 2 alone: -3.3%. The saving shrinks and the CI crosses zero. On this area the gateway does not save money that we can sell.

## Numbers

| arm | errors | mean turns | mean cost | uncached | cache_write | cache_read | output |
|---|---|---|---|---|---|---|---|
| direct-ts | 0 | 9.12 | $0.1179 | 16 | 21,710 | 240,687 | 3,951 |
| gateway | 0 | 9.12 | $0.1127 | 16 | 21,367 | 230,731 | 3,619 |

Cost per API request: $0.0146 direct-ts, $0.0144 gateway (194 and 188 requests). Turn difference gateway minus direct-ts: mean 0.00, task-resampled CI -1.75 to +1.67. The fee ($0.0009 x 9.12 = $0.0082 per run) is larger than the gross saving ($0.0052 per run).

Per task (mean of 2 rounds, gateway vs direct-ts cost): gemini-65 -17%, gemini-66 +16%, mcp-21 +12%, mcp-22 -6%, rg-141 +1%, rg-152 -14%, ruff-171 +6%, ruff-173 +11%, uv-1222 -10%, uv-135 -24%, zod-465 -20%, zod-466 -17%. Six tasks cheaper, six dearer or equal by mean; the sign follows how many turns the agent happened to take.

## Method

- Template mirrored: CherryHQ/cherry-studio `prepare-release.yml` (53k stars, claude-code-action, the most-starred Claude release-notes workflow in the census): notes from the final user-visible differences between the previous tag and the release, not one entry per commit; tools `Bash(git:*)`, Read, Write, Glob, Grep. PR titles through `gh`, as NVIDIA/OpenShell `release-notes.yml` does. The prompt text is ours; the action is not used (its entrypoint is rejected for this key).
- Tasks (12 real releases, 2 from each of 6 repos): google-gemini/gemini-cli v0.66.0, v0.65.0; astral-sh/uv 0.13.5, 0.12.22; modelcontextprotocol/servers v2.1.0, v2.2.0 (the run list uses mcp-21 and mcp-22); BurntSushi/ripgrep 15.2.0, 14.1.1; colinhacks/zod v4.6.6, v4.6.5; astral-sh/ruff 0.17.3, 0.17.1. Defined in `lab/release/tasks.sh`. Commits in prev..tag: 8 to 124.
- Repo state (`lab/release/prep.sh`): only the new tag and the previous tag are fetched (full history, no later commits, no later tags); the remote is removed; every changelog / release-notes file is pinned to its previous-tag content in each commit of prev..tag, so `git log -p`, `git diff` and `git show` cannot show the published notes (checked: 0 lines for gemini-66).
- gh is a read-only shim (`lab/release/gh`): pr/issue view, list, diff and GET api calls only. Releases, contents, tags, refs, graphql, search/code and all writes are blocked (tested). In the smoke runs the shim blocked nothing, so no agent tried to read the answer.
- Notes are written to a file and uploaded as an artifact; nothing is posted or pushed.
- Stats: pairs by (task, round); cost = mean paired log-ratio gateway/direct-ts, shown as exp(mean)-1; 95% CI by bootstrap resampling tasks (rounds stay together), 10,000 resamples, seed 1. Per-message usage is in each artifact (`usage.json`, from `--output-format stream-json --verbose`), totals in `lab-metrics.json`.
- Spend: $5.53 for 48 runs (cap $15), plus a smoke pair of about $0.23 (runs 41193569590, 41193571630).

## Quality (limits stated)

Blind by construction, but a proxy, not a model or human judge: the scoring script sees only the notes text and the published notes of that tag, never the arm label. Measures:

- Coverage: share of PR/issue numbers cited in the published notes that the generated notes also cite. direct-ts 0.874, gateway 0.901 (diff +0.027, task-resampled CI 0.000 to +0.072).
- Unmatched references: numbers cited by the generated notes that appear in neither the published notes nor the commit subjects of prev..tag. direct-ts 72, gateway 84 in total (diff per run +0.50, CI -0.67 to +2.29). Some are PR numbers the agent read through gh from PR bodies, so this is an upper bound on wrong references, not a count of wrong claims.
- Not measured: wrong claims in the prose, and a read-through of coverage of user-facing changes. A blind model judge over these 48 notes is still to do before any quality claim is made in public.
- Mean notes size: 3,851 B direct-ts, 3,766 B gateway.

## Anatomy (2 tasks, round 1, per request)

Columns are tokens per API request. "cache_write" is new content written to cache, "cache_read" is the prefix and history read back.

```
## anatomy rg-152 round 1
direct-ts run 41193952714 cost 0.1486 requests 10
 req | uncached | cache_write | cache_read | output | tools
 1 | 2 | 4168 | 14547 | 16 | Bash
 2 | 2 | 3539 | 18715 | 3 | Bash
 3 | 2 | 5805 | 22254 | 9 | Bash
 4 | 2 | 1963 | 28059 | 2 | Bash
 5 | 2 | 452 | 30022 | 16 | Bash
 6 | 2 | 3761 | 30474 | 4 | Bash
 7 | 2 | 308 | 34235 | 16 | Bash
 8 | 2 | 751 | 34543 | 4 | Bash
 9 | 2 | 1987 | 35294 | 32 | Write
 10 | 2 | 1792 | 37281 | 446 | 
gateway run 41193959703 cost 0.0966 requests 8
 req | uncached | cache_write | cache_read | output | tools
 1 | 2 | 4168 | 14413 | 16 | Bash
 2 | 2 | 5033 | 18581 | 43 | Bash
 3 | 2 | 1910 | 23614 | 3 | Bash
 4 | 2 | 477 | 25524 | 16 | Bash
 5 | 2 | 708 | 26001 | 8 | Bash
 6 | 2 | 1102 | 26709 | 6 | Bash
 7 | 2 | 785 | 27811 | 16 | Write
 8 | 2 | 2131 | 28596 | 369 | 
## anatomy mcp-21 round 1
direct-ts run 41193879717 cost 0.1668 requests 7
 req | uncached | cache_write | cache_read | output | tools
 1 | 2 | 23935 | 14547 | 16 | Bash
 2 | 2 | 3077 | 38482 | 16 | Bash
 3 | 2 | 289 | 41559 | 16 | Bash
 4 | 2 | 2103 | 41848 | 8 | Bash
 5 | 2 | 4074 | 43951 | 5 | Bash
 6 | 2 | 1838 | 48025 | 51 | Write
 7 | 2 | 1677 | 49863 | 497 | 
gateway run 41193933042 cost 0.2294 requests 14
 req | uncached | cache_write | cache_read | output | tools
 1 | 2 | 23935 | 14413 | 16 | Bash
 2 | 2 | 2058 | 38348 | 9 | Bash
 3 | 2 | 4735 | 40406 | 39 | Bash
 4 | 2 | 297 | 45141 | 16 | Bash
 5 | 2 | 270 | 45438 | 16 | Bash
 6 | 2 | 1390 | 45708 | 7 | Bash
 7 | 2 | 236 | 47098 | 16 | Bash
 8 | 2 | 1208 | 47334 | 8 | Write
 9 | 2 | 1959 | 48542 | 3 | Bash
 10 | 2 | 285 | 50501 | 16 | Bash
 11 | 2 | 919 | 50786 | 4 | Bash
 12 | 2 | 510 | 51705 | 3 | Bash
 13 | 2 | 1209 | 52215 | 3 | Edit
 14 | 2 | 1414 | 53424 | 568 | 
```

Where the gateway saves and where it does not:

- Request 1 (the fixed prefix: system and tools) is the same size on both arms: mean 24,943 tokens direct-ts vs 24,809 gateway across all 48 runs, a gap of 134 tokens. Both arms already run with ENABLE_TOOL_SEARCH, which removes most of the tool bytes before the gateway sees them. The prefix gap is only 134 tokens, so the prefix saving that the earlier areas relied on is not present here. I did not test why; ENABLE_TOOL_SEARCH on both arms is my hypothesis, not a measured cause.
- Per-turn cache writes (new tool results: git log, diffs, PR bodies) are about the same on both arms (4,168 on request 1 on both; later writes differ by task, not by arm).
- rg-152: the gateway run was cheaper ($0.0966 vs $0.1486) because it needed 8 requests instead of 10 and its history stayed smaller (last request reads 28.6k vs 37.3k). That is fewer turns, and the turn counts do not differ systematically across the 12 tasks (CI -1.75 to +1.67). I did not trace why this agent took fewer turns.
- mcp-21: the gateway run was dearer ($0.2294 vs $0.1668) because it took 14 requests instead of 7. Same cause in the other direction.
- Output tokens are 8% lower on the gateway (3,619 vs 3,951); this is part of the small gross saving and I did not test whether it is real or noise.

## Per pair

Cells are cost / turns / coverage.

| task | round | direct-ts | gateway | direct-ts run | gateway run |
|---|---|---|---|---|---|
| gemini-65 | r1 | $0.0673 / 7 / 0.87 | $0.0728 / 8 / 0.87 | [41193790580](https://github.com/mksglu/cm-ci-lab/actions/runs/41193790580) | [41193797021](https://github.com/mksglu/cm-ci-lab/actions/runs/41193797021) |
| gemini-65 | r2 | $0.0928 / 7 / 0.87 | $0.0602 / 5 / 0.90 | [41194315595](https://github.com/mksglu/cm-ci-lab/actions/runs/41194315595) | [41194322731](https://github.com/mksglu/cm-ci-lab/actions/runs/41194322731) |
| gemini-66 | r1 | $0.0536 / 5 / 0.96 | $0.0682 / 7 / 0.96 | [41193777176](https://github.com/mksglu/cm-ci-lab/actions/runs/41193777176) | [41193784308](https://github.com/mksglu/cm-ci-lab/actions/runs/41193784308) |
| gemini-66 | r2 | $0.0812 / 6 / 0.96 | $0.0876 / 8 / 0.96 | [41194300995](https://github.com/mksglu/cm-ci-lab/actions/runs/41194300995) | [41194308056](https://github.com/mksglu/cm-ci-lab/actions/runs/41194308056) |
| mcp-21 | r1 | $0.1668 / 7 / 0.95 | $0.2294 / 17 / 0.90 | [41193879717](https://github.com/mksglu/cm-ci-lab/actions/runs/41193879717) | [41193933042](https://github.com/mksglu/cm-ci-lab/actions/runs/41193933042) |
| mcp-21 | r2 | $0.1962 / 11 / 0.90 | $0.1755 / 12 / 0.95 | [41194384412](https://github.com/mksglu/cm-ci-lab/actions/runs/41194384412) | [41194393514](https://github.com/mksglu/cm-ci-lab/actions/runs/41194393514) |
| mcp-22 | r1 | $0.1862 / 12 / 0.56 | $0.2212 / 10 / 0.60 | [41193939370](https://github.com/mksglu/cm-ci-lab/actions/runs/41193939370) | [41193945586](https://github.com/mksglu/cm-ci-lab/actions/runs/41193945586) |
| mcp-22 | r2 | $0.2523 / 17 / 0.58 | $0.1915 / 10 / 0.55 | [41194402516](https://github.com/mksglu/cm-ci-lab/actions/runs/41194402516) | [41194410354](https://github.com/mksglu/cm-ci-lab/actions/runs/41194410354) |
| rg-141 | r1 | $0.0782 / 7 / 1.00 | $0.0677 / 6 / 1.00 | [41193990490](https://github.com/mksglu/cm-ci-lab/actions/runs/41193990490) | [41193996809](https://github.com/mksglu/cm-ci-lab/actions/runs/41193996809) |
| rg-141 | r2 | $0.0629 / 5 / 1.00 | $0.0750 / 7 / 1.00 | [41194457084](https://github.com/mksglu/cm-ci-lab/actions/runs/41194457084) | [41194464716](https://github.com/mksglu/cm-ci-lab/actions/runs/41194464716) |
| rg-152 | r1 | $0.1486 / 11 / 0.67 | $0.0966 / 8 / 1.00 | [41193952714](https://github.com/mksglu/cm-ci-lab/actions/runs/41193952714) | [41193959703](https://github.com/mksglu/cm-ci-lab/actions/runs/41193959703) |
| rg-152 | r2 | $0.1093 / 7 / 0.83 | $0.1243 / 12 / 1.00 | [41194442660](https://github.com/mksglu/cm-ci-lab/actions/runs/41194442660) | [41194450005](https://github.com/mksglu/cm-ci-lab/actions/runs/41194450005) |
| ruff-171 | r1 | $0.1288 / 9 / 1.00 | $0.1486 / 12 / 1.00 | [41194098204](https://github.com/mksglu/cm-ci-lab/actions/runs/41194098204) | [41194105288](https://github.com/mksglu/cm-ci-lab/actions/runs/41194105288) |
| ruff-171 | r2 | $0.1464 / 11 / 1.00 | $0.1425 / 13 / 1.00 | [41194542718](https://github.com/mksglu/cm-ci-lab/actions/runs/41194542718) | [41194550752](https://github.com/mksglu/cm-ci-lab/actions/runs/41194550752) |
| ruff-173 | r1 | $0.1469 / 8 / 1.00 | $0.1106 / 8 / 1.00 | [41194083849](https://github.com/mksglu/cm-ci-lab/actions/runs/41194083849) | [41194091420](https://github.com/mksglu/cm-ci-lab/actions/runs/41194091420) |
| ruff-173 | r2 | $0.1091 / 7 / 1.00 | $0.1725 / 13 / 1.00 | [41194528469](https://github.com/mksglu/cm-ci-lab/actions/runs/41194528469) | [41194535468](https://github.com/mksglu/cm-ci-lab/actions/runs/41194535468) |
| uv-1222 | r1 | $0.1253 / 12 / 0.94 | $0.0858 / 14 / 1.00 | [41193818346](https://github.com/mksglu/cm-ci-lab/actions/runs/41193818346) | [41193826860](https://github.com/mksglu/cm-ci-lab/actions/runs/41193826860) |
| uv-1222 | r2 | $0.1323 / 17 / 0.94 | $0.1457 / 15 / 1.00 | [41194343926](https://github.com/mksglu/cm-ci-lab/actions/runs/41194343926) | [41194351917](https://github.com/mksglu/cm-ci-lab/actions/runs/41194351917) |
| uv-135 | r1 | $0.1140 / 14 / 1.00 | $0.1085 / 11 / 1.00 | [41193803774](https://github.com/mksglu/cm-ci-lab/actions/runs/41193803774) | [41193810645](https://github.com/mksglu/cm-ci-lab/actions/runs/41193810645) |
| uv-135 | r2 | $0.1469 / 18 / 1.00 | $0.0889 / 9 / 1.00 | [41194329773](https://github.com/mksglu/cm-ci-lab/actions/runs/41194329773) | [41194336373](https://github.com/mksglu/cm-ci-lab/actions/runs/41194336373) |
| zod-465 | r1 | $0.0818 / 7 / 0.67 | $0.0521 / 3 / 0.67 | [41194068958](https://github.com/mksglu/cm-ci-lab/actions/runs/41194068958) | [41194076094](https://github.com/mksglu/cm-ci-lab/actions/runs/41194076094) |
| zod-465 | r2 | $0.0679 / 6 / 0.67 | $0.0677 / 5 / 0.67 | [41194512827](https://github.com/mksglu/cm-ci-lab/actions/runs/41194512827) | [41194520860](https://github.com/mksglu/cm-ci-lab/actions/runs/41194520860) |
| zod-466 | r1 | $0.0779 / 5 / 0.80 | $0.0545 / 3 / 0.80 | [41194003010](https://github.com/mksglu/cm-ci-lab/actions/runs/41194003010) | [41194062097](https://github.com/mksglu/cm-ci-lab/actions/runs/41194062097) |
| zod-466 | r2 | $0.0564 / 3 / 0.80 | $0.0575 / 3 / 0.80 | [41194472590](https://github.com/mksglu/cm-ci-lab/actions/runs/41194472590) | [41194504869](https://github.com/mksglu/cm-ci-lab/actions/runs/41194504869) |

## Caveats

- This area does not clear the bar and should not be sold as a saving. The honest statement is: no measurable saving in release notes on Sonnet, net negative after the fee.
- Release-notes runs are short (9 turns) and dominated by one big first read of git log and diff. The prefix is the only lever the gateway has and it has little left here.
- One model (Sonnet 5.5), 12 tasks, 2 rounds. A larger run could move the CI, but the point estimate is below the $0.0082 fee per run.
