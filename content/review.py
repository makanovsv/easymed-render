#!/usr/bin/env python3
"""Страница на вычитку: каталог + все карточки. python3 review.py → review.html"""
import html
import json
from pathlib import Path

H = Path(__file__).parent
cat = json.loads((H / "catalog.json").read_text())
cards = {p.stem: json.loads(p.read_text()) for p in sorted((H / "cards").glob("*.json"))}
e = html.escape
REV = {"L": "по открытым источникам", "M": "желательно врач", "H": "только после врача"}


def ul(xs):
    return "<ul>" + "".join(f"<li>{e(x)}</li>" for x in xs) + "</ul>" if xs else ""


def card(c):
    prep = "".join(f"<p><b>{e(p['title'])}.</b> {e(p['text'])}</p>" for p in c["prepare"])
    steps = "<ol>" + "".join(f"<li>{e(x)}</li>" for x in c["steps"]) + "</ol>"
    faq = "".join(f"<p><b>{e(f['q'])}</b><br>{e(f['a'])}</p>" for f in c["faq"])
    rem = ul([f"за {r['hoursBefore']} ч — {r['text']}" for r in c["reminders"]])
    red = f"<div class='red'><h4>Сразу к врачу, если</h4>{ul(c['red_flags'])}</div>" if c["red_flags"] else ""
    return f"""<article id="{c['id']}"><div class="tag {c['review']}">{c['review']} · {REV[c['review']]}</div>
<h2>{e(c['title'])}</h2><p class="also">{e(' · '.join(c['also']))}</p>
<p class="lead">{e(c['what'])}</p><p><b>Когда назначают:</b> {e(c['why'])}</p><p><b>Сколько длится:</b> {e(c['duration'])}</p>
<h4>Обязательно скажите врачу</h4>{ul(c['tell_doctor'])}<h4>Подготовка</h4>{prep}<h4>Что взять</h4>{ul(c['bring'])}
<h4>Как проходит</h4>{steps}<h4>Что вы почувствуете</h4>{ul(c['feel'])}<h4>После</h4>{ul(c['after'])}{red}
<h4>Частые вопросы (→ Shorts)</h4>{faq}{'<h4>Напоминания в приложении</h4>' + rem if rem else ''}</article>"""


rows = "".join(
    f"<tr class='{'has' if x['id'] in cards else ''}'><td>{e(cat['sections'][x['section']])}</td><td>{'<a href=#'+x['id']+'>' if x['id'] in cards else ''}{e(x['ru'])}{'</a>' if x['id'] in cards else ''}</td>"
    f"<td>{e(cat['scenes'][x['scene']])}</td><td class='{x['review']}'>{x['review']}</td><td>{x['freq']}</td></tr>"
    for x in cat["items"])
doc = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EasyMed — карточки услуг</title><style>
:root{{--bg:#FBF6EE;--card:#fff;--ink:#1E2A3A;--mute:#6B7280;--blue:#2D4A7A;--warm:#E59A4A;--line:#E8E1D5}}
body{{margin:0;background:var(--bg);color:var(--ink);font:17px/1.55 -apple-system,system-ui,sans-serif}}
main{{max-width:820px;margin:auto;padding:24px 16px 80px}} h1{{font-size:30px;margin:8px 0}} h2{{font-size:26px;margin:6px 0 2px}}
h4{{margin:18px 0 6px;color:var(--blue)}} .also{{color:var(--mute);margin:0 0 10px;font-size:15px}} .lead{{font-size:19px}}
article{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px;margin:22px 0}}
.tag{{display:inline-block;font-size:13px;font-weight:700;padding:3px 10px;border-radius:99px;background:#E8EEF7;color:var(--blue)}}
.tag.M{{background:#FFF1E2;color:#9A5A16}} .tag.H{{background:#FBE4E0;color:#A1301B}}
.red{{background:#FDF0EE;border-radius:12px;padding:4px 14px 8px;margin-top:14px}} .red h4{{color:#A1301B}}
table{{width:100%;border-collapse:collapse;font-size:14px;background:var(--card);border-radius:12px;overflow:hidden}}
td{{padding:6px 8px;border-bottom:1px solid var(--line)}} tr.has td{{font-weight:600}} td.H{{color:#A1301B}} td.M{{color:#9A5A16}}
details{{margin:14px 0}} summary{{cursor:pointer;font-weight:700;color:var(--blue)}} a{{color:var(--blue)}}
</style></head><body><main>
<h1>Карточки услуг EasyMed</h1>
<p>Каталог: <b>{len(cat['items'])}</b> самых частых услуг в {len(cat['sections'])} разделах, {len(cat['scenes'])} сцен для картинок. Готово карточек: <b>{len(cards)}</b> (жирные в таблице). Всё — черновик на русском, переводы и ролики делаются из карточки автоматически.</p>
<p><b>L</b> — анализы и диагностика, пишем по открытым источникам · <b>M</b> — процедуры, желательно врач · <b>H</b> — операции и наркоз, публикуем только после врача.</p>
<details><summary>Весь каталог ({len(cat['items'])})</summary><table><tr><td><b>Раздел</b></td><td><b>Услуга</b></td><td><b>Сцена</b></td><td><b>Вычитка</b></td><td><b>Частота</b></td></tr>{rows}</table></details>
{''.join(card(c) for c in cards.values())}
</main></body></html>"""
(H / "review.html").write_text(doc)
print("review.html", len(cards), "карточек")
