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

### `youtube-learn`

Lets Claude actually learn from a YouTube video instead of just its title.

YouTube doesn't expose a video's transcript or audio to the page-fetch tool — scraping the
URL returns only the title, so Claude is effectively blind and deaf to the content. This skill
closes that gap by driving `yt-dlp` + `ffmpeg`:

- **Keyframes** — captures frames at scene changes *plus* a forced frame every N seconds, so
  slides, charts, demos, and faces are all visible (and won't be missed during slow sections).
- **Transcript** — uses YouTube's own captions when available (instant), and falls back to local
  Whisper transcription only when a video has none.

It bundles everything into a `manifest.md` that interleaves each keyframe image with the
transcript spanning that moment, which Claude then reads (images included) to summarize, analyze,
or fact-check the video — citing `[mm:ss]` timestamps.

Triggers on sharing a YouTube link with an analysis ask — e.g. *"what can you learn from this
video?"* or *"summarize this YouTube video."* Requires `yt-dlp` and `ffmpeg` on `PATH`.

### `lean-search`

Keeps web research token-cheap and out of the main context window.

Web search has two costs that need different fixes: raw results **bloat the main
context** (fix: isolate the search inside a subagent that returns only a
conclusion) and **run up the bill** (fix: search before fetching, fetch with a
tight extraction prompt, never fetch twice). `lean-search` codifies the flow —
snippets-first, fetch narrow, and a clear inline-vs-subagent threshold so a
one-page lookup doesn't spawn a whole extra billed context.

Triggers before any WebSearch/WebFetch or web-research dispatch.

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
