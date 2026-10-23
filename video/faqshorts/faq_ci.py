#!/usr/bin/env python3
"""Shorts из вопросов карточек на GitHub: python3 faq_ci.py <N> <T> [минут]. Своя доля списка, пока есть время → dist/*.mp4"""
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import faq  # noqa: E402

N, T = int(sys.argv[1]), int(sys.argv[2])
LIMIT = time.time() + 60 * (int(sys.argv[3]) if len(sys.argv) > 3 else 300)
done = set((HERE / "done.txt").read_text().split()) if (HERE / "done.txt").exists() else set()
C = faq.build.ROOT / "content"
items = []
for f in sorted((C / "cards").glob("*.json")):
    base = json.loads(f.read_text())
    if base["review"] == "H":
        continue
    for k in range(len(base["faq"])):
        for lang in faq.LANGS:
            if lang == "ru" or (C / f"cards_{lang}" / f.name).exists():
                items.append((f.stem, lang, k))
only = set((HERE / "only.txt").read_text().split()) if (HERE / "only.txt").exists() else None  # партия: только эти имена
if only:
    items = [x for x in items if f"{x[0]}_{x[2]}_{x[1]}" in only]
mine = [x for i, x in enumerate(items) if i % T == N and f"{x[0]}_{x[2]}_{x[1]}" not in done]
out = HERE / "dist"
out.mkdir(exist_ok=True)
print(len(items), "всего,", len(mine), "моих", flush=True)
for cid, lang, k in mine:
    if time.time() > LIMIT:
        break
    name = f"{cid}_{k}_{lang}"
    try:
        faq.make(cid, lang, k)
        P = HERE / f"proj_{cid}_{k}_{lang}"
        subprocess.run(["npx", "--yes", "hyperframes@0.8.119", "render", "--quality", "looks", "--output", str(HERE / "raw.mp4")],
                       cwd=P, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=900)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(HERE / "raw.mp4"), "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                        "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(out / f"{name}.mp4")], check=True)
        subprocess.run(["rm", "-rf", str(P), str(HERE / "raw.mp4")])
        print("OK", name, flush=True)
    except (Exception, SystemExit) as e:
        print("FAIL", name, str(e)[:120], flush=True)
