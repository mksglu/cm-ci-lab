# CI areas, clean cross-area analysis (2026-10-31)

Goal: where does the context-mode gateway save money when an AI agent runs headless in CI, and where does it not. Nothing here is published. Inputs: the seven clean lane runs of 2026-10-31 and the lab docs in this folder. New model spend for this analysis: $0 (two dry-runs only, which call no model).

History: the first area benches of this day were invalid, because the lab tenant `t_ci_lab_1` was paused at 2026-10-31 10:29:57 UTC and the gateway arm ran as plain pass-through. Every row below is from the clean re-run (tags `c1031-*`) except the one row marked pre-pause. Per round, `used_paused` stayed at 1518 before and after, and request 1 was 30 to 42 percent smaller on the gateway arm.

Bar (fixed in advance): task-resampled CI upper bound < 0, quality not lower, 0 errors, every round valid. Pairs are (task, round). Cost change = exp(mean paired log-ratio gateway/baseline) - 1. CI = bootstrap that resamples tasks (10,000 resamples, seed 1). Net per run = (mean direct-ts - mean gateway) - $0.0009 x mean gateway requests per run.

## 1. Table: area x model

Baseline is `direct-ts` (direct API + ENABLE_TOOL_SEARCH) unless the row says `direct`.

| area | model | pairs | cost change | 95% CI | cheaper pairs | quality (gateway vs baseline) | net per run | valid | passed |
|---|---|---|---|---|---|---|---|---|---|
| CI-failure fix (PRE-PAUSE, valid) | Sonnet 5.5 | 24 | -22.3% | -29.5 .. -13.7 | n/a in the lane note | pass 23/24 vs 23/24 | +$0.0041 | yes | yes |
| CI-failure fix | Opus 5.5 | 24 | -16.8% | -23.6 .. -10.0 | 21/24 | pass 24/24 vs 24/24 | +$0.0128 | yes | yes |
| PR review, own prompt | Sonnet 5.5 | 24 | -19.0% | -26.4 .. -11.5 | 21/24 | judge 6.33 vs 6.46 (diff -0.13, CI -0.54..+0.29), 21 ties | +$0.0092 | yes | yes |
| PR review, own prompt | Opus 5.5 | 12 | -8.5% | -17.8 .. +2.1 | 8/12 | judge 7.00 vs 7.17, 11 ties | +$0.0102 | yes | NO (CI upper bound above 0) |
| PR review, official claude-code-action | Sonnet 5.5 | 24 | -11.6% | -20.8 .. -2.2 | 16/24 | judge diff 0.00 | +$0.0047 | yes | yes |
| PR review, official claude-code-action | Opus 5.5 | 12 | -13.6% | -22.4 .. -3.9 | 7/12 (recomputed from run JSON) | judge diff +0.08 | +$0.0238 | yes | yes (one round) |
| PR review, official action, baseline `direct` | Sonnet 5.5 | 12 | -19.9% | -32.0 .. -7.5 | 9/12 (recomputed) | judge diff -0.08 | +$0.0094 | yes | yes (one round) |
| @-mention fix | Sonnet 5.5 | 24 | -22.7% | -28.3 .. -16.1 | 22/24 | pass 16/24 vs 16/24 | +$0.0125 | yes | yes |
| @-mention fix | Opus 5.5 | 12 | -20.3% | -30.2 .. -8.5 | 10/12 | pass 7/12 vs 8/12 (1 discordant pair, McNemar p=1.0) | +$0.0375 | yes | yes (one round, one test lower) |
| issue triage and labels | Sonnet 5.5 | 24 | -14.4% | -20.5 .. -8.6 | 18/24 | F1 0.579 vs 0.588 (diff -0.010, CI -0.040..+0.029) | +$0.0016 | yes | NO (F1 point estimate lower) |
| issue triage and labels | Opus 5.5 | 12 | -14.4% | -23.4 .. -3.4 | 9/12 | F1 0.662 vs 0.670 (diff -0.008, CI -0.085..+0.071) | +$0.0075 | yes | NO (F1 point estimate lower) |
| issue dedupe | Sonnet 5.5 | 24 | -24.1% | -48.2 .. +2.6 | 16/24 | top-3 hit 19/24 vs 19/24 | +$0.0215 | yes | NO (CI upper bound above 0) |
| release notes | Sonnet 5.5 | 24 | -13.9% | -20.1 .. -8.4 | 19/24 | judge 6.42 vs 6.67 (diff -0.25, CI -0.54..0.00) | +$0.0080 | yes | NO (quality point estimate lower, CI touches 0) |

Reading it. Cost is lower in every row, and the CI upper bound is below 0 in 11 of 13 rows. Five rows (four areas) do not pass: PR review Opus (wide CI, 12 pairs, one round), dedupe (one task drives the headline: without bun-36967 the change is -11.6%, CI -26.9..+10.2), labels (F1 not significantly lower, but the point estimate is lower on both models), and release (judge diff -0.25, CI upper bound 0.00). Three Opus rows and the `direct` row have one round; their CIs are wide. The judge for PR review and release is Sonnet 5.5, the same model as the Sonnet runs. CI values are from each lane doc; my recompute from the run JSON agrees within 0.6 points (PR review Opus -18.0..+1.9, dedupe -47.6..+3.0).

Net note. Dedupe net uses the lane's 28.0 requests per run (main agent plus subagents). The per-message anatomy below counts main-agent messages only (11.2 gateway), so it is not the same denominator.

## 2. Where the gateway saves, and where it does not

Source: `lab/ci-areas/anatomy.py` over the per-message usage in the run JSON. Units are input-side cost units: uncached 1.0, cache write 1.25, cache read 0.1. Output is left out because the gateway arm streams `output_tokens` 0 on every message. Saved units are direct-ts minus gateway, per run.

| area / model | request 1 tokens | requests per run | saved units | from request-1 write | from later writes | from cache reads |
|---|---|---|---|---|---|---|
| PR review Sonnet | 23,639 -> 15,852 (-33%) | 2.5 -> 2.2 | 5,821 | 3,746 (64%) | -139 (-2%) | 2,215 (38%) |
| PR review Opus | 23,686 -> 15,899 (-33%) | 5.7 -> 6.7 | 4,859 | 3,734 (77%) | -833 (-17%) | 1,959 (40%) |
| review action Sonnet | 24,049 -> 15,917 (-34%) | 2.2 -> 2.3 | 5,167 | 3,120 (60%) | 446 (9%) | 1,602 (31%) |
| review action Opus | 24,096 -> 15,964 (-34%) | 5.9 -> 5.9 | 9,695 | 3,271 (34%) | 1,272 (13%) | 5,153 (53%) |
| dedupe Sonnet (main agent) | 16,655 -> 10,556 (-37%) | 9.5 -> 11.2 | 4,961 | 3,184 (64%) | -591 (-12%) | 2,368 (48%) |
| CI-fix Opus | 18,661 -> 10,864 (-42%) | 7.0 -> 7.0 | 6,674 | 3,137 (47%) | -1,396 (-21%) | 4,933 (74%) |

Mention (all 72 runs, from the lane): request 1 total 20,155 -> 12,358 (-38.7%), cache_write 5,629 -> 2,617, cache_read 14,524 -> 9,249. Later requests: cache_write 965 vs 935 (same), cache_read 26,990 -> 17,110 (-36.6%). Requests per run 9.5 -> 8.9. Labels (lane): request 1 16,771 -> 10,671 (Sonnet), about 2.2 requests per run.

Where it saves:
- The fixed prefix. Request 1 is 6.1k to 8.1k tokens smaller on every area. That cuts the first cache write by about 3.1k to 3.7k units, and it cuts every later cache read (31% to 74% of the saving).
- Fewer requests only in mention (9.5 -> 8.9) and PR review Sonnet (2.5 -> 2.2). It is not a general saving.

Where it does not:
- New tool results. Later cache writes are 35% to 46% of the gateway arm's input units, and they are equal or higher on the gateway arm in four of six rows (-0.7% to -21% of the saving; CI-fix Opus writes 7,856 vs 6,749 tokens on later requests). Those bytes are the same in both arms.
- Request count can rise: PR review Opus 5.7 -> 6.7, dedupe 9.5 -> 11.2 main-agent requests.
- Short runs. Labels takes about 2.2 requests per run, so the $0.0009 per-request fee takes 55% of the gross saving ($0.0036 gross, $0.0020 fee, net $0.0016). Dedupe: 28.0 requests x $0.0009 = $0.0252, 54% of a $0.0468 gross saving.
- Output tokens. Not shrunk, and not measurable from the stream on the gateway arm.
- The first request still bills 472 to 499 uncached tokens on the gateway arm against 2 to 4 on direct-ts (PR review, dedupe, CI-fix Opus, labels). That is 1.1% to 4.3% of a run's input units (dedupe: 3,249 vs 55 uncached tokens per run, 7%). See lever 2.
- Tool mix. In all four areas the gateway arm's runs are almost all `Bash` (CI-fix Opus: 143 Bash and nothing else, against 114 Bash, 14 Read, 12 Grep, 3 Edit on direct-ts). The cause is not known; I did not test it (lever 3).

## 3. The CI data path: are folded bytes reachable? (checked 2026-10-31)

Method. `lab/dry-probe.py` (arm `gateway-dry`, header `x-cm-dry-run: 1`, no model call, nothing billed) sends a 64,458 B real pytest log from `requests` as a Bash tool_result, with the CI headers that `ci init` writes. I extended the probe to print the forwarded `tools`, the `system`, and the pointer text. Runs: `41204858034` and `41205013107` of the `triage` workflow (tags `c1031-dry-analysis`, `c1031-dry-analysis2`). Tenant stayed in full mode (`used_paused` 1518).

Result, case A (log is the last message) and case B (log followed by 8 small exchanges), identical:
- The log is folded: 64,458 B -> 6,586 B in the forwarded body (head, a marker, tail). Forwarded body 7,567 B.
- The marker says: "58314 of 64458 B are NOT shown above ... All 64458 original bytes are archived verbatim. If you need anything from the omitted middle, call context-mode-search {"q":"full output","docid":"context-mode-toolcap-8d6f5d3d-64458","offset":0} ... Do NOT re-run the command and do NOT say the data is unavailable."
- The forwarded `tools` list is `['Bash', 'Read']`, exactly what the client sent. `context-mode-search` is not offered. `system` has no mention of it.

So the pointer names a tool that the model is not offered. Code path: `cmCiToolHidden` (src/gateway/memory-egress.ts:210) returns true for `context-mode-search` when `ci`, and `proxy-hot-path.ts:3693` filters it out of `injected`. The server side still would run a docid read: `proxy-messages.ts:653` allows `context-mode-search` on CI when `input.docid` is set or `q` is a pointer id, and `cmEdgeToolNames` includes it. But a model that is not offered a tool has no reason to emit it, and the marker also forbids re-running the command. On CI the folded middle is unreachable by design intent, and the model is told it is not. The fold is 58 KB here; the saving is real, but the data loss is silent in practice. This is lever 1.

Not tested: whether the model ever emits the hidden tool name by itself from the marker text (a live run would show it); I only proved the offer.

## 4. Levers (ranked, for the areas that did not pass)

Constraints held for all: no compaction or summary of user context, never drop data silently, cached prefix byte-identical across turns, Rust/Wasm for body work, Worker CPU near zero and 128 MB. Percentages are estimates from section 2, stated with their basis; none is measured.

1. Make a fold readable on CI (test-first, gateway-only). Expected cost effect: +0.4% to +0.7% (an offered docid-only tool adds roughly 80 tokens to the prefix, my estimate, not measured; 1,000 prefix tokens = 4.6% to 8.3% of input units). Expected quality effect: removes the silent loss on release and labels (quality rows that did not pass) and any area with a result over 24,576 B. Possible side gain: fewer re-asked requests (PR review Opus 6.7 vs 5.7, dedupe 11.2 vs 9.5); a hypothesis, not shown. Design:
   - RED 1: on CI headers, the forwarded `tools` contains a tool the marker names (`context-mode-search`), with a docid-only schema (`docid`, `offset`, `limit`; no free-text `q`). It fails today.
   - RED 2: the tools array is byte-identical on turn 1 and turn N (prefix-stability e2e already exists for this).
   - RED 3: a free-text `q` call on CI is still refused (existing `_ciFreeSearch` branch), and archive rows stay filtered by memory-off rules.
   - RED 4: every marker minted on a CI turn names an offered tool.
   - GREEN: in `cmCiToolHidden`, stop hiding `context-mode-search` on CI; add the docid-only schema variant for CI; keep `_ciFreeSearch` as is. Touches memory-egress.ts and proxy-hot-path.ts only.
   - Verify: dry-probe shows the tool; then 2 live `claude -p` runs (a big log) read the middle back via docid. Real harness, not source shape.
2. Cache the 470 to 500 uncached tokens of request 1. Evidence: gateway request 1 has 472 to 499 uncached tokens, direct-ts has 2 to 4, in PR review, dedupe, labels (482 vs 4) and CI-fix Opus. Expected: labels -4.3% (Sonnet), -2.9% (Opus); dedupe about -7% (every subagent start pays it); PR review Sonnet -2.3%; CI-fix Opus -2.0%; PR review Opus -1.1%. Basis: 0.9 x uncached tokens / gateway units. The cause is not known (likely a block the gateway injects after the last cache breakpoint); find it with a dry-run diff of the body before and after the gateway, then move the breakpoint. Prefix stays byte-identical.
3. Later-turn cache-write parity. Evidence: later writes are 35% to 46% of gateway input units and are higher on the gateway arm in four of six rows. If the gateway matched direct-ts: CI-fix Opus -6.2% (1,396 units), PR review Opus -2.1%, dedupe -1.5%, PR review Sonnet -0.7%. Two candidate causes, both untested: the gateway changes an earlier message between turns (prefix miss), or the Bash-only tool mix gives bigger results. Test: capture turn N and N+1 bodies with `lab/capture.py` and diff the common prefix; replay one run with the real Claude Code tool list.
4. Client tool allow-list header in `ci init` (owner_decision). Expected per 1,000 prefix tokens removed: -4.6% to -8.3% per area (CI-fix Opus 8.3%, PR review Sonnet 7.3%, dedupe 5.7%). The size of the client tool block in request 1 is not measured; measure it first by summing bytes per block on a captured request 1. It changes which tools the model can use, so the owner decides.
5. Lower the tail fold cap from 24,576 B (owner_decision). Evidence: writes over 3k tokens on later requests are 32% (PR review Sonnet), 30% (review action Sonnet), 25% (review action Opus), 22% (PR review Opus), 16% (dedupe), 10% (CI-fix Opus) of gateway input units. Ceiling if half of that were folded: about -16%, -15%, -13%, -11%, -8%, -5%. This is a ceiling, not an expectation: a smaller view makes the model ask for the middle (more requests). It changes what the model sees, and it is only safe after lever 1.
6. Fee shape (owner_decision, pricing). Evidence: the per-request fee takes 54% to 55% of the gross saving in labels and dedupe. Charging per Claude turn instead of per request is +$0.0428 vs +$0.0215 net on dedupe (lane figure, 4.5 turns vs 28 requests). Half the fee on labels Sonnet raises net from $0.0016 to $0.0026 (+63%). It does not change the cost CI, so it does not move any area across the bar; it moves net.

What does not move an area across the bar: more rounds on PR review Opus and dedupe will narrow the CI but cannot change the point estimate. Run them after levers 1 to 3 land.

## 5. Caveats

- Judges for PR review and release are Sonnet 5.5, the same model that wrote the Sonnet outputs. A human read of the non-tie pairs is stronger.
- Opus rows and the `direct` row have one round each.
- Four mention tasks (chalk, fd, loguru, tqdm) fail on both arms in every round on both models; not investigated.
- Per-message usage sums do not match `total_cost_usd` exactly in the PR review lane; cause not found. Savings units in section 2 are my own model (1.0 / 1.25 / 0.1), not billed dollars.
- No key was printed or committed.

## Files

- `lab/ci-areas/anatomy.py`: section 2 numbers.
- `lab/dry-probe.py`: prints forwarded tools and pointer text (section 3).
- Dry-run workflow runs: 41204858034, 41205013107 (mksglu/cm-ci-lab, workflow `triage`).
- Lane docs: `docs/pr-review-bench-1031.md`, `review-action-bench-1031.md`, `mention-bench-1031.md`, `labels-bench-1031.md`, `dedupe-bench-1031.md`, `release-bench-1031.md`, `opus-bench-1031.md`, `triage-bench-1031.md` (pre-pause CI-fix Sonnet row).
