---
name: lean-search
description: >-
  Use BEFORE running WebSearch or WebFetch, or before dispatching an agent to
  research on the web — keeps web research token-cheap and out of the main context
  window. Triggers: any task needing current/external info, "search the web", "look
  this up", "research X online", fetching docs/articles, or noticing web results
  are bloating the conversation.
---

# Lean Search

## Overview

Web research has two distinct costs, and they need different fixes:

- **Main context-window bloat** — raw search results and fetched pages pile up
  in the conversation, degrading quality and pushing toward limits. Fix:
  **isolation** (do the searching inside a subagent that returns only a
  conclusion).
- **Total billed tokens** — every token in every context bills. Fix:
  **frugality** (search before fetching, fetch narrowly, never fetch twice).

Isolation and frugality are different dials. A subagent protects the main
context but does NOT lower the bill — both contexts bill, and an unnecessary
subagent adds a whole extra context. So: isolate when the research is big,
stay frugal always.

NOT for the heavyweight `deep-research` skill's job (multi-source, adversarially
verified reports) — this is the everyday "I need a fact / a doc / a few sources"
path.

## How the tools actually bill

| Tool | What lands in context | Cost |
|---|---|---|
| **WebSearch** | Titles + URLs + **snippets only** — never page bodies. Scope with `allowed_domains` / `blocked_domains` (not both at once). | Cheap. The snippets are often the whole answer. |
| **WebFetch** | Only the extract its small model produces from **your `prompt`** — the page is lossy-compressed through that prompt. Big pages are truncated; results cached ~15 min. | The `prompt` is the throttle. Vague prompt = big extract. Tight prompt = tiny extract. |
| **Subagent** doing the search | Only its **final summary** reaches the parent; raw results stay in its context. | Protects the parent's context window; both contexts still bill. |

## The flow

### 1. Search first — read the snippets
Run WebSearch before any fetch. Scope it with `allowed_domains` when you know
the authoritative source (e.g. `docs.python.org`, a specific vendor's docs) so
you get fewer, better results. **Read the snippets.** If they answer the
question — stop. This is the "only look at headers" path, and it's the cheapest
one. Most lookups end here.

### 2. Need a page? Pick inline vs. isolated — by expected fetch count

- **1 known URL, 1 specific question → fetch INLINE.** Spawning a subagent for
  a single page adds a whole context to the bill for no context-window benefit
  worth it. Just WebFetch with a tight prompt (step 3).
- **Multiple pages / exploratory / "research X" / unknown how many sources →
  ISOLATE.** Dispatch ONE subagent to do all the searching and fetching; it
  returns a short, cited synthesis. The main thread pays only for that summary
  (step 4).

Rough line: **≤1–2 fetches → inline; more, or unknown → subagent.**

### 3. WebFetch discipline (always)
- **One specific extraction prompt per fetch.** Ask for *the thing*, not the
  page: "Return only the default value of `timeout` and the version it changed
  in" — not "summarize this page." The prompt is what bills into context.
- **Don't fetch what a snippet already gave you.**
- **Don't fetch the same URL twice** (it's cached ~15 min, and you don't need
  it again).
- **Never** ask it to dump the whole page or "read the full doc into context."

### 4. Subagent discipline (when isolating)
Isolation alone protects the context window but can quietly run up the bill if
the subagent fetches everything. Instruct it to be frugal too:
- Snippets-first; fetch a page only when snippets fall short.
- **Cap the fetches** (e.g. "fetch at most 3 pages").
- Tight extraction prompt per fetch.
- **Return a short, cited answer** (e.g. "≤150 words + source URLs"), not a
  transcript of what it read.

### 5. Reuse, don't re-run
Already have search results or a fetched extract? Use them. Re-searching to
"double-check" re-bills for information you already hold.

## Red Flags — rationalizations to reject

| Thought | Reality |
|---|---|
| "I'll just fetch the page to be safe." | The snippet probably had it. Fetching is the expensive step — earn it. |
| "Fetch and summarize this page." | Vague prompt → big extract. Name the specific fact you need. |
| "Spawn a subagent for this quick lookup." | One page? Fetch inline. A subagent is a whole extra billed context. |
| "Let me re-search to confirm." | You already have results. Re-running re-bills. |
| "Read the whole doc into context." | Never. Extract the section with a targeted prompt. |
| "Searching in the main thread is fine, it's just one query." | One query is — but one fetch isn't, and they multiply. Isolate once it's more than a peek. |
