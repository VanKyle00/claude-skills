---
name: rethink
description: Use when you have an existing solution, design, draft, plan, or code structure and need genuinely different approaches — not tweaks or variations. Triggers: feeling anchored, "try another way", "rethink this", a solution that works but feels uninspired, or an approach that keeps hitting the same wall.
---

# Rethink

## Overview

A different approach must **abandon a load-bearing assumption** of the current one.
Anything that keeps all the original's assumptions is a *variation*, not an
*alternative*. This skill is for escaping a frame you are already inside.

NOT for greenfield ideation (use `brainstorming`). NOT for polishing a solution
already verified correct (don't churn working code).

## The Iron Law

```
NO ALTERNATIVE COUNTS UNLESS IT DROPS A LOAD-BEARING ASSUMPTION OF THE ORIGINAL.
```

If you can't name the assumption a candidate drops, it's a variation — discard it.

## The Process

### 1. Strip to the goal
State what success means in one sentence, with zero mention of *how* the current
solution does it. ("The user needs to ___.") This is the target every alternative
must hit; the current solution is just one path to it.

### 2. Expose the current frame
List the load-bearing assumptions the current approach bakes in — the choices so
ingrained they feel like the problem itself (e.g. "data is relational", "the user
reads top-to-bottom", "work happens on request", "it's a form"). For each, ask:
*what if this weren't true?*

### 3. Diverge — apply at least 3 operators, each yielding a different family
- **Invert** — reverse a core assumption.
- **Drop the constraint** — what if the hardest limit simply vanished?
- **Change the primitive** — a different fundamental building block (form→conversation, table→graph, request/response→stream, page→canvas).
- **Borrow a domain** — how would a game designer / a spreadsheet / biology / a physical store solve this?
- **Go to extremes** — the radically minimal version, and the radically maximal version.
- **Move the work** — shift who/when/where it happens (user↔system, client↔server, build-time↔runtime, sync↔async).

### 4. Distinctness gate
For each candidate, name the assumption it drops. Two candidates that drop the
*same* assumption and look alike are one idea wearing two hats — merge them or push
one further. Aim for 2–4 survivors that are genuinely different *in kind*.

### 5. Contrast and recommend
For each survivor: what it makes **easy** that the original made hard, and what it
**sacrifices**. Then recommend one (or a synthesis) tied to the actual goal and
constraints — explicitly say why it beats the original, or honestly conclude the
original wins after a real fight.

## Red Flags — rationalizations to reject

| Thought | Reality |
|---|---|
| "These options are all distinct." | If they drop the same assumption, it's one idea in three outfits. Name the dropped assumption for each. |
| "The original is basically fine." | Maybe — but defending it *before* diverging is anchoring. Earn that verdict in step 5, not step 0. |
| "I already considered alternatives." | Considering ≠ generating. Actually run the operators. |
| "A fresh approach is riskier." | The gate is *distinctness*, not adoption. Generate freely; judge risk in step 5. |
| Changed colors / params / wording / file layout. | Surface change. Did the *organizing principle* move? If not, keep going. |
