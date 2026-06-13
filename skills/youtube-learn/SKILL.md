---
name: youtube-learn
description: >-
  Use when the user shares a YouTube link (youtu.be / youtube.com) and wants you to learn from,
  summarize, analyze, explain, fact-check, react to, or pull information out of the video's ACTUAL
  content — talks, tutorials, lectures, reviews, demos, stock/market or news videos. Triggers on
  "what can you learn from this video", "summarize this YouTube video", "watch this", "what does
  this video say", or a bare video URL paired with an analysis ask. The page itself only exposes
  the title; this skill captures scene-change + interval keyframes and the transcript so you can
  read what is shown and said.
---

# youtube-learn

## Overview
YouTube does not expose a video's transcript or audio to the fetch tool — scraping the page
returns only the title. This skill turns a YouTube URL into things you *can* consume: keyframe
images (so you can see slides, charts, demos, faces) plus a timestamped transcript (so you can
read what was said), bundled into one `manifest.md`.

## When to use
- The user wants the substance of a specific YouTube video, not just its metadata.
- **Skip it** for pure-metadata questions ("who posted this?"), or music videos where the audio
  isn't informational.

## Run it
From this skill's directory:

```bash
python scripts/extract.py "<youtube_url>"
```

Useful flags (`--help` for all):
- `--interval 20`   force a frame at least every N seconds (safety net for slow-changing slides)
- `--scene 0.4`     scene-change sensitivity (lower = more frames)
- `--max-frames 40` cap total frames (evenly subsampled if exceeded)
- `--height 720`    download resolution cap
- `--no-whisper`    skip the local transcription fallback

It writes to `~/Downloads/yt-learn/<video-id>/` and prints the path to `manifest.md`.

## Then consume the output
1. **Read `manifest.md`** — it interleaves each keyframe with the transcript spanning that moment.
2. **Read the referenced `frames/*.jpg`** images — you are vision-capable, so actually open them.
3. Answer from frames **and** transcript together. Cite `[mm:ss]` timestamps from the manifest.

## Notes & troubleshooting
- **Transcript source** appears in the manifest: `youtube captions` (default, instant) or
  `local whisper` (fallback when a video has none — first run downloads a ~140 MB model and needs
  `faster-whisper`, which the script tries to `pip install` automatically; on success it transcribes
  on CPU, which is slow for long videos).
- **Long videos**: raise `--interval` and/or lower `--max-frames` to keep the frame set readable.
- **Download fails**: age/region-restricted or members-only videos may be inaccessible to yt-dlp.
- **Requirements**: `yt-dlp` and `ffmpeg` on `PATH` (or set the `YT_DLP` / `FFMPEG` env vars). No
  third-party Python packages are needed unless the Whisper fallback runs.
