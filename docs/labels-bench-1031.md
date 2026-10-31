# Issue triage and labels benchmark (2026-10-31, clean re-run)

Area: issue triage and labels. Real templates: anthropics/claude-code `claude-issue-triage.yml` (Opus), openai/codex `issue-labeler.yml`, gemini-cli automated triage. Headless `claude -p` (native installer). Arms `direct-ts` (direct API + ENABLE_TOOL_SEARCH) and `gateway`. Workflow `.github/workflows/labels.yml`. Nothing here is published.

History: the first run of this doc (tags a1031-labels-*) was invalid because the lab tenant `t_ci_lab_1` was paused at 2026-10-31 10:29:57 UTC, so the gateway arm was plain pass-through. This is the clean re-run in full mode (tags c1031-labels-sonnet-r1, c1031-labels-sonnet-r2, c1031-labels-opus-r1).

## Round validity

| round | used_paused before | used_paused after | request 1 input tokens direct-ts / gateway | valid |
|---|---|---|---|---|
| sonnet-r1 | 1,518 | 1,518 | 16,771 / 10,671 | yes |
| sonnet-r2 | 1,518 | 1,518 | 16,771 / 10,671 | yes |
| opus-r1 | 1,518 | 1,518 | 16,818 / 10,718 | yes |

The gateway request 1 is about 36% smaller than direct-ts, so the gateway was in full mode (in the invalid run the two were equal).

## Result vs the pass bar (fixed in advance)

**The cost bar is met on both models. The quality bar is met within noise, but not on the point estimate.**

| model | pairs (tasks) | cost change gateway vs direct-ts | task-resampled 95% CI | cheaper pairs | mean cost direct-ts / gateway | requests | F1 direct-ts / gateway | net per run at $0.0009 per request | errors |
|---|---|---|---|---|---|---|---|---|---|
| Sonnet 5.5 (2 rounds) | 24 (12) | -14.4% | -20.5% to -8.6% | 18 of 24 | $0.0245 / $0.0209 | 2.17 / 2.17 | 0.588 / 0.579 | +$0.0016 | 0 |
| Opus 5.5 (1 round) | 12 (12) | -14.4% | -23.4% to -3.4% | 9 of 12 | $0.0765 / $0.0658 | 3.42 / 3.58 | 0.670 / 0.662 | +$0.0075 | 0 |

Per Sonnet round: r1 -14.0% (CI -21.5% to -4.3%, 10 of 12 cheaper), r2 -14.7% (CI -23.3% to -5.2%, 8 of 12 cheaper).

- CI upper bound < 0: yes (Sonnet -8.6%, Opus -3.4%).
- Net saving > 0 at the $0.0009 fee: yes (Sonnet +$0.0016, Opus +$0.0075 per run). Sonnet's margin is small.
- 0 errors: yes. Every round valid: yes.
- Quality not lower: F1 differences are small and not significant (Sonnet -0.010, CI -0.040 to +0.029; Opus -0.008, CI -0.085 to +0.071), but both point estimates are below direct-ts. Read strictly, the bar says "not lower", so this item is not proven. Per round, Sonnet r1 is -0.027 and r2 is +0.008.

Method: pairs by (task, round); cost = mean paired log-ratio gateway/direct-ts, shown as exp(mean)-1; bootstrap resamples the 12 TASKS (all rounds of a task together), 10,000 resamples, seed 1. Net per run = (mean direct-ts - mean gateway) - 0.0009 x mean gateway requests (requests = assistant messages). Spend: Sonnet $1.09 (both arms, 48 runs), Opus $1.71 (24 runs), total about $2.80, under the $15 cap per lane.

Tokens per run (mean; uncached / cache_write / cache_read / output):

| arm | Sonnet | Opus |
|---|---|---|
| direct-ts | 4 / 7,682 / 33,154 / 197 | 6 / 9,021 / 52,944 / 717 |
| gateway | 482 / 5,980 / 21,621 / 284 | 403 / 6,838 / 36,755 / 684 |

## Where the saving comes from (anatomy)

Request 1, mean per arm: Sonnet direct-ts 16,771 tokens (cache_write 3,941, cache_read 12,828 over both rounds), gateway 10,671 (cache_write 1,303, cache_read 8,892). Opus direct-ts 16,818, gateway 10,718. The gateway cuts about 6,100 tokens from the fixed prefix of request 1, which also lowers the first cache write and every later cache read. Tool results (an issue body, a label list) are the same bytes on both arms and are not shrunk.

Requests 2 and later, mean per request: Sonnet direct-ts cache_write 3,206, cache_read 17,422 (28 requests); gateway cache_write 4,009, cache_read 10,911 (28 requests). Opus direct-ts cache_write 1,814, cache_read 19,016 (29 requests); gateway cache_write 2,270, cache_read 13,244 (31 requests). Cache reads fall by about 6,000 to 6,500 tokens per request; cache writes rise a little on the gateway. The gateway arm also shows a few hundred uncached tokens per run (482 Sonnet, 403 Opus) where direct-ts shows 4 to 6. Per-request output counts for requests 2 and later are 0 in the gateway usage lists, so this table does not compare output; the run totals above come from the result message and are used for cost.

A triage run is 2 to 4 requests, so the per-request fee is a large part of the bill: Sonnet's net gain after the fee is only +$0.0016 per run.

## Setup

- Template: the most-starred, anthropics/claude-code `.claude/commands/triage-issue.md` (prompt in `lab/labels/prompt.md`, mirrored; lifecycle labels kept, writes replaced by a final line `{"labels": [...]}`). Tools allowed: `Bash(./scripts/gh.sh:*)`, `Bash(./scripts/edit-issue-labels.sh:*)`; Write, Edit, WebFetch, WebSearch disallowed. `anthropics/claude-code-action` is not used (the key is rejected for the action entrypoint); the prompt and tools are mirrored with `claude -p`. The Opus template model there is opus-4-6; this run used claude-opus-5-5.
- `lab/labels/scripts/gh.py`: read-only `gh` wrapper (label list, issue view N [--comments], issue list, search issues). The target issue shows title, body and author only (no labels, no comments, state open). Other issues and their comments are visible only if created before the target. Any other command is refused. The edit-label script prints a DRY-RUN line and writes nothing to any repo.
- Tasks (`lab/labels/tasks.json`): 12 closed issues, 2 per repo, from godotengine/godot (119k stars), zed-industries/zed (92k), tauri-apps/tauri (112k), oven-sh/bun (96k), rust-lang/rust (121k), microsoft/vscode (194k). Ground truth: labels a human (not the issue author, not a bot) added through a label event and that are still on the issue. Status, bot, priority and team labels are dropped from both truth and prediction (`DROP` list in `lab/labels/extract.py`). Filter: body 300 to 5,000 characters, issue author is a user, at least 2 truth labels.
- Quality: label F1 against the truth, computed by script from the final JSON line, so it needs no hidden arm labels. All 72 answers parsed.

## Caveats

- F1 is low on both arms (about 0.58 Sonnet, 0.67 Opus). Maintainer labels are subjective, so F1 mostly measures label-set taste. 12 tasks is small; the F1 CIs are wide.
- Opus has one round, so its CI is the widest (-23.4% to -3.4%).
- Request counts are assistant messages in `per-message-usage.json`; `num_turns` can differ from them.
- The first run is kept only as history; none of its numbers are used here.

## Per pair

Cost / turns / F1 per arm.

| task | tag | direct-ts cost / turns / F1 | gateway cost / turns / F1 | direct-ts run | gateway run |
|---|---|---|---|---|---|
| bun-47006 | opus-r1 | $0.0628 / 3 / 1.00 | $0.0471 / 3 / 0.80 | [41202031449](https://github.com/mksglu/cm-ci-lab/actions/runs/41202031449) | [41202034770](https://github.com/mksglu/cm-ci-lab/actions/runs/41202034770) |
| bun-47090 | opus-r1 | $0.0970 / 2 / 0.86 | $0.0591 / 3 / 0.86 | [41202023353](https://github.com/mksglu/cm-ci-lab/actions/runs/41202023353) | [41202027286](https://github.com/mksglu/cm-ci-lab/actions/runs/41202027286) |
| godot-124937 | opus-r1 | $0.0622 / 3 / 0.57 | $0.0476 / 3 / 0.57 | [41201985414](https://github.com/mksglu/cm-ci-lab/actions/runs/41201985414) | [41201989350](https://github.com/mksglu/cm-ci-lab/actions/runs/41201989350) |
| godot-124950 | opus-r1 | $0.1127 / 3 / 0.80 | $0.0839 / 3 / 1.00 | [41201977510](https://github.com/mksglu/cm-ci-lab/actions/runs/41201977510) | [41201981396](https://github.com/mksglu/cm-ci-lab/actions/runs/41201981396) |
| rust-165127 | opus-r1 | $0.0709 / 4 / 0.22 | $0.0536 / 4 / 0.25 | [41202045264](https://github.com/mksglu/cm-ci-lab/actions/runs/41202045264) | [41202049137](https://github.com/mksglu/cm-ci-lab/actions/runs/41202049137) |
| rust-165173 | opus-r1 | $0.0713 / 4 / 0.59 | $0.0519 / 4 / 0.43 | [41202038193](https://github.com/mksglu/cm-ci-lab/actions/runs/41202038193) | [41202041611](https://github.com/mksglu/cm-ci-lab/actions/runs/41202041611) |
| tauri-16323 | opus-r1 | $0.0642 / 3 / 1.00 | $0.0689 / 2 / 1.00 | [41202015696](https://github.com/mksglu/cm-ci-lab/actions/runs/41202015696) | [41202019468](https://github.com/mksglu/cm-ci-lab/actions/runs/41202019468) |
| tauri-16340 | opus-r1 | $0.0715 / 3 / 0.67 | $0.0667 / 1 / 0.67 | [41202008764](https://github.com/mksglu/cm-ci-lab/actions/runs/41202008764) | [41202012238](https://github.com/mksglu/cm-ci-lab/actions/runs/41202012238) |
| vscode-345099 | opus-r1 | $0.0614 / 4 / 0.33 | $0.0593 / 4 / 0.33 | [41202059645](https://github.com/mksglu/cm-ci-lab/actions/runs/41202059645) | [41202063274](https://github.com/mksglu/cm-ci-lab/actions/runs/41202063274) |
| vscode-345117 | opus-r1 | $0.0643 / 3 / 0.40 | $0.0855 / 3 / 0.67 | [41202052560](https://github.com/mksglu/cm-ci-lab/actions/runs/41202052560) | [41202056265](https://github.com/mksglu/cm-ci-lab/actions/runs/41202056265) |
| zed-66163 | opus-r1 | $0.0946 / 3 / 0.80 | $0.0947 / 4 / 0.80 | [41202001097](https://github.com/mksglu/cm-ci-lab/actions/runs/41202001097) | [41202004937](https://github.com/mksglu/cm-ci-lab/actions/runs/41202004937) |
| zed-66189 | opus-r1 | $0.0855 / 3 / 0.80 | $0.0715 / 3 / 0.57 | [41201993702](https://github.com/mksglu/cm-ci-lab/actions/runs/41201993702) | [41201997507](https://github.com/mksglu/cm-ci-lab/actions/runs/41201997507) |
| bun-47006 | sonnet-r1 | $0.0226 / 2 / 0.80 | $0.0217 / 3 / 0.67 | [41200886893](https://github.com/mksglu/cm-ci-lab/actions/runs/41200886893) | [41200890867](https://github.com/mksglu/cm-ci-lab/actions/runs/41200890867) |
| bun-47090 | sonnet-r1 | $0.0292 / 3 / 0.86 | $0.0242 / 2 / 0.75 | [41200878787](https://github.com/mksglu/cm-ci-lab/actions/runs/41200878787) | [41200882912](https://github.com/mksglu/cm-ci-lab/actions/runs/41200882912) |
| godot-124937 | sonnet-r1 | $0.0206 / 2 / 0.50 | $0.0138 / 2 / 0.75 | [41200838744](https://github.com/mksglu/cm-ci-lab/actions/runs/41200838744) | [41200842504](https://github.com/mksglu/cm-ci-lab/actions/runs/41200842504) |
| godot-124950 | sonnet-r1 | $0.0189 / 2 / 0.80 | $0.0259 / 2 / 0.80 | [41200831451](https://github.com/mksglu/cm-ci-lab/actions/runs/41200831451) | [41200835045](https://github.com/mksglu/cm-ci-lab/actions/runs/41200835045) |
| rust-165127 | sonnet-r1 | $0.0317 / 2 / 0.00 | $0.0257 / 2 / 0.00 | [41200902415](https://github.com/mksglu/cm-ci-lab/actions/runs/41200902415) | [41200906332](https://github.com/mksglu/cm-ci-lab/actions/runs/41200906332) |
| rust-165173 | sonnet-r1 | $0.0247 / 2 / 0.40 | $0.0194 / 2 / 0.40 | [41200894856](https://github.com/mksglu/cm-ci-lab/actions/runs/41200894856) | [41200898672](https://github.com/mksglu/cm-ci-lab/actions/runs/41200898672) |
| tauri-16323 | sonnet-r1 | $0.0214 / 2 / 1.00 | $0.0185 / 2 / 1.00 | [41200871257](https://github.com/mksglu/cm-ci-lab/actions/runs/41200871257) | [41200875144](https://github.com/mksglu/cm-ci-lab/actions/runs/41200875144) |
| tauri-16340 | sonnet-r1 | $0.0228 / 2 / 0.67 | $0.0243 / 3 / 0.67 | [41200863042](https://github.com/mksglu/cm-ci-lab/actions/runs/41200863042) | [41200867042](https://github.com/mksglu/cm-ci-lab/actions/runs/41200867042) |
| vscode-345099 | sonnet-r1 | $0.0254 / 2 / 0.00 | $0.0198 / 2 / 0.00 | [41200918038](https://github.com/mksglu/cm-ci-lab/actions/runs/41200918038) | [41200922501](https://github.com/mksglu/cm-ci-lab/actions/runs/41200922501) |
| vscode-345117 | sonnet-r1 | $0.0250 / 2 / 0.40 | $0.0193 / 2 / 0.40 | [41200910242](https://github.com/mksglu/cm-ci-lab/actions/runs/41200910242) | [41200913986](https://github.com/mksglu/cm-ci-lab/actions/runs/41200913986) |
| zed-66163 | sonnet-r1 | $0.0327 / 2 / 1.00 | $0.0259 / 2 / 0.80 | [41200854400](https://github.com/mksglu/cm-ci-lab/actions/runs/41200854400) | [41200858432](https://github.com/mksglu/cm-ci-lab/actions/runs/41200858432) |
| zed-66189 | sonnet-r1 | $0.0328 / 3 / 0.80 | $0.0260 / 2 / 0.67 | [41200846398](https://github.com/mksglu/cm-ci-lab/actions/runs/41200846398) | [41200850378](https://github.com/mksglu/cm-ci-lab/actions/runs/41200850378) |
| bun-47006 | sonnet-r2 | $0.0250 / 2 / 0.80 | $0.0216 / 3 / 0.80 | [41201795386](https://github.com/mksglu/cm-ci-lab/actions/runs/41201795386) | [41201799773](https://github.com/mksglu/cm-ci-lab/actions/runs/41201799773) |
| bun-47090 | sonnet-r2 | $0.0295 / 3 / 0.86 | $0.0248 / 2 / 0.86 | [41201787610](https://github.com/mksglu/cm-ci-lab/actions/runs/41201787610) | [41201791434](https://github.com/mksglu/cm-ci-lab/actions/runs/41201791434) |
| godot-124937 | sonnet-r2 | $0.0232 / 2 / 0.50 | $0.0147 / 2 / 0.57 | [41201742674](https://github.com/mksglu/cm-ci-lab/actions/runs/41201742674) | [41201746909](https://github.com/mksglu/cm-ci-lab/actions/runs/41201746909) |
| godot-124950 | sonnet-r2 | $0.0192 / 2 / 0.80 | $0.0124 / 2 / 0.80 | [41201734365](https://github.com/mksglu/cm-ci-lab/actions/runs/41201734365) | [41201738086](https://github.com/mksglu/cm-ci-lab/actions/runs/41201738086) |
| rust-165127 | sonnet-r2 | $0.0201 / 2 / 0.00 | $0.0224 / 2 / 0.00 | [41201812283](https://github.com/mksglu/cm-ci-lab/actions/runs/41201812283) | [41201816563](https://github.com/mksglu/cm-ci-lab/actions/runs/41201816563) |
| rust-165173 | sonnet-r2 | $0.0244 / 2 / 0.40 | $0.0174 / 2 / 0.22 | [41201803989](https://github.com/mksglu/cm-ci-lab/actions/runs/41201803989) | [41201808376](https://github.com/mksglu/cm-ci-lab/actions/runs/41201808376) |
| tauri-16323 | sonnet-r2 | $0.0214 / 2 / 1.00 | $0.0183 / 2 / 1.00 | [41201778758](https://github.com/mksglu/cm-ci-lab/actions/runs/41201778758) | [41201782976](https://github.com/mksglu/cm-ci-lab/actions/runs/41201782976) |
| tauri-16340 | sonnet-r2 | $0.0228 / 2 / 0.67 | $0.0235 / 3 / 0.67 | [41201769876](https://github.com/mksglu/cm-ci-lab/actions/runs/41201769876) | [41201774322](https://github.com/mksglu/cm-ci-lab/actions/runs/41201774322) |
| vscode-345099 | sonnet-r2 | $0.0143 / 2 / 0.00 | $0.0153 / 2 / 0.00 | [41201829204](https://github.com/mksglu/cm-ci-lab/actions/runs/41201829204) | [41201833117](https://github.com/mksglu/cm-ci-lab/actions/runs/41201833117) |
| vscode-345117 | sonnet-r2 | $0.0139 / 2 / 0.40 | $0.0151 / 2 / 0.40 | [41201820790](https://github.com/mksglu/cm-ci-lab/actions/runs/41201820790) | [41201824819](https://github.com/mksglu/cm-ci-lab/actions/runs/41201824819) |
| zed-66163 | sonnet-r2 | $0.0334 / 2 / 0.80 | $0.0259 / 2 / 1.00 | [41201760796](https://github.com/mksglu/cm-ci-lab/actions/runs/41201760796) | [41201764959](https://github.com/mksglu/cm-ci-lab/actions/runs/41201764959) |
| zed-66189 | sonnet-r2 | $0.0332 / 3 / 0.67 | $0.0262 / 2 / 0.67 | [41201750949](https://github.com/mksglu/cm-ci-lab/actions/runs/41201750949) | [41201756238](https://github.com/mksglu/cm-ci-lab/actions/runs/41201756238) |
