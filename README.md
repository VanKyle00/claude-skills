# claude-skills

A collection of personal [Claude Code](https://docs.claude.com/en/docs/claude-code) skills.

## Skills

### `rethink`

Forces genuinely different approaches to an **existing** solution, design, draft, or
plan — not tweaks or restyled variations.

LLMs anchor hard on whatever already exists: asked to "try another way," they tend to
produce cosmetic variants inside the same paradigm (a form becomes a slightly different
form). `rethink` defeats that anchoring with one rule — its **Iron Law**:

> No alternative counts unless it drops a load-bearing assumption of the original.

It walks through stripping the problem to its goal, exposing the current approach's
hidden assumptions, diverging with concrete operators (invert, drop-the-constraint,
change-the-primitive, borrow-a-domain, go-to-extremes, move-the-work), passing a
distinctness gate, then contrasting the survivors and recommending one.

Invoke it explicitly — e.g. *"use the rethink skill"* or *"rethink this."*

## Installing

Copy a skill folder into your Claude Code skills directory:

```bash
# macOS / Linux
cp -r skills/rethink ~/.claude/skills/rethink
```

```powershell
# Windows (PowerShell)
Copy-Item -Recurse skills\rethink "$env:USERPROFILE\.claude\skills\rethink"
```

The skill is picked up the next time Claude Code starts.
