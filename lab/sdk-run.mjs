// Claude Agent SDK (TypeScript) run: writes every message as JSON lines to argv[2]. Base URL and headers come from
// the environment (ANTHROPIC_BASE_URL, ANTHROPIC_CUSTOM_HEADERS), as for any Claude Code process.
import { query } from "@anthropic-ai/claude-agent-sdk";
import { writeFileSync } from "node:fs";
const out = [];
for await (const m of query({ prompt: process.env.PROMPT, options: { model: process.env.LAB_MODEL || "haiku", maxTurns: 30,
  allowedTools: ["Bash", "Read", "Edit", "Write", "Glob", "Grep"], permissionMode: "acceptEdits" } })) out.push(m);
writeFileSync(process.argv[2], out.map((m) => JSON.stringify(m)).join("\n") + "\n");
const r = out.findLast((m) => m.type === "result") || {};
console.log(JSON.stringify({ subtype: r.subtype, is_error: r.is_error, num_turns: r.num_turns, total_cost_usd: r.total_cost_usd }));
