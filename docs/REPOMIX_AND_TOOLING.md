# Repomix + tooling references

Small, additive workflow utilities. Nothing here is wired into CI, hooks, or the data pipeline.

## repomix — pack the repo into one AI-friendly file

**Purpose:** produce a single packed file of the codebase + structural data so it can be handed to an external LLM (or a fresh Claude Code session) as one artifact.

### One-line command (regenerate the pack)

```
npx repomix@1.15.0
```

Run it from the repo root. It reads `repomix.config.json` and writes **`repomix-output.xml`** (gitignored — regenerate on demand; not committed).

### Prerequisite — Node.js

⚠️ **repomix needs Node.js, which is not currently installed on this machine.** Install it once before running the command above:
- Easiest: the official installer at https://nodejs.org (LTS), or
- Homebrew: `brew install node`

Then `npx repomix@1.15.0` works (npx fetches the pinned version on demand — no `package.json`, no dependency added to the repo).

### What the config does (`repomix.config.json`)

- **Output:** XML (LLM-optimised, repomix's default) → `repomix-output.xml`.
- **Scope:** code (Python / HTML / JS / CSS) + docs + the **structural** data (registries, `material_nodes.json`, `dependency_edges.json`, `home.json`, index summaries). The **bulk data dumps are excluded** (price feeds, funding rounds, investor list, enriched equities, exports/reports, news/research, CSV/XLSX/PDF/PNG) to keep the pack high-signal and small.
- **Security check: ON** (`security.enableSecurityCheck: true`). repomix runs Secretlint over every file, so no API keys or secrets leak into the pack. `.env`, `archive/`, and `.claude/` are excluded via `.gitignore` anyway.

To change what's packed, edit the `ignore.customPatterns` list in `repomix.config.json`.

---

## Reference (not vendored): awesome-claude-code

- **https://github.com/hesreallyhim/awesome-claude-code** — directory of Claude Code skills/plugins. **Consult when a concrete tooling need arises; do not adopt speculatively.** Recorded as a reference only — not cloned, submoduled, or copied.

### Standing filter for workflow tools

A tool earns adoption only if it **eases the work actually done** — content drafting, the Claude Code relay, sourcing/research. It does **not** earn adoption if it solves an engineering-throughput problem we don't have (agent fleets, orchestration, large-scale automation). Prefer **official / simple** tools over community grab-bags; be wary of anything that installs hooks.
