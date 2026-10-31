# Mention assistant / issue-to-PR benchmark (2026-10-31)

Area: a maintainer writes "@claude <request>" on an issue and the agent implements it (claude.yml, in 8,224 workflow files). Headless `claude -p` (native installer), arms `direct-ts` (direct API + ENABLE_TOOL_SEARCH) and `gateway`. Workflow `.github/workflows/mention.yml`. Nothing here is published.

## Result vs the pass bar (fixed in advance): NOT MET

| bar | Sonnet (24 pairs, 12 tasks) | Opus (12 pairs, 12 tasks) |
|---|---|---|
| task-resampled CI upper bound < 0 | NO: +8.4%, CI +2.6 to +14.9 (gateway costs MORE) | NO: +5.0%, CI -6.1 to +17.8 |
| quality not lower than direct-ts | yes, 16/24 vs 16/24 | yes, 8/12 vs 7/12 |
| 0 errors | yes | yes |
| net per run > 0 | NO, -$0.0184 | NO, -$0.0210 |

In this area the gateway did not save money. It cost more per task on both models. The Sonnet CI lies entirely above zero.

## Method

- Template: the real `anthropics/claude-code-action` tag-mode prompt (src/create-prompt/index.ts, generateDefaultPrompt, issue event), same context tags, steps and notes. Tool list: Read, Write, Edit, Bash, Glob, Grep, LS (the action's base tools plus edit tools, as in popular claude.yml files: remotion, twenty, storybook). `--permission-mode acceptEdits`. Forced changes: no GitHub comment tool exists in `claude -p`, so the reply is the final message; the push is printed (`out/push.txt`), never run.
- Request: the real linked issue title and body, with "@claude " in front. 12 tasks, each a merged PR of a repo with 20k+ stars that closes a linked issue: flask #6096 (issue 6093), cobra #2356 (2257), ripgrep #3182 (3180), rich #3180 (3176), chalk #688 (624), gin #4852 (4851), fd #2193 (2192), plus 5 replacements for triage tasks that had no linked issue: dayjs #3180 (3178), tqdm #1830 (1828), testify #1888 (1800), loguru #1508 (1501), chi #1029 (996). Replaced: requests, express, koa, black, axios (no closing issue).
- Snapshot (`lab/mention/task.sh`): the parent of the merge commit as one commit with no history. The PR's test files are held back in a hidden folder and copied in at check time. The upstream clone is deleted from the runner.
- Check: the PR's own tests (hidden test files copied over) must pass.
- Validity: every task fails with the hidden tests and passes with the upstream source fix, no model call. Baseline runs (all fail): flask 41193221211, cobra 41193228967, ripgrep 41193236035, rich 41193242695, chalk 41193250990, gin 41193260419, fd 41193268479, dayjs 41193276371, tqdm 41193284666, testify 41193292551, loguru 41193300610, chi 41193308020. Control runs (all pass): flask 41193224809, cobra 41193232531, ripgrep 41193239424, rich 41193246713, chalk 41193256360, gin 41193264741, fd 41193272133, dayjs 41193280571, tqdm 41193288762, testify 41193296486, loguru 41193304374, chi 41193311780.
- Stats: pairs by (task, round). Cost = mean paired log-ratio gateway/direct-ts, % = exp(mean)-1. 95% CI: bootstrap over tasks (all rounds of a task together), 10,000 resamples, seed 1 (`lab/mention/stats.py`). Fee $0.0009 per request. Dispatch 8 at a time. Tags a1031-mention-sonnet-r1, -sonnet-r2, -opus-r1. Spend: Sonnet $3.771, Opus $5.013, total $8.78 (cap $15).

## Numbers

Sonnet (r1 + r2):
```
pairs 24 tasks 12 errors 0
cost change +8.4%  task-resampled 95% CI +2.6..+14.9  cheaper 6/24
direct-ts: pass 16/24 mean cost $0.0741 turns 8.96 uncached 16 cache_write 11472 cache_read 182020 output 2721
gateway: pass 16/24 mean cost $0.0830 turns 10.58 uncached 18 cache_write 12386 cache_read 216801 output 3034
net per run = (0.0741-0.0830) - 0.0009x10.58 = $-0.0184
McNemar exact: direct-only 0 gateway-only 0 p=1.000
spend $3.771
```
Sonnet round 1 alone: +7.0%, CI -1.4 to +18.3, cheaper 4/12.

Opus (r1):
```
pairs 12 tasks 12 errors 0
cost change +5.0%  task-resampled 95% CI -6.1..+17.8  cheaper 4/12
direct-ts: pass 7/12 mean cost $0.2038 turns 11.33 uncached 20 cache_write 14401 cache_read 242343 output 4162
gateway: pass 8/12 mean cost $0.2140 turns 12.00 uncached 21 cache_write 15555 cache_read 250962 output 4295
net per run = (0.2038-0.2140) - 0.0009x12.00 = $-0.0210
McNemar exact: direct-only 0 gateway-only 1 p=1.000
spend $5.013
```

## Quality

- Pass rate: Sonnet 16/24 vs 16/24 (McNemar exact p=1.000, 0 and 0 discordant). Opus 7/12 vs 8/12 (p=1.000; the one discordant pair is flask: the direct-ts run read the issue as a question and made no patch, the gateway run fixed it).
- Four tasks fail on both arms in every round: chalk, fd, loguru, tqdm. Both arms fail the same way each round, so this is not an arm effect. I did not investigate why they fail (not measured). They count in the pass rates and in the cost pairs.
- Blind patch check (labels hidden, arm order shuffled with seed 7, key kept outside the judge folder): all 19 pairs where both arms passed but the source patches differ were read. All 38 patches are real fixes of the issue's root cause, no test hack and no special-casing. Differences are style only (for example chi: helper in `tree.go` vs a method on `Context`; flask: `urlsplit` vs manual bracket parsing). 4 pairs have identical source patches.
- Test-file scan of all 72 patches: 62 add or edit tests (the agents write their own tests, as the prompt asks). Those edits are overwritten when the PR's tests are copied in. No passing patch lacks a source change.

## Anatomy (Sonnet r1, per request, tokens)

gin, direct-ts (run 41193767025), cost $0.0603, 8 requests:
```
req  uncached  cache_write  cache_read  output
0    2         5140         14547       7
1    2         992          19687       16
2    2         392          20679       16
3    2         230          21071       35
4    2         561          21301       3
5    2         706          21862       16
6    2         344          22568       8
7    2         262          22912       583
```
gin, gateway (run 41193770589), cost $0.0626, 7 requests:
```
0    2         5139         14413       7
1    2         1083         19552       16
2    2         1611         20635       33
3    2         893          22246       16
4    2         344          23139       34
5    2         419          23483       5
6    2         376          23902       430
```
flask: direct-ts (41193609605) 7 requests, cache_write 9,640, cache_read 146,674, $0.0627. Gateway (41193613063) 6 requests, cache_write 9,475, cache_read 123,446, $0.0606.

All 72 runs, means per request, direct-ts vs gateway: first request cache_write 5,633 vs 5,992, cache_read 14,522 vs 14,029; later requests cache_write 894 vs 878, cache_read 23,902 vs 24,176; requests per run 8.61 vs 9.44; cost per turn $0.0115 vs $0.0112.

Where the gateway saves and where it does not:
- It does not shrink the first request here. With ENABLE_TOOL_SEARCH the client already defers most tool schemas, so the first request holds about 20k tokens in both arms (cache write plus cache read: 20,155 vs 20,021). The prefix cut seen in the triage cause check (tools 71.5 KB to 27.5 KB) does not show up here. I did not capture a mention request, so I cannot say why.
- Per-turn writes are new tool results (file reads, test output) with the same size in both arms: 894 vs 878 tokens.
- The only gap is cost per turn, -2.6%. It is smaller than the extra requests: the gateway used 0.83 more requests per run (+9.6%). More requests re-read the whole cache each time, and cache reads are the biggest line. The fee ($0.0009 x 10.6 = $0.0095 per Sonnet run) comes on top.
- So in this area the gateway saves nothing on the prefix, the per-turn cost gap is too small to pay for extra turns, and extra turns appear more often with the gateway (not explained; turn counts per pair over all 36 pairs: gateway higher in 23, lower in 6, equal in 7).

## Caveats

- Per-run noise is large (flask Sonnet 7 vs 8 requests with the same patch). The CI covers this for cost, not for the turn mechanism.
- `claude -p` mirrors the action's prompt and tools. It is not the action itself (Anthropic rejects that entrypoint for this key; no entrypoint spoofing).
- 4 of 12 tasks fail on both arms in every round, which lowers pass rates and gives no quality signal on those tasks.
- Opus has one round only, so its CI is wide (-6.1 to +17.8); it does not show a saving or a loss.

## Per pair (cost / turns / pass)

| task | round | direct-ts | gateway | direct-ts run | gateway run |
|---|---|---|---|---|---|
| chalk | sonnet-r1 | $0.0615 / 8 / False | $0.0574 / 7 / False | [41193760608](https://github.com/mksglu/cm-ci-lab/actions/runs/41193760608) | [41193763987](https://github.com/mksglu/cm-ci-lab/actions/runs/41193763987) |
| chi | sonnet-r1 | $0.0666 / 9 / True | $0.0578 / 7 / True | [41194113210](https://github.com/mksglu/cm-ci-lab/actions/runs/41194113210) | [41194116508](https://github.com/mksglu/cm-ci-lab/actions/runs/41194116508) |
| cobra | sonnet-r1 | $0.0637 / 9 / True | $0.0779 / 10 / True | [41193616587](https://github.com/mksglu/cm-ci-lab/actions/runs/41193616587) | [41193619825](https://github.com/mksglu/cm-ci-lab/actions/runs/41193619825) |
| dayjs | sonnet-r1 | $0.0607 / 8 / True | $0.0640 / 8 / True | [41193780308](https://github.com/mksglu/cm-ci-lab/actions/runs/41193780308) | [41193784275](https://github.com/mksglu/cm-ci-lab/actions/runs/41193784275) |
| fd | sonnet-r1 | $0.1975 / 22 / False | $0.2155 / 25 / False | [41193773947](https://github.com/mksglu/cm-ci-lab/actions/runs/41193773947) | [41193777164](https://github.com/mksglu/cm-ci-lab/actions/runs/41193777164) |
| flask | sonnet-r1 | $0.0627 / 7 / True | $0.0606 / 8 / True | [41193609605](https://github.com/mksglu/cm-ci-lab/actions/runs/41193609605) | [41193613063](https://github.com/mksglu/cm-ci-lab/actions/runs/41193613063) |
| gin | sonnet-r1 | $0.0603 / 8 / True | $0.0626 / 9 / True | [41193767025](https://github.com/mksglu/cm-ci-lab/actions/runs/41193767025) | [41193770589](https://github.com/mksglu/cm-ci-lab/actions/runs/41193770589) |
| loguru | sonnet-r1 | $0.0574 / 8 / False | $0.0640 / 10 / False | [41194106784](https://github.com/mksglu/cm-ci-lab/actions/runs/41194106784) | [41194110045](https://github.com/mksglu/cm-ci-lab/actions/runs/41194110045) |
| rich | sonnet-r1 | $0.0580 / 7 / True | $0.0679 / 8 / True | [41193630176](https://github.com/mksglu/cm-ci-lab/actions/runs/41193630176) | [41193633709](https://github.com/mksglu/cm-ci-lab/actions/runs/41193633709) |
| ripgrep | sonnet-r1 | $0.0700 / 7 / True | $0.0639 / 8 / True | [41193623401](https://github.com/mksglu/cm-ci-lab/actions/runs/41193623401) | [41193626871](https://github.com/mksglu/cm-ci-lab/actions/runs/41193626871) |
| testify | sonnet-r1 | $0.0888 / 10 / True | $0.0890 / 11 / True | [41194100044](https://github.com/mksglu/cm-ci-lab/actions/runs/41194100044) | [41194103476](https://github.com/mksglu/cm-ci-lab/actions/runs/41194103476) |
| tqdm | sonnet-r1 | $0.0475 / 5 / False | $0.0788 / 14 / False | [41194093297](https://github.com/mksglu/cm-ci-lab/actions/runs/41194093297) | [41194096752](https://github.com/mksglu/cm-ci-lab/actions/runs/41194096752) |
| chalk | sonnet-r2 | $0.0610 / 8 / False | $0.0621 / 8 / False | [41194506750](https://github.com/mksglu/cm-ci-lab/actions/runs/41194506750) | [41194510904](https://github.com/mksglu/cm-ci-lab/actions/runs/41194510904) |
| chi | sonnet-r2 | $0.0604 / 7 / True | $0.0677 / 9 / True | [41194792814](https://github.com/mksglu/cm-ci-lab/actions/runs/41194792814) | [41194796551](https://github.com/mksglu/cm-ci-lab/actions/runs/41194796551) |
| cobra | sonnet-r2 | $0.0675 / 8 / True | $0.0762 / 10 / True | [41194363260](https://github.com/mksglu/cm-ci-lab/actions/runs/41194363260) | [41194367784](https://github.com/mksglu/cm-ci-lab/actions/runs/41194367784) |
| dayjs | sonnet-r2 | $0.0613 / 8 / True | $0.0624 / 8 / True | [41194529436](https://github.com/mksglu/cm-ci-lab/actions/runs/41194529436) | [41194533016](https://github.com/mksglu/cm-ci-lab/actions/runs/41194533016) |
| fd | sonnet-r2 | $0.1780 / 20 / False | $0.2716 / 30 / False | [41194521935](https://github.com/mksglu/cm-ci-lab/actions/runs/41194521935) | [41194525628](https://github.com/mksglu/cm-ci-lab/actions/runs/41194525628) |
| flask | sonnet-r2 | $0.0663 / 8 / True | $0.0603 / 8 / True | [41194354542](https://github.com/mksglu/cm-ci-lab/actions/runs/41194354542) | [41194358460](https://github.com/mksglu/cm-ci-lab/actions/runs/41194358460) |
| gin | sonnet-r2 | $0.0688 / 11 / True | $0.0700 / 11 / True | [41194515052](https://github.com/mksglu/cm-ci-lab/actions/runs/41194515052) | [41194518262](https://github.com/mksglu/cm-ci-lab/actions/runs/41194518262) |
| loguru | sonnet-r2 | $0.0560 / 7 / False | $0.0571 / 9 / False | [41194782835](https://github.com/mksglu/cm-ci-lab/actions/runs/41194782835) | [41194786658](https://github.com/mksglu/cm-ci-lab/actions/runs/41194786658) |
| rich | sonnet-r2 | $0.0672 / 9 / True | $0.0744 / 11 / True | [41194380360](https://github.com/mksglu/cm-ci-lab/actions/runs/41194380360) | [41194384231](https://github.com/mksglu/cm-ci-lab/actions/runs/41194384231) |
| ripgrep | sonnet-r2 | $0.0650 / 7 / True | $0.0750 / 7 / True | [41194371767](https://github.com/mksglu/cm-ci-lab/actions/runs/41194371767) | [41194375988](https://github.com/mksglu/cm-ci-lab/actions/runs/41194375988) |
| testify | sonnet-r2 | $0.0858 / 9 / True | $0.1100 / 12 / True | [41194773662](https://github.com/mksglu/cm-ci-lab/actions/runs/41194773662) | [41194777768](https://github.com/mksglu/cm-ci-lab/actions/runs/41194777768) |
| tqdm | sonnet-r2 | $0.0466 / 5 / False | $0.0464 / 6 / False | [41194765498](https://github.com/mksglu/cm-ci-lab/actions/runs/41194765498) | [41194769740](https://github.com/mksglu/cm-ci-lab/actions/runs/41194769740) |
| chalk | opus-r1 | $0.1628 / 10 / False | $0.1843 / 11 / False | [41195109557](https://github.com/mksglu/cm-ci-lab/actions/runs/41195109557) | [41195113419](https://github.com/mksglu/cm-ci-lab/actions/runs/41195113419) |
| chi | opus-r1 | $0.1621 / 11 / True | $0.1748 / 13 / True | [41195396119](https://github.com/mksglu/cm-ci-lab/actions/runs/41195396119) | [41195400447](https://github.com/mksglu/cm-ci-lab/actions/runs/41195400447) |
| cobra | opus-r1 | $0.1760 / 11 / True | $0.1488 / 9 / True | [41194935045](https://github.com/mksglu/cm-ci-lab/actions/runs/41194935045) | [41194938449](https://github.com/mksglu/cm-ci-lab/actions/runs/41194938449) |
| dayjs | opus-r1 | $0.1892 / 11 / True | $0.2122 / 12 / True | [41195133387](https://github.com/mksglu/cm-ci-lab/actions/runs/41195133387) | [41195139072](https://github.com/mksglu/cm-ci-lab/actions/runs/41195139072) |
| fd | opus-r1 | $0.3164 / 16 / False | $0.3500 / 19 / False | [41195125179](https://github.com/mksglu/cm-ci-lab/actions/runs/41195125179) | [41195128890](https://github.com/mksglu/cm-ci-lab/actions/runs/41195128890) |
| flask | opus-r1 | $0.1729 / 7 / False | $0.2696 / 11 / True | [41194928452](https://github.com/mksglu/cm-ci-lab/actions/runs/41194928452) | [41194931853](https://github.com/mksglu/cm-ci-lab/actions/runs/41194931853) |
| gin | opus-r1 | $0.1817 / 12 / True | $0.1937 / 11 / True | [41195117230](https://github.com/mksglu/cm-ci-lab/actions/runs/41195117230) | [41195121024](https://github.com/mksglu/cm-ci-lab/actions/runs/41195121024) |
| loguru | opus-r1 | $0.1717 / 10 / False | $0.2364 / 14 / False | [41195387164](https://github.com/mksglu/cm-ci-lab/actions/runs/41195387164) | [41195391623](https://github.com/mksglu/cm-ci-lab/actions/runs/41195391623) |
| rich | opus-r1 | $0.1881 / 11 / True | $0.2031 / 12 / True | [41194948294](https://github.com/mksglu/cm-ci-lab/actions/runs/41194948294) | [41194951383](https://github.com/mksglu/cm-ci-lab/actions/runs/41194951383) |
| ripgrep | opus-r1 | $0.3102 / 13 / True | $0.2412 / 11 / True | [41194941787](https://github.com/mksglu/cm-ci-lab/actions/runs/41194941787) | [41194945005](https://github.com/mksglu/cm-ci-lab/actions/runs/41194945005) |
| testify | opus-r1 | $0.2223 / 11 / True | $0.1746 / 8 / True | [41195377754](https://github.com/mksglu/cm-ci-lab/actions/runs/41195377754) | [41195382655](https://github.com/mksglu/cm-ci-lab/actions/runs/41195382655) |
| tqdm | opus-r1 | $0.1919 / 13 / False | $0.1788 / 13 / False | [41195368832](https://github.com/mksglu/cm-ci-lab/actions/runs/41195368832) | [41195373373](https://github.com/mksglu/cm-ci-lab/actions/runs/41195373373) |
