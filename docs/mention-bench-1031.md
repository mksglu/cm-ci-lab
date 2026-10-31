# Mention assistant / issue-to-PR benchmark (2026-10-31)

Area: a maintainer writes "@claude <request>" on an issue and the agent implements it (claude.yml, in 8,224 workflow files). Headless `claude -p` (native installer), arms `direct-ts` (direct API + ENABLE_TOOL_SEARCH) and `gateway`. Workflow `.github/workflows/mention.yml`. Nothing here is published.

History: the first run of this benchmark (tags a1031-*) was invalid. The lab tenant `t_ci_lab_1` was paused (free requests used up), so the gateway arm was a plain pass-through with no savings, and it showed +8.4% (Sonnet) and +5.0% (Opus). This doc is the clean re-run (tags c1031-*) with the tenant in full mode: request 1 is about 39% smaller on the gateway arm in every round, and `used_paused` did not grow.

## Result vs the pass bar (fixed in advance): MET

| bar | Sonnet (24 pairs, 12 tasks) | Opus (12 pairs, 12 tasks) |
|---|---|---|
| task-resampled CI upper bound < 0 | YES: -22.7%, CI -28.3 to -16.1 | YES: -20.3%, CI -30.2 to -8.5 |
| quality not lower than direct-ts | yes, 16/24 vs 16/24 | yes, 7/12 vs 8/12 (1 discordant pair, McNemar p=1.000) |
| 0 errors | yes | yes |
| every round valid | yes (used_paused 1518 before and after each round) | yes |
| net per run > 0 | yes, +$0.0125 | yes, +$0.0375 |

The gateway cut cost on both models. Sonnet: cheaper in 22 of 24 pairs. Opus: cheaper in 10 of 12 pairs.


- Template: the real `anthropics/claude-code-action` tag-mode prompt (src/create-prompt/index.ts, generateDefaultPrompt, issue event), same context tags, steps and notes. Tool list: Read, Write, Edit, Bash, Glob, Grep, LS (the action's base tools plus edit tools, as in popular claude.yml files: remotion, twenty, storybook). `--permission-mode acceptEdits`. Forced changes: no GitHub comment tool exists in `claude -p`, so the reply is the final message; the push is printed (`out/push.txt`), never run.
- Request: the real linked issue title and body, with "@claude " in front. 12 tasks, each a merged PR of a repo with 20k+ stars that closes a linked issue: flask #6096 (issue 6093), cobra #2356 (2257), ripgrep #3182 (3180), rich #3180 (3176), chalk #688 (624), gin #4852 (4851), fd #2193 (2192), plus 5 replacements for triage tasks that had no linked issue: dayjs #3180 (3178), tqdm #1830 (1828), testify #1888 (1800), loguru #1508 (1501), chi #1029 (996). Replaced: requests, express, koa, black, axios (no closing issue).
- Snapshot (`lab/mention/task.sh`): the parent of the merge commit as one commit with no history. The PR's test files are held back in a hidden folder and copied in at check time. The upstream clone is deleted from the runner.
- Check: the PR's own tests (hidden test files copied over) must pass.
- Validity: every task fails with the hidden tests and passes with the upstream source fix, no model call. Baseline runs (all fail): flask 41193221211, cobra 41193228967, ripgrep 41193236035, rich 41193242695, chalk 41193250990, gin 41193260419, fd 41193268479, dayjs 41193276371, tqdm 41193284666, testify 41193292551, loguru 41193300610, chi 41193308020. Control runs (all pass): flask 41193224809, cobra 41193232531, ripgrep 41193239424, rich 41193246713, chalk 41193256360, gin 41193264741, fd 41193272133, dayjs 41193280571, tqdm 41193288762, testify 41193296486, loguru 41193304374, chi 41193311780.
- Stats: pairs by (task, round). Cost = mean paired log-ratio gateway/direct-ts, % = exp(mean)-1. 95% CI: bootstrap over tasks (all rounds of a task together), 10,000 resamples, seed 1 (`lab/mention/stats.py`). Fee $0.0009 per request. Dispatch 8 at a time. Tags c1031-mention-sonnet-r1, -sonnet-r2, -opus-r1 (Opus model claude-opus-5-5). Quota guard (`/tmp/ci-quota-guard.py --need 3000`) before and after each round: mode full each time, used_paused stayed at 1518 (no request ran paused). Spend: Sonnet $3.421, Opus $5.260, total $8.68 (cap $15 per lane).


## Numbers

Sonnet (r1 + r2):
```
pairs 24 tasks 12 errors 0
cost change -22.7%  task-resampled 95% CI -28.3..-16.1  cheaper 22/24
direct-ts: pass 16/24 mean cost $0.0812 turns 9.96 uncached 17 cache_write 12185 cache_read 210992 output 2958
gateway: pass 16/24 mean cost $0.0614 turns 8.08 uncached 522 cache_write 8734 cache_read 122440 output 2625
net per run = (0.0812-0.0614) - 0.0009x8.08 = $0.0125
McNemar exact: direct-only 0 gateway-only 0 p=1.000
spend $3.421
```
Sonnet round 1 alone: -18.1%, CI -24.2 to -11.3, cheaper 11/12.

Opus (r1):
```
pairs 12 tasks 12 errors 0
cost change -20.3%  task-resampled 95% CI -30.2..-8.5  cheaper 10/12
direct-ts: pass 8/12 mean cost $0.2431 turns 13.92 uncached 23 cache_write 17039 cache_read 307580 output 4814
gateway: pass 7/12 mean cost $0.1953 turns 11.50 uncached 529 cache_write 12666 cache_read 190662 output 4584
net per run = (0.2431-0.1953) - 0.0009x11.50 = $0.0375
McNemar exact: direct-only 1 gateway-only 0 p=1.000
spend $5.260
```

## Quality

- Pass rate: Sonnet 16/24 vs 16/24 (McNemar exact p=1.000, 0 and 0 discordant). Opus 8/12 vs 7/12 (p=1.000; one discordant pair, flask: the direct-ts run passed, the gateway run failed 2 of 493 tests, `test_run_from_config[...[::1]:8080...]` and `test_session_transaction_ipv6`, run 41203044681). I read the log: the gateway patch did not handle the bracketed IPv6 host in the server name and in the test client, so it is an incomplete fix, not an infrastructure error. In the invalid run the same task went the other way (direct-ts made no patch), so single flask runs are noisy on both arms.
- Four tasks fail on both arms in every round, on both models: chalk, fd, loguru, tqdm. I did not investigate why they fail (not measured). They count in the pass rates and in the cost pairs.
- Blind patch check (labels hidden, arm order shuffled with seed 7, key kept outside the judge folder): 23 pairs had both arms passing. 1 pair has identical source patches. I read the other 22 pairs (44 patches). All are real fixes of the issue's root cause, with no test hack and no special-casing. Differences are style only (for example chi: helper method vs a dedup loop; cobra: copy the slice vs clip its capacity; flask: manual bracket parsing vs `urlsplit`; ripgrep: guard only vs guard plus a `find_at` change). I read the 22 pairs myself, not an independent judge.
- No passing run lacks a source change (checked on all 72 diffs, test files excluded).

## Anatomy (per request, tokens)

All 72 runs, mean per request, direct-ts vs gateway:
- Request 1 total (uncached + cache_write + cache_read): 20,155 vs 12,358 (-38.7%). Request 1 is smaller on the gateway in every round (Sonnet r1 20,139 vs 12,343 over 12 pairs; Sonnet all 24 pairs 20,139 vs 12,343; Opus 20,186 vs 12,389).
- Request 1 split: cache_write 5,629 vs 2,617, cache_read 14,524 vs 9,249, uncached 2 vs 493.
- Later requests: cache_write 965 vs 935 (same size: new tool results), cache_read 26,990 vs 17,110 (-36.6%).
- Requests per run: 9.5 vs 8.9.

gin, Sonnet r1, direct-ts (run 41201291870), cost $0.0591, 6 requests:
```
req  uncached  cache_write  cache_read
0    2         5139         14547
1    2         1059         19686
2    2         1614         20745
3    2         1029         22359
4    2         595          23388
5    2         326          23983
```
gin, Sonnet r1, gateway (run 41201294601), cost $0.0427, 7 requests:
```
0    494       1903         9495
1    4         1415         11398
2    4         359          12813
3    4         246          13172
4    4         398          13418
5    4         760          13816
6    4         326          14576
```

Where the gateway saves: the fixed prefix is smaller (request 1 about 7.8k tokens less), and every later request re-reads that smaller prefix from the cache, so cache reads fall by about 37%. It does not shrink new tool results: cache_write per later request is the same (965 vs 935). Turn counts per pair over all 36 pairs: gateway higher in 5, lower in 26, equal in 5.

## Caveats

- Per-run noise is large. The task-resampled CI covers it for cost.
- `claude -p` mirrors the action's prompt and tools. It is not the action itself (Anthropic rejects that entrypoint for this key; no entrypoint spoofing).
- The per-message `output` column in `per-message-usage.json` reads 0 for gateway runs (the stream reports output tokens differently through the gateway). Output tokens in the tables above come from the run totals in `lab-metrics.json`, not from that column.
- Sonnet has 2 rounds and Opus has 1. The Opus CI is wider (-30.2 to -8.5) but its upper bound is below zero.
- The mention workload is 12 tasks of 12 repos. The saving here comes from the prefix cut; it may differ for other prompts.
- The Opus model id is `claude-opus-5-5` (the same as the invalid run).

## Per pair (cost / turns / pass)

| task | round | direct-ts | gateway | direct-ts run | gateway run |
|---|---|---|---|---|---|
| chalk | sonnet-r1 | $0.0678 / 9 / False | $0.0509 / 6 / False | [41201302547](https://github.com/mksglu/cm-ci-lab/actions/runs/41201302547) | [41201305606](https://github.com/mksglu/cm-ci-lab/actions/runs/41201305606) |
| chi | sonnet-r1 | $0.0535 / 7 / True | $0.0438 / 6 / True | [41201825723](https://github.com/mksglu/cm-ci-lab/actions/runs/41201825723) | [41201829132](https://github.com/mksglu/cm-ci-lab/actions/runs/41201829132) |
| cobra | sonnet-r1 | $0.0823 / 11 / True | $0.0801 / 12 / True | [41200830411](https://github.com/mksglu/cm-ci-lab/actions/runs/41200830411) | [41200832996](https://github.com/mksglu/cm-ci-lab/actions/runs/41200832996) |
| dayjs | sonnet-r1 | $0.0612 / 6 / True | $0.0483 / 6 / True | [41201308397](https://github.com/mksglu/cm-ci-lab/actions/runs/41201308397) | [41201311216](https://github.com/mksglu/cm-ci-lab/actions/runs/41201311216) |
| fd | sonnet-r1 | $0.2304 / 29 / False | $0.2008 / 25 / False | [41201297152](https://github.com/mksglu/cm-ci-lab/actions/runs/41201297152) | [41201299642](https://github.com/mksglu/cm-ci-lab/actions/runs/41201299642) |
| flask | sonnet-r1 | $0.0704 / 9 / True | $0.0745 / 6 / True | [41200825200](https://github.com/mksglu/cm-ci-lab/actions/runs/41200825200) | [41200828044](https://github.com/mksglu/cm-ci-lab/actions/runs/41200828044) |
| gin | sonnet-r1 | $0.0591 / 8 / True | $0.0427 / 7 / True | [41201291870](https://github.com/mksglu/cm-ci-lab/actions/runs/41201291870) | [41201294601](https://github.com/mksglu/cm-ci-lab/actions/runs/41201294601) |
| loguru | sonnet-r1 | $0.0658 / 11 / False | $0.0465 / 7 / False | [41201820132](https://github.com/mksglu/cm-ci-lab/actions/runs/41201820132) | [41201823025](https://github.com/mksglu/cm-ci-lab/actions/runs/41201823025) |
| rich | sonnet-r1 | $0.0582 / 7 / True | $0.0542 / 8 / True | [41200840401](https://github.com/mksglu/cm-ci-lab/actions/runs/41200840401) | [41200842878](https://github.com/mksglu/cm-ci-lab/actions/runs/41200842878) |
| ripgrep | sonnet-r1 | $0.0864 / 8 / True | $0.0556 / 6 / True | [41200835563](https://github.com/mksglu/cm-ci-lab/actions/runs/41200835563) | [41200837865](https://github.com/mksglu/cm-ci-lab/actions/runs/41200837865) |
| testify | sonnet-r1 | $0.0764 / 8 / True | $0.0679 / 9 / True | [41201814648](https://github.com/mksglu/cm-ci-lab/actions/runs/41201814648) | [41201817329](https://github.com/mksglu/cm-ci-lab/actions/runs/41201817329) |
| tqdm | sonnet-r1 | $0.0524 / 6 / False | $0.0401 / 6 / False | [41201809338](https://github.com/mksglu/cm-ci-lab/actions/runs/41201809338) | [41201812081](https://github.com/mksglu/cm-ci-lab/actions/runs/41201812081) |
| chalk | sonnet-r2 | $0.0565 / 7 / False | $0.0445 / 6 / False | [41202360075](https://github.com/mksglu/cm-ci-lab/actions/runs/41202360075) | [41202362516](https://github.com/mksglu/cm-ci-lab/actions/runs/41202362516) |
| chi | sonnet-r2 | $0.0555 / 6 / True | $0.0383 / 5 / True | [41202861712](https://github.com/mksglu/cm-ci-lab/actions/runs/41202861712) | [41202864771](https://github.com/mksglu/cm-ci-lab/actions/runs/41202864771) |
| cobra | sonnet-r2 | $0.0671 / 8 / True | $0.0465 / 6 / True | [41202012669](https://github.com/mksglu/cm-ci-lab/actions/runs/41202012669) | [41202015298](https://github.com/mksglu/cm-ci-lab/actions/runs/41202015298) |
| dayjs | sonnet-r2 | $0.0634 / 8 / True | $0.0484 / 6 / True | [41202364988](https://github.com/mksglu/cm-ci-lab/actions/runs/41202364988) | [41202367437](https://github.com/mksglu/cm-ci-lab/actions/runs/41202367437) |
| fd | sonnet-r2 | $0.2843 / 30 / False | $0.1167 / 15 / False | [41202353728](https://github.com/mksglu/cm-ci-lab/actions/runs/41202353728) | [41202357060](https://github.com/mksglu/cm-ci-lab/actions/runs/41202357060) |
| flask | sonnet-r2 | $0.0650 / 9 / True | $0.0470 / 6 / True | [41202007856](https://github.com/mksglu/cm-ci-lab/actions/runs/41202007856) | [41202010425](https://github.com/mksglu/cm-ci-lab/actions/runs/41202010425) |
| gin | sonnet-r2 | $0.0653 / 10 / True | $0.0581 / 10 / True | [41202347889](https://github.com/mksglu/cm-ci-lab/actions/runs/41202347889) | [41202350425](https://github.com/mksglu/cm-ci-lab/actions/runs/41202350425) |
| loguru | sonnet-r2 | $0.0515 / 6 / False | $0.0405 / 5 / False | [41202855956](https://github.com/mksglu/cm-ci-lab/actions/runs/41202855956) | [41202858647](https://github.com/mksglu/cm-ci-lab/actions/runs/41202858647) |
| rich | sonnet-r2 | $0.0728 / 10 / True | $0.0451 / 6 / True | [41202022970](https://github.com/mksglu/cm-ci-lab/actions/runs/41202022970) | [41202025429](https://github.com/mksglu/cm-ci-lab/actions/runs/41202025429) |
| ripgrep | sonnet-r2 | $0.0736 / 9 / True | $0.0604 / 8 / True | [41202017918](https://github.com/mksglu/cm-ci-lab/actions/runs/41202017918) | [41202020655](https://github.com/mksglu/cm-ci-lab/actions/runs/41202020655) |
| testify | sonnet-r2 | $0.0651 / 7 / True | $0.0850 / 12 / True | [41202849818](https://github.com/mksglu/cm-ci-lab/actions/runs/41202849818) | [41202852799](https://github.com/mksglu/cm-ci-lab/actions/runs/41202852799) |
| tqdm | sonnet-r2 | $0.0641 / 10 / False | $0.0368 / 5 / False | [41202843404](https://github.com/mksglu/cm-ci-lab/actions/runs/41202843404) | [41202846337](https://github.com/mksglu/cm-ci-lab/actions/runs/41202846337) |
| chalk | opus-r1 | $0.2062 / 12 / False | $0.1505 / 10 / False | [41203319008](https://github.com/mksglu/cm-ci-lab/actions/runs/41203319008) | [41203321438](https://github.com/mksglu/cm-ci-lab/actions/runs/41203321438) |
| chi | opus-r1 | $0.1777 / 12 / True | $0.1434 / 11 / True | [41203588575](https://github.com/mksglu/cm-ci-lab/actions/runs/41203588575) | [41203591563](https://github.com/mksglu/cm-ci-lab/actions/runs/41203591563) |
| cobra | opus-r1 | $0.2031 / 10 / True | $0.1177 / 9 / True | [41203047064](https://github.com/mksglu/cm-ci-lab/actions/runs/41203047064) | [41203050156](https://github.com/mksglu/cm-ci-lab/actions/runs/41203050156) |
| dayjs | opus-r1 | $0.2265 / 12 / True | $0.1956 / 12 / True | [41203323623](https://github.com/mksglu/cm-ci-lab/actions/runs/41203323623) | [41203326025](https://github.com/mksglu/cm-ci-lab/actions/runs/41203326025) |
| fd | opus-r1 | $0.5678 / 30 / False | $0.3080 / 17 / False | [41203313557](https://github.com/mksglu/cm-ci-lab/actions/runs/41203313557) | [41203316114](https://github.com/mksglu/cm-ci-lab/actions/runs/41203316114) |
| flask | opus-r1 | $0.1823 / 12 / True | $0.1107 / 6 / False | [41203042263](https://github.com/mksglu/cm-ci-lab/actions/runs/41203042263) | [41203044681](https://github.com/mksglu/cm-ci-lab/actions/runs/41203044681) |
| gin | opus-r1 | $0.1809 / 12 / True | $0.1461 / 11 / True | [41203308729](https://github.com/mksglu/cm-ci-lab/actions/runs/41203308729) | [41203311071](https://github.com/mksglu/cm-ci-lab/actions/runs/41203311071) |
| loguru | opus-r1 | $0.1967 / 12 / False | $0.2394 / 14 / False | [41203581994](https://github.com/mksglu/cm-ci-lab/actions/runs/41203581994) | [41203585199](https://github.com/mksglu/cm-ci-lab/actions/runs/41203585199) |
| rich | opus-r1 | $0.1875 / 11 / True | $0.1848 / 11 / True | [41203058217](https://github.com/mksglu/cm-ci-lab/actions/runs/41203058217) | [41203060843](https://github.com/mksglu/cm-ci-lab/actions/runs/41203060843) |
| ripgrep | opus-r1 | $0.3748 / 17 / True | $0.4209 / 16 / True | [41203052779](https://github.com/mksglu/cm-ci-lab/actions/runs/41203052779) | [41203055338](https://github.com/mksglu/cm-ci-lab/actions/runs/41203055338) |
| testify | opus-r1 | $0.2239 / 12 / True | $0.1642 / 9 / True | [41203575082](https://github.com/mksglu/cm-ci-lab/actions/runs/41203575082) | [41203578483](https://github.com/mksglu/cm-ci-lab/actions/runs/41203578483) |
| tqdm | opus-r1 | $0.1895 / 15 / False | $0.1619 / 12 / False | [41203567883](https://github.com/mksglu/cm-ci-lab/actions/runs/41203567883) | [41203571612](https://github.com/mksglu/cm-ci-lab/actions/runs/41203571612) |
