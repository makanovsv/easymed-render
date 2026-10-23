#!/usr/bin/env python3
"""Shorts 9:16 из вопросов карточки (faq): вопрос → ответ → «полное видео по ссылке». Озвучка — тот же кэш, что у длинных роликов.

  python3 faq.py <card_id> <lang> <k>   → proj_<id>_<k>_<lang>/ (k — номер вопроса в faq)
  python3 faq.py --list [N]             → следующие N несобранных (id lang k) по порядку очереди
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "cards"))
import build  # noqa: E402
from strings import VOICE  # noqa: E402

LANGS = ["ru", "en", "es", "pt", "kk", "ar", "zh", "ja", "ko", "hi", "uz"]
CTA = {"ru": "Подробно — в полном видео, ссылка в описании.", "en": "More in the full video, link in the description.",
       "kk": "Толығырақ — толық бейнеде, сілтеме сипаттамада.", "es": "Más detalles en el video completo, enlace en la descripción.",
       "pt": "Mais detalhes no vídeo completo, link na descrição.", "ar": "التفاصيل في الفيديو الكامل، الرابط في الوصف.",
       "zh": "更多内容请看完整视频，链接在简介里。", "ja": "くわしくはフル動画で。リンクは概要欄にあります。",
       "ko": "자세한 내용은 전체 영상에서, 링크는 설명란에 있어요.",
       "hi": "पूरी जानकारी पूरे वीडियो में, लिंक विवरण में है।", "uz": "Batafsil — to‘liq videoda, havola tavsifda."}
INK = "#2D4A7A"


def card(cid, lang):
    base = json.loads((build.ROOT / "content/cards" / f"{cid}.json").read_text())
    return base if lang == "ru" else {**base, **json.loads((build.ROOT / f"content/cards_{lang}" / f"{cid}.json").read_text())}


def images(c):
    imgs = [x for x in build.OVERRIDE.get(c["id"], []) if (build.IMG / f"{x}.png").exists()] or build.SCENE.get(c["scene"], ["b_questionnaire"])
    return imgs[:2] if len(imgs) > 1 else [imgs[0], "b_questionnaire"]


def make(cid, lang, k):
    c = card(cid, lang)
    q, a = c["faq"][k]["q"], c["faq"][k]["a"]
    text = f"{q} {a} {CTA[lang]}"
    P = HERE / f"proj_{cid}_{k}_{lang}"
    if P.exists():
        shutil.rmtree(P)
    (P / "assets").mkdir(parents=True)
    for f in ("package.json", "hyperframes.json"):
        shutil.copy(build.HERE.parent / "hf_draw" / f, P / f)
    shutil.copytree(build.FONTS, P / "assets/fonts")
    shutil.copy(build.HERE / "gsap.min.js", P / "assets/gsap.min.js")
    imgs = images(c)
    for x in imgs:
        shutil.copy(build.IMG / f"{x}.png", P / "assets" / f"{x}.png")
    mp3, sub = P / "assets/vo.mp3", P / "assets/vo.srt"
    build.tts(text, VOICE[lang], mp3, sub)
    LEAD = 0.3
    T = round(build.dur(mp3) + LEAD + 1.2, 2)
    cues = build.srt_cues(sub)
    half = T / len(imgs)
    scenes = "".join(
        f'<section id="sc{i}" class="clip scene" data-start="{i*half:.2f}" data-duration="{half:.2f}" data-track-index="1">'
        f'<div class="bg" style="background-image:url(assets/{x}.png)"></div>'
        f'<div class="pic" id="p{i}"><img src="assets/{x}.png"></div></section>' for i, x in enumerate(imgs))
    subs = "".join(f'<div class="clip cap" data-start="{s0+LEAD:.2f}" data-duration="{max(.3, s1-s0):.2f}" data-track-index="3"><span>{html.escape(x)}</span></div>'
                   for s0, s1, x in cues)
    tl = "".join(f"tl.fromTo('#p{i}',{{scale:1.0}},{{scale:1.12,duration:{half:.2f},ease:'none'}},{i*half:.2f});"
                 f"tl.fromTo('#sc{i}',{{opacity:0}},{{opacity:1,duration:.35}},{i*half:.2f});" for i in range(len(imgs)))
    big = 58 if len(q) > 60 else 66
    doc = f"""<!doctype html><html lang="{lang}"{' dir="rtl"' if lang == 'ar' else ''}><head><meta charset="UTF-8"><meta name="viewport" content="width=1080, height=1920">
<title>{html.escape(q)}</title>
<script src="assets/gsap.min.js"></script>
<style>
@font-face{{font-family:"ArialLocal";src:url("assets/fonts/ArialBold.ttf");font-weight:700}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#FBF6EE}}
#root{{position:relative;width:100%;height:100%;overflow:hidden;font-family:"ArialLocal","PingFang SC","Hiragino Sans","Apple SD Gothic Neo","Noto Sans CJK SC","Noto Sans Arabic",sans-serif}}
.scene{{position:absolute;inset:0;opacity:0}} #sc0{{opacity:1}}
.bg{{position:absolute;inset:-60px;background-size:cover;background-position:center;filter:blur(36px) brightness(1.05);opacity:.7}}
.pic{{position:absolute;left:0;right:0;top:600px;height:608px;overflow:hidden}}
.pic img{{width:100%;height:100%;object-fit:cover;display:block}}
.head{{position:absolute;left:60px;right:60px;top:150px;background:#fff;border-radius:34px;padding:34px 40px;box-shadow:0 12px 40px rgba(0,0,0,.12)}}
.head small{{display:block;font-size:34px;font-weight:700;color:{INK}}} .head b{{display:block;font-size:{big}px;line-height:1.1;color:#111114;margin-top:10px}}
.cap{{position:absolute;left:60px;right:60px;top:1290px;text-align:center}}
.cap span{{display:inline-block;background:#111114;color:#fff;font-weight:700;font-size:52px;line-height:1.25;padding:18px 28px;border-radius:22px}}
.foot{{position:absolute;left:0;right:0;bottom:150px;text-align:center;font-size:40px;font-weight:700;color:{INK}}}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{T}">
{scenes}
<div class="head"><small>EasyMed Global</small><b>{html.escape(q)}</b></div>
{subs}
<div class="foot">easymedglobal.com</div>
<audio id="vo" src="assets/vo.mp3" data-start="{LEAD}" data-duration="{T-LEAD:.2f}" data-track-index="5"></audio>
</div>
<script>const tl = gsap.timeline({{ paused: true }});{tl}window.__timelines["main"] = tl;</script>
</body></html>"""
    (P / "index.html").write_text(doc)
    return T


def cached(cid, lang, k):
    """Вся озвучка вопроса уже в кэше (её делает сервер, faq_tts.py) — тогда Мак собирает без обращений к edge-tts."""
    import hashlib
    c = card(cid, lang)
    x = c["faq"][k]
    return all((build.CACHE / (hashlib.sha1(f"{VOICE[lang]}|-5%|{t}".encode()).hexdigest() + ".mp3")).exists()
               for t in build.split_sents(f"{x['q']} {x['a']} {CTA[lang]}"))


def todo():
    """Порядок: сначала услуги, у которых уже вышел длинный ролик (ссылка сразу на видео), потем остальные не-H по алфавиту."""
    log = (build.HERE / "queue_cards.log").read_text()
    pub = sorted({m for m in re.findall(r"OK (\w+?)_(?:ru|en|kk|es|pt|ar|zh|ja|ko):", log)})
    ids = sorted(f.stem for f in (build.ROOT / "content/cards").glob("*.json"))
    rest = [i for i in ids if i not in pub]
    for cid in pub + rest:
        base = json.loads((build.ROOT / "content/cards" / f"{cid}.json").read_text())
        if base["review"] == "H":
            continue
        for k in range(len(base["faq"])):
            for lang in LANGS:
                if lang != "ru" and not (build.ROOT / f"content/cards_{lang}/{cid}.json").exists():
                    continue
                name = f"{cid}_{k}_{lang}"
                if not cached(cid, lang, k) and not __import__("os").environ.get("CI"):
                    continue
                if (HERE / f"{name}.mp4").exists() or (HERE / f".published_{name}").exists() or (HERE / f".failed_{name}").exists():
                    continue
                yield cid, lang, k


if __name__ == "__main__":
    if sys.argv[1] == "--list":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        for i, t in enumerate(todo()):
            if i >= n:
                break
            print(*t)
    else:
        print(make(sys.argv[1], sys.argv[2], int(sys.argv[3])))
