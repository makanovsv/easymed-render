#!/usr/bin/env python3
"""Ролик по карточке услуги: главы из полей карточки → озвучка edge-tts → HyperFrames (акварель + движение камеры).

  python3 build.py <card_id> <lang>      → proj_<id>_<lang>/ (+ .srt рядом)
  cd proj_<id>_<lang> && nice -n 15 npx --yes hyperframes@0.8.119 render --quality looks --output ../<id>_<lang>.mp4 < /dev/null

Карточки: content/cards/<id>.json (ru) и content/cards_<lang>/<id>.json (переводы). Картинки: ../hf_cartoon/img.
"""
import html
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent  # easymed/
sys.path.insert(0, str(ROOT / "content"))
from strings import S, VOICE  # noqa: E402

IMG = HERE.parent / "hf_cartoon/img"
TTS = Path(__import__("os").environ.get("EDGE_TTS", str(Path.home() / "Movies/tiktok/.venv/bin/edge-tts")))
FONTS = HERE.parent / "hf_draw/assets/fonts"
INK, WARM = "#2D4A7A", "#E59A4A"
COVER, PAUSE = 3.0, 0.6

# сцена карточки → картинки (основная, вторая). Файлы в ../hf_cartoon/img
SCENE = {
    "lab_draw": ["g_lab_draw"], "lab_cup": ["g_lab_cup"], "swab": ["g_lab_draw"], "us_room": ["g_us_abd", "g_us_neck"],
    "func_room": ["g_ecg"], "func_treadmill": ["g_treadmill", "g_ecg"], "xr_room": ["xr_room", "xr_chest"],
    "ct_room": ["ct_room", "ct_inj"], "mri_room": ["em_2_A_book", "em_7_s3_tunnel"], "mammo_room": ["g_mammo"],
    "endo_room": ["g_endo"], "proc_room": ["g_proc"], "dent_chair": ["g_dent"], "or_room": ["g_or", "g_ward"],
    "ward": ["g_ward"], "home": ["g_home"], "office": ["b_questionnaire"],
    "gyn_chair": ["g_gyn"], "swab": ["g_swab"], "eye_room": ["g_eye"], "ent_room": ["g_ent"], "uro_room": ["g_uro"],
    "rehab_room": ["g_massage", "g_lfk"], "dent_xray": ["g_dent_xray", "g_dent"], "cath_lab": ["g_cath", "g_ward"],
}
# карточка → своя основная картинка, если сцена общая
OVERRIDE = {"us_thyroid": ["g_us_neck"], "fna_thyroid": ["g_us_neck"], "holter": ["g_holter", "g_ecg"],
            "iv_drip": ["g_iv"], "colono": ["g_endo", "g_home"], "fgds": ["g_endo"], "colono_prep": ["g_home", "g_endo"],
            "us_preg1": ["g_us_abd"], "echo": ["g_us_abd", "g_ecg"], "ct_abd": ["ct_room", "ct_inj"],
            "pcr_swab": ["g_swab"], "kids_check": ["g_kids"], "vacc_kids": ["g_kids_vacc", "g_kids"], "ctg": ["g_ctg"],
            "massage": ["g_massage"], "lfk": ["g_lfk"], "vacc_flu": ["g_lab_draw"], "inj_im": ["g_lab_draw", "g_proc"],
            "birth": ["g_ward", "g_ctg"], "csection": ["g_or", "g_ward"], "sedation": ["g_endo"], "colono_sed": ["g_endo", "g_home"],
            "us_breast": ["g_us_abd"], "us_pelvis": ["g_us_abd"], "us_preg2": ["g_us_abd"], "us_kidney": ["g_us_abd"],
            "us_abdomen": ["g_us_abd"], "xr_teeth": ["g_dent_xray"], "anest_local": ["g_proc"]}
OVERRIDE.update({'urine': ['g_urine'], 'urine_24h': ['g_urine'], 'urine_culture': ['g_urine'], 'blood_finger': ['g_finger'], 'glucose': ['g_finger', 'g_lab_draw'], 'ogtt': ['g_glucose', 'g_lab_draw'], 'stool': ['g_stool'], 'fobt': ['g_stool'], 'echo': ['g_echo', 'g_ecg'], 'us_preg1': ['g_preg_us'], 'us_preg2': ['g_preg_us'], 'us_neuro_baby': ['g_baby_us'], 'us_hip_baby': ['g_baby_us'], 'us_breast': ['g_breast_us'], 'biopsy_breast': ['g_breast_us'], 'us_veins': ['g_leg_us'], 'us_arteries': ['g_leg_us'], 'xr_bone': ['g_xr_arm'], 'mri_joint': ['g_mri_knee'], 'ct_head': ['g_ct_head'], 'dexa': ['g_dexa'], 'inj_im': ['g_inj'], 'vacc_flu': ['g_inj'], 'joint_inj': ['g_inj'], 'dressing': ['g_dressing'], 'sutures_out': ['g_dressing'], 'wound_care': ['g_dressing'], 'dermatoscopy': ['g_dermato'], 'wart': ['g_cryo'], 'papilloma': ['g_cryo'], 'dent_check': ['g_dent_clean'], 'sealant': ['g_dent_clean'], 'whitening': ['g_dent_clean'], 'braces': ['g_braces'], 'iop': ['g_eye_iop'], 'oct': ['g_eye_iop'], 'physio': ['g_physio'], 'shockwave': ['g_physio'], 'therapist': ['g_checkup'], 'checkup': ['g_checkup'], 'medcert': ['g_checkup']})  # отдельные картинки частых услуг (Gemini 12.10)



def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


def srt_cues(p):
    out = []
    for b in p.read_text().strip().split("\n\n"):
        ls = b.strip().splitlines()
        if len(ls) < 3:
            continue
        f = lambda x: sum(float(v) * m for v, m in zip(x.replace(",", ".").split(":"), (3600, 60, 1)))
        a, z = ls[1].split(" --> ")
        out.append((f(a), f(z), " ".join(ls[2:])))
    return out


def complete(sub, text):
    norm = lambda x: re.sub(r"[^\w]+", "", x.lower())
    got = norm(" ".join(c[2] for c in srt_cues(sub))) if sub.exists() else ""
    return norm(text)[-10:] in got


def split_sents(text):
    parts = re.split(r"(?<=[.!?。！？])\s*", text.strip())
    return [x for x in (p.strip() for p in parts) if x]


CACHE = HERE / "tts_cache"


def tts_one(text, voice, mp3, sub):
    """Одно предложение; кэш по (голос, текст). При сбое edge-tts — растущая пауза, чтобы не злить сервер."""
    import hashlib
    CACHE.mkdir(exist_ok=True)
    key = CACHE / (hashlib.sha1(f"{voice}|-5%|{text}".encode()).hexdigest() + ".mp3")
    if key.exists() and key.stat().st_size > 1000:
        shutil.copy(key, mp3)
        return
    for k in range(int(__import__("os").environ.get("TTS_TRIES", "80"))):
        r = subprocess.run([str(TTS), "--voice", voice, "--rate=-5%", "--text", text,
                            "--write-media", str(key)], capture_output=True, text=True)
        if r.returncode == 0 and key.exists() and key.stat().st_size > 1000:
            shutil.copy(key, mp3)
            time.sleep(0.3)
            return
        key.unlink(missing_ok=True)
        time.sleep(min(60, 3 * 2 ** min(k, 5)))  # растущая пауза: частые повторы только усиливают ограничение edge-tts
    raise SystemExit(f"TTS failed: {text[:60]}")


def tts(text, voice, mp3, sub):
    """Озвучка по предложениям (edge-tts часто обрывает длинные запросы) → склейка mp3 и srt."""
    tmp = mp3.parent / f"_{mp3.stem}"
    tmp.mkdir(exist_ok=True)
    parts, cues, t = [], [], 0.0
    for i, x in enumerate(split_sents(text)):
        m, sb = tmp / f"{i:03d}.mp3", tmp / f"{i:03d}.srt"
        tts_one(x, voice, m, sb)
        d = dur(m)
        cues.append((t, t + d, x))
        parts.append(m)
        t += d + 0.15
    lst = tmp / "list.txt"
    sil = tmp / "sil.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-t", "0.15", "-i", "anullsrc=r=24000:cl=mono", "-c:a", "libmp3lame", "-b:a", "48k", str(sil)], check=True)
    lst.write_text("".join(f"file '{m}'\nfile '{sil}'\n" for m in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:a", "libmp3lame", "-b:a", "64k", str(mp3)], check=True)
    ts = lambda x: f"{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(round(x%1*1000)):03d}"
    sub.write_text("\n".join(f"{n}\n{ts(a)} --> {ts(z)}\n{x}\n" for n, (a, z, x) in enumerate(cues, 1)))
    shutil.rmtree(tmp)


def sent(xs, end="."):
    """Список пунктов → фразы для озвучки (каждый пункт — отдельное предложение)."""
    out = []
    for x in xs:
        x = x.strip()
        out.append(x if x[-1:] in ".!?。！？" else x + end)
    return " ".join(out)


def chapters(c, s, lang):
    """Главы ролика: (подпись на экране, текст озвучки, картинка, вставка)."""
    imgs = [x for x in OVERRIDE.get(c["id"], []) if (IMG / f"{x}.png").exists()] or SCENE.get(c["scene"], ["b_questionnaire"])
    main, alt = imgs[0], imgs[-1]
    stop = "。" if lang in ("zh", "ja") else "."
    ch = [(None, f"{c['title']}{stop} {c['what']} {c['why']}", main, None)]
    if c["tell_doctor"]:
        ch.append((s["tell"], f"{s['tell']}{':' if lang not in ('zh','ja') else '：'} " + sent(c["tell_doctor"], stop), "b_questionnaire", None))
    prep = " ".join(p["text"] for p in c["prepare"])
    if c["bring"]:
        prep += f" {s['bring']}{':' if lang not in ('zh','ja') else '：'} " + sent(c["bring"], stop)
    ch.append((s["prep"], prep, "g_home" if c["scene"] in ("endo_room", "home") else "b_locker" if c["scene"] in ("ct_room", "mri_room", "xr_room", "mammo_room") else "b_questionnaire", None))
    ch.append((s["steps"], sent(c["steps"], stop), main, None))
    ch.append((s["feel"], sent(c["feel"], stop) + f" {s['dur']}{'：' if lang in ('zh','ja') else ':'} {c['duration']}{stop}", alt, ("dur", c["duration"])))
    after = sent(c["after"], stop)
    if c["red_flags"]:
        after += f" {s['red']}{'：' if lang in ('zh','ja') else ':'} " + sent(c["red_flags"], stop)
    sec = c.get("section")
    after_img = ("g_ward" if c["review"] == "H" or sec == "endo" else "g_lab_cup" if sec == "lab"
                 else "b_radiologist" if sec in ("us", "func", "rad") else main)
    ch.append((s["after"], after, after_img, None))
    ch.append((None, f"{s['disclaimer']} {s['outro']}", main, ("url", "easymedglobal.com")))
    return ch


def build(cid, lang):
    src = ROOT / "content" / ("cards" if lang == "ru" else f"cards_{lang}") / f"{cid}.json"
    base = json.loads((ROOT / "content/cards" / f"{cid}.json").read_text())
    c = {**base, **json.loads(src.read_text())} if lang != "ru" else base
    s = S[lang]
    P = HERE / f"proj_{cid}_{lang}"
    if P.exists():
        shutil.rmtree(P)
    (P / "assets").mkdir(parents=True)
    for f in ("package.json", "hyperframes.json"):
        shutil.copy(HERE.parent / "hf_draw" / f, P / f)
    shutil.copytree(FONTS, P / "assets/fonts")
    shutil.copy(HERE / "gsap.min.js", P / "assets/gsap.min.js")

    chs = chapters(c, s, lang)
    lens, srt, t = [], [], COVER
    for i, (_, text, img, _) in enumerate(chs, 1):
        shutil.copy(IMG / f"{img}.png", P / "assets" / f"{img}.png")
        mp3, sub = P / f"assets/n{i:02d}.mp3", P / f"assets/n{i:02d}.srt"
        tts(text, VOICE[lang], mp3, sub)
        ln = round(dur(mp3) + PAUSE, 2)
        srt += [(a + t, z + t, x) for a, z, x in srt_cues(sub)]
        lens.append(ln)
        t += ln
    TOTAL = round(t, 2)
    inputs, fc = ["-f", "lavfi", "-t", str(COVER), "-i", "anullsrc=r=48000:cl=stereo"], []
    for i, ln in enumerate(lens, 1):
        inputs += ["-i", str(P / f"assets/n{i:02d}.mp3")]
        fc.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur={ln}[a{i}]")
    fc.append("[0:a]" + "".join(f"[a{i}]" for i in range(1, len(lens) + 1)) + f"concat=n={len(lens)+1}:v=0:a=1[out]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(fc), "-map", "[out]",
                    "-c:a", "aac", "-b:a", "160k", str(P / "assets/narration.m4a")], check=True)
    ts = lambda x: f"{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(round(x%1*1000)):03d}"
    (HERE / f"{cid}_{lang}.srt").write_text("\n".join(f"{n}\n{ts(a)} --> {ts(z)}\n{x}\n" for n, (a, z, x) in enumerate(srt, 1)))

    e = html.escape
    main = chs[0][2]
    secs = [f'''<section id="cv" class="clip scene" data-start="0" data-duration="{COVER}" data-track-index="1">
<div class="cam" id="ccv"><img src="assets/{main}.png"></div>
<div class="title"><small>EasyMed Global · {e(s["kicker"])}</small><b>{e(c["title"])}</b></div></section>''']
    tl = [f"tl.fromTo('#ccv',{{scale:1.08}},{{scale:1.0,duration:{COVER},ease:'none'}},0);"]
    moves = [(1.0, 1.12, 0, -40), (1.12, 1.0, 40, 0), (1.04, 1.14, -30, 30), (1.1, 1.02, 0, -30)]
    t = COVER
    for i, ((label, _, img, extra), d) in enumerate(zip(chs, lens)):
        s0, s1, x0, x1 = moves[i % len(moves)]
        pill = f'<div class="pill" id="l{i}">{e(label)}</div>' if label else ""
        ex = ""
        if extra and extra[0] == "dur":
            ex = f'<div class="num" id="x{i}">{e(extra[1])}</div>'
        if extra and extra[0] == "url":
            ex = f'<div class="url" id="x{i}">{e(extra[1])}</div>'
        secs.append(f'''<section id="s{i}" class="clip scene" data-start="{t:.2f}" data-duration="{d}" data-track-index="1">
<div class="cam" id="c{i}"><img src="assets/{img}.png"></div>{pill}{ex}</section>''')
        tl.append(f"tl.fromTo('#c{i}',{{scale:{s0},x:{x0}}},{{scale:{s1},x:{x1},duration:{d},ease:'sine.inOut'}},{t:.2f});")
        tl.append(f"tl.fromTo('#s{i}',{{opacity:0}},{{opacity:1,duration:.45}},{t:.2f});")
        if label:
            tl.append(f"tl.fromTo('#l{i}',{{opacity:0,y:-20}},{{opacity:1,y:0,duration:.5,ease:'power2.out'}},{t+.3:.2f});")
        if ex:
            tl.append(f"tl.fromTo('#x{i}',{{opacity:0,scale:.8}},{{opacity:1,scale:1,duration:.6,ease:'back.out(1.6)'}},{t+1.0:.2f});")
        t += d
    tl.append(f"tl.to('#s{len(chs)-1}',{{opacity:0,duration:.6}},{TOTAL-.6:.2f});")
    rtl = ' dir="rtl"' if lang == "ar" else ""
    doc = f"""<!doctype html><html lang="{lang}"{rtl}><head><meta charset="UTF-8"><meta name="viewport" content="width=1920, height=1080">
<title>{e(c["title"])}</title>
<script src="assets/gsap.min.js"></script>
<style>
@font-face{{font-family:"ArialLocal";src:url("assets/fonts/ArialBold.ttf");font-weight:700}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1920px;height:1080px;overflow:hidden;background:#FBF6EE}}
#root{{position:relative;width:100%;height:100%;overflow:hidden;font-family:"ArialLocal","PingFang SC","Hiragino Sans","Apple SD Gothic Neo",sans-serif;font-weight:700}}
.scene{{position:absolute;inset:0;overflow:hidden;background:#FBF6EE;opacity:0}} #cv{{opacity:1}}
.cam{{position:absolute;inset:0;transform-origin:50% 50%}} .cam img{{width:100%;height:100%;object-fit:cover;display:block}}
.title{{position:absolute;left:90px;right:90px;top:90px;width:fit-content;max-width:1500px;background:rgba(255,255,255,.95);border-radius:30px;padding:34px 52px;box-shadow:0 10px 40px rgba(0,0,0,.12)}}
.title small{{display:block;font-size:36px;color:{INK}}} .title b{{display:block;font-size:104px;line-height:1.05;color:#111114;margin-top:12px}}
.pill{{position:absolute;left:70px;top:70px;background:rgba(255,255,255,.95);color:{INK};font-size:54px;padding:18px 36px;border-radius:999px;box-shadow:0 8px 30px rgba(0,0,0,.12);opacity:0}}
[dir=rtl] .pill{{left:auto;right:70px}} [dir=rtl] .title{{left:auto;right:90px}}
.num{{position:absolute;right:110px;bottom:110px;max-width:1200px;background:#fff;border-left:14px solid {WARM};border-radius:26px;padding:30px 44px;font-size:64px;line-height:1.15;color:#111114;box-shadow:0 10px 40px rgba(0,0,0,.12);opacity:0}}
.url{{position:absolute;left:0;right:0;margin:0 auto;width:fit-content;bottom:90px;background:#fff;color:{INK};font-size:60px;padding:18px 44px;border-radius:999px;box-shadow:0 10px 40px rgba(0,0,0,.12);opacity:0}}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-width="1920" data-height="1080" data-duration="{TOTAL}">
{chr(10).join(secs)}
<audio id="vo" src="assets/narration.m4a" data-start="0" data-duration="{TOTAL}" data-track-index="5"></audio>
</div>
<script>const tl = gsap.timeline({{ paused: true }});
{chr(10).join(tl)}
window.__timelines["main"] = tl;</script></body></html>"""
    (P / "index.html").write_text(doc)
    print(cid, lang, "total", TOTAL)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
