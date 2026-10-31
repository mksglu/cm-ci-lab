> **INVALID: do not use the numbers below.** The lab tenant `t_ci_lab_1` used up its 1,000 free requests and was paused at 2026-10-31 10:29:57 UTC. A paused tenant gets plain pass-through: the gateway forwards the request unchanged, with no savings. 37 of the 37 gateway-arm runs behind this doc started after that time, so this doc compares direct with a paused pass-through, not with the gateway. The tenant is back in full mode and a clean re-run is in progress. Note added 2026-10-31.

# Issue triage and labels benchmark (2026-10-31)

Area: issue triage and labels. Real templates: anthropics/claude-code `claude-issue-triage.yml` (Opus), openai/codex `issue-labeler.yml`, gemini-cli automated triage. Headless `claude -p` (native installer). Arms `direct-ts` (direct API + ENABLE_TOOL_SEARCH) and `gateway`. Workflow `.github/workflows/labels.yml`. Nothing here is published.

## Result vs the pass bar (fixed in advance)

**The bar is NOT met. The gateway gives no saving in this area.**

| model | pairs (tasks) | cost change gateway vs direct-ts | task-resampled 95% CI | cheaper pairs | mean cost direct-ts / gateway | turns | F1 direct-ts / gateway | net per run at $0.0009 per request | errors |
|---|---|---|---|---|---|---|---|---|---|
| Sonnet 5.5 (2 rounds) | 24 (12) | +3.4% | -5.3% to +11.1% | 9 of 24 | $0.0196 / $0.0204 | 2.04 / 2.21 | 0.577 / 0.562 | -$0.0028 | 0 |
| Opus 5.5 (1 round) | 12 (12) | -0.7% | -5.5% to +3.8% | 4 of 12 | $0.0759 / $0.0753 | 3.42 / 3.25 | 0.741 / 0.707 | -$0.0024 | 0 |

- CI upper bound < 0: no (Sonnet +11.1%, Opus +3.8%).
- Quality not lower: F1 is numerically lower on the gateway (Sonnet -0.015, CI -0.056 to +0.029; Opus -0.034, CI -0.112 to +0.047). Not significant, but the bar says "not lower", so this also fails on the point estimate.
- Net saving > 0: no. The fee ($0.0009 per request) costs more than any gain, on both models.
- 0 errors: yes.

Method: pairs by (task, round); cost = mean paired log-ratio gateway/direct-ts, shown as exp(mean)-1; bootstrap resamples the 12 TASKS (all rounds of a task together), 10,000 resamples, seed 1. Net per run = (mean direct-ts - mean gateway) - 0.0009 x mean gateway turns. Spend: Sonnet $0.958, Opus $1.814, smoke pair about $0.09 (excluded from stats). Total about $2.9, far under the $15 cap.

Tokens per run (mean; uncached / cache_write / cache_read / output):

| arm | Sonnet | Opus |
|---|---|---|
| direct-ts | 4 / 5,392 / 32,864 / 192 | 7 / 9,829 / 57,358 / 760 |
| gateway | 4 / 5,877 / 34,082 / 224 | 7 / 9,757 / 53,419 / 792 |

## Why there is no saving here (anatomy)

Request 1, mean over all 36 runs per arm: direct-ts uncached 2.0, cache_write 3,218, cache_read 13,567 (total input 16,787 tokens); gateway uncached 2.0, cache_write 3,218, cache_read 13,568 (total 16,788 tokens). **The first request is byte-for-byte the same size on both arms.** With ENABLE_TOOL_SEARCH=true the client already defers its tool list, so the fixed prefix is small (about 16.8k tokens) and the gateway has nothing left to shrink. In the CI-fix lane the saving came from the tools block (71.6 KB to 27.5 KB in the cause check); here that block is already deferred on both arms.

Requests 2 and later (cache_write is the new tool result, cache_read is the prefix plus history):

| arm | n requests | cache_write | cache_read | output |
|---|---|---|---|---|
| direct-ts | 57 | 2,395 | 18,308 | 59 |
| gateway | 54 | 2,635 | 17,973 | 50 |

Tool results here are small (an issue body, a label list, a search list), so the gateway has no large result to fold. A triage run is 2 to 4 requests: one to run `label list` and `issue view`, then the answer. The per-request fee is a larger part of the bill than in long agent loops.

Two tasks, per request (usage list is in each artifact, `per-message-usage.json`):

bun-47090, Sonnet r1 (direct-ts run 41193524094, gateway run 41193528536):

| arm | req | uncached | cache_write | cache_read | output | note |
|---|---|---|---|---|---|---|
| direct-ts | 1 | 2 | 0 | 16,769 | 16 | prefix already cached, Bash call |
| direct-ts | 2 | 2 | 3,872 | 16,769 | 17 | writes the new tool result (issue + labels) |
| direct-ts | 3 | 2 | 128 | 20,641 | 109 | answer |
| gateway | 1 | 2 | 0 | 16,770 | 20 | same prefix |
| gateway | 2 | 2 | 3,788 | 16,857 | 60 | same new tool result, answer in one turn |

Here the gateway took 2 turns, direct-ts 3, and was cheaper ($0.0143 vs $0.0182). This is turn-count noise, not byte saving: the cache_write (3,788 vs 3,872) is the same content.

rust-165173, Sonnet r1 (direct-ts run 41193544178, gateway run 41193548448):

| arm | req | uncached | cache_write | cache_read | output |
|---|---|---|---|---|---|
| direct-ts | 1 | 2 | 4,504 | 12,265 | 16 |
| direct-ts | 2 | 2 | 3,253 | 16,769 | 116 |
| gateway | 1 | 2 | 4,504 | 12,266 | 20 |
| gateway | 2 | 2 | 3,648 | 16,770 | 123 |

Identical shape; the gateway wrote slightly more in request 2 and cost more ($0.0256 vs $0.0243). Where the gateway saves: nowhere measurable in this area. Where it does not: prefix (already deferred), tool results (small, same bytes).

## Setup

- Template: the most-starred, anthropics/claude-code `.claude/commands/triage-issue.md` (prompt in `lab/labels/prompt.md`, mirrored; lifecycle labels kept, writes replaced by a final line `{"labels": [...]}`). Tools allowed: `Bash(./scripts/gh.sh:*)`, `Bash(./scripts/edit-issue-labels.sh:*)`; Write, Edit, WebFetch, WebSearch disallowed. `anthropics/claude-code-action` is not used (the key is rejected for the action entrypoint); the prompt and tools are mirrored with `claude -p`. The Opus template model there is opus-4-6; this run used claude-opus-5-5.
- `lab/labels/scripts/gh.py`: read-only `gh` wrapper (label list, issue view N [--comments], issue list, search issues). The target issue shows title, body and author only (no labels, no comments, state open). Other issues and their comments are visible only if created before the target. Any other command is refused. The edit-label script prints a DRY-RUN line and writes nothing to any repo.
- Tasks (`lab/labels/tasks.json`): 12 closed issues, 2 per repo, from godotengine/godot (119k stars), zed-industries/zed (92k), tauri-apps/tauri (112k), oven-sh/bun (96k), rust-lang/rust (121k), microsoft/vscode (194k). Ground truth: labels a human (not the issue author, not a bot) added through a label event and that are still on the issue. Status, bot, priority and team labels are dropped from both truth and prediction (`DROP` list in `lab/labels/extract.py`). Filter: body 300 to 5,000 characters, issue author is a user, at least 2 truth labels.
- Quality: label F1 against the truth, computed by script from the final JSON line, so it needs no hidden arm labels. All 72 answers parsed.
- Smoke pair (bun-47090, tag a1031-labels-smoke): runs 41193268600 and 41193270986, excluded.

## Caveats

- F1 is low on both arms (0.58 Sonnet, 0.74 Opus). Maintainer labels are subjective, so F1 mostly measures label-set taste, and the arms differ little. 12 tasks is small.
- Triage is a short job (2 to 4 requests). Any saving must come from the first request; the gateway did not change it.
- One download of an artifact failed once and was retried; the run itself was fine (godot-124937 gateway r1, run 41193471940).
- Tags: a1031-labels-sonnet-r1, a1031-labels-sonnet-r2, a1031-labels-opus-r1.

## Per pair

| task | tag | direct-ts cost / turns / F1 | gateway cost / turns / F1 | direct-ts run | gateway run |
|---|---|---|---|---|---|
| bun-47006 | opus-r1 | $0.0610 / 3 / 1.00 | $0.0641 / 3 / 1.00 | [41193954571](https://github.com/mksglu/cm-ci-lab/actions/runs/41193954571) | [41193959125](https://github.com/mksglu/cm-ci-lab/actions/runs/41193959125) |
| bun-47090 | opus-r1 | $0.0752 / 3 / 0.86 | $0.0741 / 3 / 0.86 | [41193926479](https://github.com/mksglu/cm-ci-lab/actions/runs/41193926479) | [41193930934](https://github.com/mksglu/cm-ci-lab/actions/runs/41193930934) |
| godot-124937 | opus-r1 | $0.0624 / 3 / 0.57 | $0.0650 / 3 / 0.86 | [41193796672](https://github.com/mksglu/cm-ci-lab/actions/runs/41193796672) | [41193801141](https://github.com/mksglu/cm-ci-lab/actions/runs/41193801141) |
| godot-124950 | opus-r1 | $0.1137 / 3 / 1.00 | $0.1157 / 3 / 0.80 | [41193769456](https://github.com/mksglu/cm-ci-lab/actions/runs/41193769456) | [41193774010](https://github.com/mksglu/cm-ci-lab/actions/runs/41193774010) |
| rust-165127 | opus-r1 | $0.0704 / 4 / 0.50 | $0.0704 / 4 / 0.44 | [41193977284](https://github.com/mksglu/cm-ci-lab/actions/runs/41193977284) | [41193981833](https://github.com/mksglu/cm-ci-lab/actions/runs/41193981833) |
| rust-165173 | opus-r1 | $0.0669 / 4 / 0.62 | $0.0719 / 4 / 0.57 | [41193966430](https://github.com/mksglu/cm-ci-lab/actions/runs/41193966430) | [41193970719](https://github.com/mksglu/cm-ci-lab/actions/runs/41193970719) |
| tauri-16323 | opus-r1 | $0.0612 / 3 / 1.00 | $0.0673 / 3 / 1.00 | [41193897228](https://github.com/mksglu/cm-ci-lab/actions/runs/41193897228) | [41193901896](https://github.com/mksglu/cm-ci-lab/actions/runs/41193901896) |
| tauri-16340 | opus-r1 | $0.0712 / 3 / 0.67 | $0.0715 / 3 / 0.67 | [41193867826](https://github.com/mksglu/cm-ci-lab/actions/runs/41193867826) | [41193872250](https://github.com/mksglu/cm-ci-lab/actions/runs/41193872250) |
| vscode-345099 | opus-r1 | $0.0700 / 3 / 0.33 | $0.0598 / 3 / 0.29 | [41194016408](https://github.com/mksglu/cm-ci-lab/actions/runs/41194016408) | [41194021659](https://github.com/mksglu/cm-ci-lab/actions/runs/41194021659) |
| vscode-345117 | opus-r1 | $0.0753 / 4 / 0.67 | $0.0650 / 4 / 0.40 | [41193987422](https://github.com/mksglu/cm-ci-lab/actions/runs/41193987422) | [41193991578](https://github.com/mksglu/cm-ci-lab/actions/runs/41193991578) |
| zed-66163 | opus-r1 | $0.0888 / 4 / 1.00 | $0.0956 / 3 / 0.80 | [41193857690](https://github.com/mksglu/cm-ci-lab/actions/runs/41193857690) | [41193862401](https://github.com/mksglu/cm-ci-lab/actions/runs/41193862401) |
| zed-66189 | opus-r1 | $0.0941 / 4 / 0.67 | $0.0838 / 3 / 0.80 | [41193827353](https://github.com/mksglu/cm-ci-lab/actions/runs/41193827353) | [41193832459](https://github.com/mksglu/cm-ci-lab/actions/runs/41193832459) |
| bun-47006 | sonnet-r1 | $0.0225 / 2 / 0.67 | $0.0247 / 2 / 0.67 | [41193534244](https://github.com/mksglu/cm-ci-lab/actions/runs/41193534244) | [41193538770](https://github.com/mksglu/cm-ci-lab/actions/runs/41193538770) |
| bun-47090 | sonnet-r1 | $0.0182 / 3 / 0.86 | $0.0143 / 2 / 0.75 | [41193524094](https://github.com/mksglu/cm-ci-lab/actions/runs/41193524094) | [41193528536](https://github.com/mksglu/cm-ci-lab/actions/runs/41193528536) |
| godot-124937 | sonnet-r1 | $0.0210 / 2 / 0.57 | $0.0207 / 2 / 0.50 | [41193466715](https://github.com/mksglu/cm-ci-lab/actions/runs/41193466715) | [41193471940](https://github.com/mksglu/cm-ci-lab/actions/runs/41193471940) |
| godot-124950 | sonnet-r1 | $0.0191 / 2 / 0.80 | $0.0192 / 2 / 0.67 | [41193454901](https://github.com/mksglu/cm-ci-lab/actions/runs/41193454901) | [41193459700](https://github.com/mksglu/cm-ci-lab/actions/runs/41193459700) |
| rust-165127 | sonnet-r1 | $0.0273 / 2 / 0.00 | $0.0379 / 2 / 0.00 | [41193554689](https://github.com/mksglu/cm-ci-lab/actions/runs/41193554689) | [41193559295](https://github.com/mksglu/cm-ci-lab/actions/runs/41193559295) |
| rust-165173 | sonnet-r1 | $0.0243 / 2 / 0.40 | $0.0256 / 2 / 0.22 | [41193544178](https://github.com/mksglu/cm-ci-lab/actions/runs/41193544178) | [41193548448](https://github.com/mksglu/cm-ci-lab/actions/runs/41193548448) |
| tauri-16323 | sonnet-r1 | $0.0217 / 2 / 1.00 | $0.0286 / 3 / 1.00 | [41193514128](https://github.com/mksglu/cm-ci-lab/actions/runs/41193514128) | [41193518589](https://github.com/mksglu/cm-ci-lab/actions/runs/41193518589) |
| tauri-16340 | sonnet-r1 | $0.0229 / 2 / 0.67 | $0.0228 / 2 / 0.67 | [41193503301](https://github.com/mksglu/cm-ci-lab/actions/runs/41193503301) | [41193508011](https://github.com/mksglu/cm-ci-lab/actions/runs/41193508011) |
| vscode-345099 | sonnet-r1 | $0.0250 / 2 / 0.00 | $0.0254 / 2 / 0.00 | [41193574905](https://github.com/mksglu/cm-ci-lab/actions/runs/41193574905) | [41193579148](https://github.com/mksglu/cm-ci-lab/actions/runs/41193579148) |
| vscode-345117 | sonnet-r1 | $0.0251 / 2 / 0.40 | $0.0250 / 2 / 0.40 | [41193564827](https://github.com/mksglu/cm-ci-lab/actions/runs/41193564827) | [41193569169](https://github.com/mksglu/cm-ci-lab/actions/runs/41193569169) |
| zed-66163 | sonnet-r1 | $0.0327 / 2 / 0.80 | $0.0344 / 2 / 1.00 | [41193491418](https://github.com/mksglu/cm-ci-lab/actions/runs/41193491418) | [41193496880](https://github.com/mksglu/cm-ci-lab/actions/runs/41193496880) |
| zed-66189 | sonnet-r1 | $0.0293 / 2 / 0.80 | $0.0261 / 2 / 0.67 | [41193479222](https://github.com/mksglu/cm-ci-lab/actions/runs/41193479222) | [41193484418](https://github.com/mksglu/cm-ci-lab/actions/runs/41193484418) |
| bun-47006 | sonnet-r2 | $0.0119 / 2 / 0.67 | $0.0156 / 3 / 0.67 | [41193662144](https://github.com/mksglu/cm-ci-lab/actions/runs/41193662144) | [41193657572](https://github.com/mksglu/cm-ci-lab/actions/runs/41193657572) |
| bun-47090 | sonnet-r2 | $0.0101 / 3 / 0.86 | $0.0135 / 2 / 0.86 | [41193651687](https://github.com/mksglu/cm-ci-lab/actions/runs/41193651687) | [41193647436](https://github.com/mksglu/cm-ci-lab/actions/runs/41193647436) |
| godot-124937 | sonnet-r2 | $0.0096 / 2 / 0.50 | $0.0100 / 2 / 0.86 | [41193600663](https://github.com/mksglu/cm-ci-lab/actions/runs/41193600663) | [41193595921](https://github.com/mksglu/cm-ci-lab/actions/runs/41193595921) |
| godot-124950 | sonnet-r2 | $0.0084 / 2 / 0.80 | $0.0083 / 2 / 0.80 | [41193589833](https://github.com/mksglu/cm-ci-lab/actions/runs/41193589833) | [41193584819](https://github.com/mksglu/cm-ci-lab/actions/runs/41193584819) |
| rust-165127 | sonnet-r2 | $0.0209 / 2 / 0.00 | $0.0232 / 3 / 0.00 | [41193722628](https://github.com/mksglu/cm-ci-lab/actions/runs/41193722628) | [41193718327](https://github.com/mksglu/cm-ci-lab/actions/runs/41193718327) |
| rust-165173 | sonnet-r2 | $0.0140 / 2 / 0.40 | $0.0162 / 2 / 0.40 | [41193693154](https://github.com/mksglu/cm-ci-lab/actions/runs/41193693154) | [41193688288](https://github.com/mksglu/cm-ci-lab/actions/runs/41193688288) |
| tauri-16323 | sonnet-r2 | $0.0106 / 2 / 1.00 | $0.0112 / 3 / 1.00 | [41193641776](https://github.com/mksglu/cm-ci-lab/actions/runs/41193641776) | [41193637596](https://github.com/mksglu/cm-ci-lab/actions/runs/41193637596) |
| tauri-16340 | sonnet-r2 | $0.0252 / 1 / 0.67 | $0.0120 / 2 / 0.50 | [41193631797](https://github.com/mksglu/cm-ci-lab/actions/runs/41193631797) | [41193627712](https://github.com/mksglu/cm-ci-lab/actions/runs/41193627712) |
| vscode-345099 | sonnet-r2 | $0.0144 / 2 / 0.00 | $0.0154 / 2 / 0.00 | [41193763436](https://github.com/mksglu/cm-ci-lab/actions/runs/41193763436) | [41193759079](https://github.com/mksglu/cm-ci-lab/actions/runs/41193759079) |
| vscode-345117 | sonnet-r2 | $0.0142 / 2 / 0.40 | $0.0141 / 2 / 0.40 | [41193752513](https://github.com/mksglu/cm-ci-lab/actions/runs/41193752513) | [41193747217](https://github.com/mksglu/cm-ci-lab/actions/runs/41193747217) |
| zed-66163 | sonnet-r2 | $0.0227 / 2 / 0.80 | $0.0217 / 2 / 0.80 | [41193622237](https://github.com/mksglu/cm-ci-lab/actions/runs/41193622237) | [41193617668](https://github.com/mksglu/cm-ci-lab/actions/runs/41193617668) |
| zed-66189 | sonnet-r2 | $0.0185 / 2 / 0.80 | $0.0226 / 3 / 0.67 | [41193612005](https://github.com/mksglu/cm-ci-lab/actions/runs/41193612005) | [41193607381](https://github.com/mksglu/cm-ci-lab/actions/runs/41193607381) |

F1 difference gateway minus direct-ts (sonnet), task-resampled: -0.015 (95% CI -0.056 to +0.029)

F1 difference gateway minus direct-ts (opus), task-resampled: -0.034 (95% CI -0.112 to +0.047)

Request 1, mean over all 36 direct-ts runs: uncached 2.0, cache_write 3218, cache_read 13567, total input 16787 tokens

Request 1, mean over all 36 gateway runs: uncached 2.0, cache_write 3218, cache_read 13568, total input 16788 tokens
Requests 2+ , direct-ts: n=57, mean cache_write 2395, cache_read 18308, output 59
Requests 2+ , gateway: n=54, mean cache_write 2635, cache_read 17973, output 50
