#!/usr/bin/env python3
"""Turn a YouTube video into keyframes + a timestamped transcript that Claude can read.

Pipeline:  yt-dlp (download + captions)  ->  ffmpeg (scene-change + interval keyframes)
        -> transcript (YouTube captions first, local Whisper fallback)  ->  manifest.md

Stdlib only for the default (captions) path. `faster_whisper` is imported lazily, and only
when a video has no captions, so the common path needs no third-party packages.

Usage:
    python extract.py "<youtube_url>" [--scene 0.4] [--interval 20] [--max-frames 40]
                                      [--height 720] [--width 960] [--out DIR] [--no-whisper]
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

VIDEO_EXTS = (".mp4", ".mkv", ".webm", ".m4v", ".mov")


def find_exe(name, candidates=()):
    p = shutil.which(name) or shutil.which(name + ".exe")
    if p:
        return p
    for c in candidates:
        if Path(c).exists():
            return str(c)
    return None


def locate_tools():
    home = Path.home()
    ytdlp = os.environ.get("YT_DLP") or find_exe(
        "yt-dlp", [home / "AppData/Local/Programs/yt-dlp.exe"]
    )
    ffmpeg = os.environ.get("FFMPEG") or find_exe(
        "ffmpeg", [home / "AppData/Local/Microsoft/ffmpeg.exe"]
    )
    missing = [n for n, v in (("yt-dlp", ytdlp), ("ffmpeg", ffmpeg)) if not v]
    if missing:
        sys.exit(
            f"ERROR: required tool(s) not found: {', '.join(missing)}. "
            f"Install them or set the YT_DLP / FFMPEG env vars."
        )
    return ytdlp, ffmpeg


def run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)


def fmt_ts(seconds):
    seconds = int(seconds or 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"


def get_meta(ytdlp, url):
    r = run([ytdlp, "--dump-single-json", "--skip-download", "--no-warnings", url])
    if r.returncode != 0:
        sys.exit(f"ERROR: yt-dlp metadata failed:\n{r.stderr.strip()[:800]}")
    info = json.loads(r.stdout)
    return {
        "id": info.get("id", "video"),
        "title": info.get("title", ""),
        "uploader": info.get("uploader") or info.get("channel", ""),
        "duration": info.get("duration") or 0,
        "url": info.get("webpage_url", url),
    }


def download(ytdlp, url, height, workdir):
    fmt = f"bv*[height<={height}]+ba/b[height<={height}]/b"
    r = run([
        ytdlp, "-f", fmt,
        "--write-subs", "--write-auto-subs", "--sub-langs", "en.*",
        "--sub-format", "vtt", "--no-warnings",
        "-o", str(workdir / "video.%(ext)s"), url,
    ])
    vids = [p for p in workdir.iterdir() if p.suffix.lower() in VIDEO_EXTS]
    if not vids:
        sys.exit(f"ERROR: video download failed:\n{r.stderr.strip()[:1000]}")
    # Prefer a manual caption file over an auto-generated one when both exist.
    vtts = sorted(workdir.glob("*.vtt"), key=lambda p: ("auto" in p.stem.lower(), p.name))
    return vids[0], (vtts[0] if vtts else None)


def _to_sec(t):
    hh, mm, ss = t.split(":")
    return int(hh) * 3600 + int(mm) * 60 + float(ss)


def parse_vtt(path):
    """Parse a WebVTT file into [(start, end, text)], collapsing rolling-caption dupes."""
    ts_re = re.compile(r"(\d{2}:\d{2}:\d{2}\.\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2}\.\d{3})")
    text = path.read_text(encoding="utf-8", errors="replace")
    segs = []
    for block in re.split(r"\n\n+", text):
        m = ts_re.search(block)
        if not m:
            continue
        start, end = _to_sec(m.group(1)), _to_sec(m.group(2))
        cue = []
        for ln in block.split("\n"):
            if ts_re.search(ln) or ln.strip().upper().startswith("WEBVTT") or ln.strip().isdigit():
                continue
            cue.append(ln)
        line = re.sub(r"<[^>]+>", "", " ".join(cue))       # strip <c>/<00:00:..> tags
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            segs.append((start, end, line))

    cleaned = []
    for start, end, line in segs:
        if cleaned:
            ps, _, pl = cleaned[-1]
            if line == pl or line in pl:        # exact dupe or partial of previous
                cleaned[-1] = (ps, end, pl)
                continue
            if pl in line:                       # previous was a partial of this line
                cleaned[-1] = (ps, end, line)
                continue
        cleaned.append((start, end, line))
    return cleaned


def whisper_transcribe(ffmpeg, video, workdir):
    """Fallback transcription when a video has no captions. Returns (segments, error)."""
    audio = workdir / "audio.wav"
    r = run([ffmpeg, "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(audio)])
    if r.returncode != 0 or not audio.exists():
        return None, "audio extraction for transcription failed"
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        run([sys.executable, "-m", "pip", "install", "--quiet", "faster-whisper"])
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            return None, (
                "no captions and local transcription unavailable "
                "(faster-whisper not installed; try `pip install faster-whisper`)"
            )
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio))
    out = [(s.start, s.end, s.text.strip()) for s in segments if s.text.strip()]
    return out, None


def extract_frames(ffmpeg, video, scene, interval, width, framesdir):
    """Capture scene-change frames OR-ed with a forced frame every `interval` seconds."""
    framesdir.mkdir(parents=True, exist_ok=True)
    expr = f"eq(n\\,0)+gt(scene\\,{scene})+gte(t-prev_selected_t\\,{interval})"
    vf = f"select='{expr}',scale={width}:-2,showinfo"
    r = run([
        ffmpeg, "-hide_banner", "-y", "-i", str(video),
        "-vf", vf, "-fps_mode", "vfr", "-q:v", "3",
        str(framesdir / "f_%04d.jpg"),
    ])
    times = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
    frames = sorted(framesdir.glob("f_*.jpg"))
    if not frames:
        sys.exit(f"ERROR: no frames extracted:\n{r.stderr.strip()[-800:]}")
    if len(times) >= len(frames):
        return list(zip(frames, times[: len(frames)]))
    return [(f, i * interval) for i, f in enumerate(frames)]   # fallback timing


def cap_frames(paired, max_frames):
    if len(paired) <= max_frames:
        return paired, 0
    n = len(paired)
    idxs = sorted({round(i * (n - 1) / (max_frames - 1)) for i in range(max_frames)})
    keep = {paired[i][0] for i in idxs}
    dropped = 0
    for p, _ in paired:
        if p not in keep:
            try:
                p.unlink()
            except OSError:
                pass
            dropped += 1
    return [paired[i] for i in idxs], dropped


def build_manifest(meta, paired, transcript, source, note, workdir):
    if transcript:
        (workdir / "transcript.txt").write_text(
            "\n".join(f"[{fmt_ts(s)}] {tx}" for s, _, tx in transcript), encoding="utf-8"
        )

    L = [f"# {meta['title'] or meta['id']}", ""]
    if meta["uploader"]:
        L.append(f"- **Channel:** {meta['uploader']}")
    if meta["duration"]:
        L.append(f"- **Duration:** {fmt_ts(meta['duration'])}")
    L += [
        f"- **Source URL:** {meta['url']}",
        f"- **Transcript source:** {source}",
        f"- **Keyframes:** {len(paired)}",
    ]
    if note:
        L.append(f"- **Note:** {note}")
    L += [
        "",
        "Read each `frames/*.jpg` image (you can see them) together with the transcript "
        "text below it, in order. Cite the `[mm:ss]` timestamps when you answer.",
        "",
    ]

    times = [t for _, t in paired]
    for i, (fp, t) in enumerate(paired):
        lo = 0 if i == 0 else t
        nxt = times[i + 1] if i + 1 < len(paired) else float("inf")
        L.append(f"## [{fmt_ts(t)}] frames/{fp.name}")
        if transcript:
            chunk = " ".join(tx for s, _, tx in transcript if lo <= s < nxt)
            if chunk:
                L += ["", chunk]
        L.append("")

    (workdir / "manifest.md").write_text("\n".join(L), encoding="utf-8")
    return workdir / "manifest.md"


def main():
    ap = argparse.ArgumentParser(description="Extract keyframes + transcript from a YouTube video.")
    ap.add_argument("url", help="YouTube video URL")
    ap.add_argument("--scene", type=float, default=0.4, help="scene-change threshold (lower = more frames)")
    ap.add_argument("--interval", type=float, default=20, help="force a frame at least every N seconds")
    ap.add_argument("--max-frames", type=int, default=40, help="cap total frames (evenly subsampled)")
    ap.add_argument("--height", type=int, default=720, help="max download resolution")
    ap.add_argument("--width", type=int, default=960, help="output frame width (px)")
    ap.add_argument("--out", default=None, help="output directory (default ~/Downloads/yt-learn/<id>)")
    ap.add_argument("--no-whisper", action="store_true", help="skip local Whisper transcription fallback")
    args = ap.parse_args()

    ytdlp, ffmpeg = locate_tools()
    meta = get_meta(ytdlp, args.url)
    base = Path(args.out) if args.out else (Path.home() / "Downloads" / "yt-learn" / meta["id"])
    base.mkdir(parents=True, exist_ok=True)
    print(f"[1/4] {meta['title'][:70]!r}  ({fmt_ts(meta['duration']) if meta['duration'] else '?'})")
    print(f"      workdir: {base}")

    video, vtt = download(ytdlp, args.url, args.height, base)
    print(f"[2/4] downloaded {video.name}; captions: {'yes' if vtt else 'none'}")

    note = ""
    if vtt:
        transcript, source = parse_vtt(vtt), "youtube captions"
    elif args.no_whisper:
        transcript, source, note = None, "none", "no captions; Whisper fallback disabled (--no-whisper)"
    else:
        print("      no captions -> attempting local Whisper transcription (first run downloads a model)...")
        transcript, err = whisper_transcribe(ffmpeg, video, base)
        source = "local whisper" if transcript else "none"
        note = err or ""
    print(f"[3/4] transcript: {source}" + (f" ({len(transcript)} segments)" if transcript else ""))

    paired = extract_frames(ffmpeg, video, args.scene, args.interval, args.width, base / "frames")
    paired, dropped = cap_frames(paired, args.max_frames)
    if dropped:
        print(f"      capped to {len(paired)} frames (dropped {dropped} over --max-frames={args.max_frames})")
    print(f"[4/4] extracted {len(paired)} keyframes")

    manifest = build_manifest(meta, paired, transcript, source, note, base)
    print()
    print(f"DONE. Read this next:  {manifest}")
    print(f"Then read the keyframe images in:  {base / 'frames'}")
    print("Answer from the frames (you can see them) + transcript together; cite [mm:ss] timestamps.")


if __name__ == "__main__":
    main()
