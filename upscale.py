#!/usr/bin/env python3
"""Upscale a video.

Two methods:
  classic  - ffmpeg Lanczos resampling + light sharpening (fast, CPU, always available)
  ai       - Real-ESRGAN via realesrgan-ncnn-vulkan (much sharper, needs the binary + a GPU/Vulkan)

Examples:
  python upscale.py input.mp4                      # 2x, classic
  python upscale.py input.mp4 -s 4 -o out.mp4      # 4x
  python upscale.py input.mp4 --height 2160        # upscale to 4K height, keep aspect
  python upscale.py input.mp4 -m ai -s 4           # AI upscale
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run(cmd, check=True)


def probe_fps(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return out or "30"


def encode_args(crf, preset):
    return ["-c:v", "libx264", "-crf", str(crf), "-preset", preset, "-pix_fmt", "yuv420p"]


def upscale_classic(src, dst, scale, height, crf, preset):
    # Force even dimensions so libx264 accepts them
    if height:
        size = f"scale=-2:{height}:flags=lanczos"
    else:
        size = f"scale=trunc(iw*{scale}/2)*2:trunc(ih*{scale}/2)*2:flags=lanczos"
    vf = f"{size},unsharp=5:5:0.8:5:5:0.0"
    run(["ffmpeg", "-y", "-i", str(src), "-vf", vf,
         *encode_args(crf, preset), "-c:a", "copy", str(dst)])


def upscale_ai(src, dst, scale, crf, preset, model):
    exe = shutil.which("realesrgan-ncnn-vulkan")
    if not exe:
        sys.exit("realesrgan-ncnn-vulkan not found on PATH. Download it from "
                 "https://github.com/xinntao/Real-ESRGAN/releases or use -m classic.")
    if scale not in (2, 3, 4):
        sys.exit("AI mode supports scale 2, 3 or 4.")
    fps = probe_fps(src)
    with tempfile.TemporaryDirectory() as tmp:
        frames, up = Path(tmp, "in"), Path(tmp, "out")
        frames.mkdir()
        up.mkdir()
        run(["ffmpeg", "-y", "-i", str(src), "-qscale:v", "1", str(frames / "%08d.png")])
        run([exe, "-i", str(frames), "-o", str(up), "-s", str(scale), "-n", model, "-f", "png"])
        # Reassemble frames and take audio from the original
        run(["ffmpeg", "-y", "-framerate", fps, "-i", str(up / "%08d.png"),
             "-i", str(src), "-map", "0:v", "-map", "1:a?",
             *encode_args(crf, preset), "-c:a", "copy", str(dst)])


def main():
    p = argparse.ArgumentParser(description="Upscale a video.")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument("-s", "--scale", type=float, default=2)
    p.add_argument("--height", type=int, help="target height (classic only); overrides --scale")
    p.add_argument("-m", "--method", choices=["classic", "ai"], default="classic")
    p.add_argument("--model", default="realesr-animevideov3",
                   help="Real-ESRGAN model for AI mode (e.g. realesrgan-x4plus for live action)")
    p.add_argument("--crf", type=int, default=18, help="quality, lower = better (default 18)")
    p.add_argument("--preset", default="medium")
    a = p.parse_args()

    src = Path(a.input)
    if not src.exists():
        sys.exit(f"Input not found: {src}")
    dst = Path(a.output) if a.output else src.with_name(f"{src.stem}_upscaled.mp4")

    if a.method == "ai":
        upscale_ai(src, dst, int(a.scale), a.crf, a.preset, a.model)
    else:
        upscale_classic(src, dst, a.scale, a.height, a.crf, a.preset)
    print(f"Done: {dst}")


if __name__ == "__main__":
    main()
