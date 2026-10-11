#!/usr/bin/env python3
"""Каталог услуг EasyMed — первые ~200 самых частых. Мастер-список, из него строятся карточки, приложение и видео.

  python3 catalog.py   → catalog.json + catalog.csv (для просмотра в Excel)

Поля строки: id, раздел, название (ru), название (en), сцена из библиотеки картинок, уровень вычитки, частота.
  вычитка: L — анализы и неинвазивная диагностика (пишем по открытым клиническим источникам),
           M — процедуры и манипуляции (желательно врач), H — операции и наркоз (только после врача).
  частота: 1 — делают почти все, 2 — часто, 3 — реже.
Коды номенклатуры МЗ РК / 804н РФ подставим отдельным проходом (поле code).
"""
import csv
import json
from pathlib import Path

SECTIONS = {
    "lab": "Анализы", "us": "УЗИ", "func": "Функциональная диагностика", "rad": "Рентген, КТ, МРТ",
    "endo": "Эндоскопия", "proc": "Процедуры и манипуляции", "derm": "Малая хирургия и кожа",
    "dent": "Стоматология", "eye": "Глаза", "ent": "Ухо, горло, нос", "gyn": "Гинекология и беременность",
    "uro": "Урология", "cardio": "Сердце и сосуды: вмешательства", "surg": "Плановые операции",
    "anest": "Обезболивание и наркоз", "rehab": "Реабилитация и физиотерапия", "visit": "Приёмы и осмотры",
    "vacc": "Прививки",
}

# id, раздел, ru, en, сцена, вычитка, частота
ROWS = """
blood_vein|lab|Забор крови из вены|Blood draw from a vein|lab_draw|L|1
blood_finger|lab|Забор крови из пальца|Finger-prick blood test|lab_draw|L|1
cbc|lab|Общий анализ крови|Complete blood count|lab_draw|L|1
biochem|lab|Биохимический анализ крови|Blood chemistry panel|lab_draw|L|1
glucose|lab|Глюкоза крови|Blood glucose test|lab_draw|L|1
hba1c|lab|Гликированный гемоглобин|HbA1c test|lab_draw|L|2
ogtt|lab|Глюкозотолерантный тест|Oral glucose tolerance test|lab_draw|L|2
lipids|lab|Липидный профиль (холестерин)|Lipid panel (cholesterol)|lab_draw|L|1
thyroid|lab|Гормоны щитовидной железы (ТТГ, Т4)|Thyroid hormones (TSH, T4)|lab_draw|L|1
coag|lab|Коагулограмма|Blood clotting tests|lab_draw|L|2
crp|lab|С-реактивный белок|C-reactive protein|lab_draw|L|2
ferritin|lab|Ферритин и железо|Ferritin and iron|lab_draw|L|2
vitd|lab|Витамин D|Vitamin D|lab_draw|L|2
blood_group|lab|Группа крови и резус-фактор|Blood type and Rh factor|lab_draw|L|2
hiv_hep|lab|Анализ на ВИЧ, гепатиты B и C, сифилис|HIV, hepatitis B and C, syphilis tests|lab_draw|L|1
psa|lab|ПСА (простатический антиген)|PSA test|lab_draw|L|2
hcg|lab|ХГЧ — анализ крови на беременность|hCG pregnancy blood test|lab_draw|L|2
sex_hormones|lab|Половые гормоны|Sex hormones|lab_draw|L|2
tumor_markers|lab|Онкомаркеры|Tumour markers|lab_draw|L|3
allergy_panel|lab|Аллергопанель (IgE)|Allergy blood panel (IgE)|lab_draw|L|3
urine|lab|Общий анализ мочи|Urinalysis|lab_cup|L|1
urine_24h|lab|Суточная моча|24-hour urine collection|lab_cup|L|3
urine_culture|lab|Посев мочи|Urine culture|lab_cup|L|2
stool|lab|Анализ кала (копрограмма)|Stool test|lab_cup|L|2
fobt|lab|Кал на скрытую кровь|Faecal occult blood test|lab_cup|L|2
pcr_swab|lab|ПЦР-мазок из носа и горла|Nose and throat PCR swab|swab|L|1
gyn_smear|lab|Мазок на флору (гинекологический)|Vaginal smear|gyn_chair|L|1
pap|lab|ПАП-тест (цитология шейки матки)|Pap smear|gyn_chair|L|1
semen|lab|Спермограмма|Semen analysis|lab_cup|L|3
sputum|lab|Анализ мокроты|Sputum test|lab_cup|L|3
us_abdomen|us|УЗИ брюшной полости|Abdominal ultrasound|us_room|L|1
us_liver|us|УЗИ печени и желчного пузыря|Liver and gallbladder ultrasound|us_room|L|1
elastography|us|Эластография печени (фиброскан)|Liver elastography (FibroScan)|us_room|L|3
us_kidney|us|УЗИ почек|Kidney ultrasound|us_room|L|1
us_bladder|us|УЗИ мочевого пузыря с остаточной мочой|Bladder ultrasound with residual urine|us_room|L|2
us_thyroid|us|УЗИ щитовидной железы|Thyroid ultrasound|us_room|L|1
us_breast|us|УЗИ молочных желёз|Breast ultrasound|us_room|L|1
us_pelvis|us|УЗИ органов малого таза (женщинам)|Pelvic ultrasound (women)|us_room|L|1
us_tv|us|Трансвагинальное УЗИ|Transvaginal ultrasound|us_room|L|2
us_prostate|us|УЗИ простаты (ТРУЗИ)|Prostate ultrasound (TRUS)|us_room|L|2
us_scrotum|us|УЗИ мошонки|Scrotal ultrasound|us_room|L|3
us_preg1|us|Скрининг беременности 1 триместра|First-trimester pregnancy scan|us_room|L|1
us_preg2|us|Скрининг беременности 2 и 3 триместра|Second and third trimester scans|us_room|L|1
us_carotid|us|УЗИ сосудов шеи (БЦА)|Carotid ultrasound|us_room|L|2
us_veins|us|УЗИ вен ног|Leg vein ultrasound|us_room|L|2
us_arteries|us|УЗИ артерий ног|Leg artery ultrasound|us_room|L|3
echo|us|Эхокардиография (УЗИ сердца)|Echocardiogram (heart ultrasound)|us_room|L|1
us_joint|us|УЗИ сустава|Joint ultrasound|us_room|L|2
us_lymph|us|УЗИ лимфоузлов и мягких тканей|Lymph node and soft tissue ultrasound|us_room|L|2
us_neuro_baby|us|Нейросонография младенцу|Infant brain ultrasound|us_room|L|2
us_hip_baby|us|УЗИ тазобедренных суставов младенцу|Infant hip ultrasound|us_room|L|2
ecg|func|ЭКГ|ECG|func_room|L|1
stress_ecg|func|ЭКГ с нагрузкой (тредмил, велоэргометрия)|Exercise stress test|func_treadmill|M|2
holter|func|Холтер ЭКГ (суточный монитор)|Holter monitor|func_room|L|2
abpm|func|Суточный мониторинг давления (СМАД)|24-hour blood pressure monitoring|func_room|L|2
spirometry|func|Спирометрия|Spirometry|func_room|L|2
eeg|func|ЭЭГ (электроэнцефалография)|EEG|func_room|L|2
enmg|func|ЭНМГ (проверка нервов и мышц)|Nerve conduction study (EMG)|func_room|L|3
sleep_study|func|Исследование сна (полисомнография)|Sleep study|ward|L|3
xr_chest|rad|Рентген грудной клетки|Chest X-ray|xr_room|L|1
fluoro|rad|Флюорография|Chest screening X-ray|xr_room|L|1
xr_bone|rad|Рентген костей и суставов|Bone and joint X-ray|xr_room|L|1
xr_spine|rad|Рентген позвоночника|Spine X-ray|xr_room|L|2
xr_teeth|rad|Панорамный снимок зубов (ОПТГ)|Dental panoramic X-ray|dent_xray|L|1
mammo|rad|Маммография|Mammogram|mammo_room|L|1
dexa|rad|Денситометрия (плотность костей)|Bone density scan (DEXA)|xr_room|L|3
ct_head|rad|КТ головы|Head CT|ct_room|L|1
ct_chest|rad|КТ лёгких|Chest CT|ct_room|L|1
ct_abd|rad|КТ брюшной полости с контрастом|Abdominal CT with contrast|ct_room|M|2
ct_angio|rad|КТ-ангиография|CT angiography|ct_room|M|3
mri_brain|rad|МРТ головного мозга|Brain MRI|mri_room|L|1
mri_spine|rad|МРТ позвоночника|Spine MRI|mri_room|L|1
mri_joint|rad|МРТ сустава|Joint MRI|mri_room|L|1
mri_abd|rad|МРТ брюшной полости и малого таза|Abdominal and pelvic MRI|mri_room|M|2
barium|rad|Рентген желудка и кишечника с барием|Barium X-ray|xr_room|M|3
pet_ct|rad|ПЭТ-КТ|PET-CT|ct_room|M|3
fgds|endo|ФГДС (гастроскопия)|Gastroscopy|endo_room|M|1
fgds_sed|endo|Гастроскопия во сне (под седацией)|Gastroscopy under sedation|endo_room|M|2
colono|endo|Колоноскопия|Colonoscopy|endo_room|M|1
colono_sed|endo|Колоноскопия во сне (под седацией)|Colonoscopy under sedation|endo_room|M|1
colono_prep|endo|Подготовка кишечника к колоноскопии|Bowel prep for colonoscopy|home|M|1
capsule|endo|Капсульная эндоскопия|Capsule endoscopy|endo_room|M|3
broncho|endo|Бронхоскопия|Bronchoscopy|endo_room|M|3
cysto|endo|Цистоскопия|Cystoscopy|uro_room|M|3
hystero|endo|Гистероскопия|Hysteroscopy|gyn_chair|M|2
colpo|endo|Кольпоскопия|Colposcopy|gyn_chair|L|2
anoscopy|endo|Аноскопия и ректоскопия|Anoscopy and proctoscopy|proc_room|M|3
laryngo|endo|Осмотр гортани (ларингоскопия)|Laryngoscopy|ent_room|L|3
inj_im|proc|Внутримышечный укол|Intramuscular injection|proc_room|L|1
iv_drip|proc|Капельница|IV drip|proc_room|M|1
iv_cannula|proc|Установка венозного катетера|IV cannula|proc_room|L|2
dressing|proc|Перевязка|Wound dressing|proc_room|L|1
sutures_out|proc|Снятие швов|Stitch removal|proc_room|L|1
wound_care|proc|Обработка раны и наложение швов|Wound cleaning and stitches|proc_room|M|2
earwax|proc|Промывание ушей (серная пробка)|Ear wax removal|ent_room|L|1
sinus_wash|proc|Промывание носа и пазух|Sinus rinse|ent_room|L|2
fna_thyroid|proc|Пункция щитовидной железы (ТАБ)|Thyroid fine-needle biopsy|us_room|M|2
biopsy_breast|proc|Биопсия молочной железы|Breast biopsy|us_room|M|3
joint_inj|proc|Укол в сустав|Joint injection|proc_room|M|2
lumbar|proc|Люмбальная пункция|Lumbar puncture|ward|H|3
skin_biopsy|proc|Биопсия кожи|Skin biopsy|proc_room|M|3
iud_in|proc|Установка внутриматочной спирали|IUD insertion|gyn_chair|M|2
iud_out|proc|Удаление внутриматочной спирали|IUD removal|gyn_chair|L|2
catheter|proc|Установка мочевого катетера|Urinary catheter|ward|M|3
enema|proc|Клизма|Enema|proc_room|L|3
mole|derm|Удаление родинки|Mole removal|proc_room|M|1
wart|derm|Удаление бородавки (криодеструкция)|Wart removal (cryotherapy)|proc_room|L|1
papilloma|derm|Удаление папиллом|Skin tag removal|proc_room|L|1
lipoma|derm|Удаление липомы и атеромы|Lipoma or cyst removal|proc_room|M|2
abscess|derm|Вскрытие нарыва (абсцесса, фурункула)|Abscess drainage|proc_room|M|2
nail|derm|Удаление вросшего ногтя|Ingrown toenail removal|proc_room|M|2
tick|derm|Удаление клеща|Tick removal|proc_room|L|2
dermatoscopy|derm|Дерматоскопия (осмотр родинок)|Dermatoscopy (mole check)|proc_room|L|1
dent_check|dent|Осмотр и профессиональная чистка зубов|Dental check-up and cleaning|dent_chair|L|1
caries|dent|Лечение кариеса (пломба)|Filling a cavity|dent_chair|L|1
root_canal|dent|Лечение каналов зуба|Root canal treatment|dent_chair|M|1
tooth_out|dent|Удаление зуба|Tooth extraction|dent_chair|M|1
wisdom|dent|Удаление зуба мудрости|Wisdom tooth removal|dent_chair|M|2
implant|dent|Имплантация зуба|Dental implant|dent_chair|H|2
crown|dent|Коронка на зуб|Dental crown|dent_chair|L|2
braces|dent|Брекеты|Braces|dent_chair|L|2
whitening|dent|Отбеливание зубов|Teeth whitening|dent_chair|L|2
sealant|dent|Герметизация фиссур ребёнку|Fissure sealants for children|dent_chair|L|2
vision|eye|Проверка зрения и подбор очков|Eye test and glasses|eye_room|L|1
iop|eye|Измерение глазного давления|Eye pressure test|eye_room|L|1
fundus|eye|Осмотр глазного дна с расширением зрачка|Dilated eye exam|eye_room|L|2
oct|eye|ОКТ сетчатки|Retinal OCT scan|eye_room|L|2
lasik|eye|Лазерная коррекция зрения|Laser eye surgery|or_room|H|2
cataract|eye|Операция по удалению катаракты|Cataract surgery|or_room|H|2
audiometry|ent|Проверка слуха (аудиометрия)|Hearing test|ent_room|L|2
tympanometry|ent|Тимпанометрия|Tympanometry|ent_room|L|3
adenoids|ent|Удаление аденоидов|Adenoid removal|or_room|H|2
tonsils|ent|Удаление миндалин|Tonsillectomy|or_room|H|2
septum|ent|Операция на перегородке носа (септопластика)|Septoplasty|or_room|H|3
gyn_visit|gyn|Осмотр гинеколога|Gynaecological exam|gyn_chair|L|1
ctg|gyn|КТГ плода|Fetal heart monitoring (CTG)|ward|L|1
birth|gyn|Естественные роды|Vaginal birth|ward|H|1
csection|gyn|Кесарево сечение|Caesarean section|or_room|H|1
curettage|gyn|Выскабливание (диагностическое)|Diagnostic curettage|or_room|H|2
ivf_retrieval|gyn|ЭКО: пункция яйцеклеток|IVF egg retrieval|or_room|H|3
ivf_transfer|gyn|ЭКО: перенос эмбриона|IVF embryo transfer|gyn_chair|M|3
uro_visit|uro|Осмотр уролога|Urology exam|uro_room|L|1
uroflow|uro|Урофлоуметрия|Uroflowmetry|uro_room|L|3
prostate_biopsy|uro|Биопсия простаты|Prostate biopsy|uro_room|H|3
eswl|uro|Дробление камней в почках (литотрипсия)|Kidney stone lithotripsy|uro_room|H|2
coronary|cardio|Коронарография|Coronary angiography|cath_lab|H|2
stent|cardio|Стентирование сосудов сердца|Coronary stent|cath_lab|H|2
pacemaker|cardio|Установка кардиостимулятора|Pacemaker implantation|cath_lab|H|3
ablation|cardio|Радиочастотная абляция (РЧА)|Catheter ablation|cath_lab|H|3
evlk|cardio|Лазерное лечение варикоза (ЭВЛК)|Laser treatment of varicose veins|proc_room|H|2
gallbladder|surg|Удаление желчного пузыря (лапароскопия)|Gallbladder removal (laparoscopic)|or_room|H|1
appendix|surg|Удаление аппендицита|Appendectomy|or_room|H|1
hernia_ing|surg|Операция при паховой грыже|Inguinal hernia repair|or_room|H|1
hernia_umb|surg|Операция при пупочной грыже|Umbilical hernia repair|or_room|H|2
hemorrhoids|surg|Лечение геморроя (операция)|Haemorrhoid surgery|or_room|H|2
arthroscopy|surg|Артроскопия колена|Knee arthroscopy|or_room|H|2
hip_replace|surg|Замена тазобедренного сустава|Hip replacement|or_room|H|2
knee_replace|surg|Замена коленного сустава|Knee replacement|or_room|H|2
disc|surg|Операция при грыже позвоночника|Spinal disc surgery|or_room|H|3
thyroidectomy|surg|Удаление щитовидной железы|Thyroid surgery|or_room|H|3
myoma|surg|Удаление миомы матки|Fibroid removal|or_room|H|2
hysterectomy|surg|Удаление матки|Hysterectomy|or_room|H|3
circumcision|surg|Обрезание|Circumcision|or_room|H|2
anest_general|anest|Общий наркоз|General anaesthesia|or_room|H|1
anest_spinal|anest|Спинальная анестезия|Spinal anaesthesia|or_room|H|2
anest_local|anest|Местная анестезия|Local anaesthesia|proc_room|M|1
sedation|anest|Седация (медикаментозный сон)|Sedation|endo_room|M|1
massage|rehab|Лечебный массаж|Therapeutic massage|rehab_room|L|1
lfk|rehab|ЛФК (лечебная физкультура)|Physiotherapy exercises|rehab_room|L|1
physio|rehab|Физиотерапия (магнит, электрофорез, ультразвук)|Physical therapy (magnet, electrophoresis)|rehab_room|L|2
shockwave|rehab|Ударно-волновая терапия|Shockwave therapy|rehab_room|L|2
therapist|visit|Приём терапевта|GP appointment|office|L|1
checkup|visit|Комплексный чекап|Health check-up|office|L|1
medcert|visit|Медосмотр для справки (водительская, на работу)|Medical certificate exam|office|L|1
kids_check|visit|Профосмотр ребёнка|Child check-up|office|L|1
vacc_kids|vacc|Детские прививки|Childhood vaccines|proc_room|L|1
vacc_flu|vacc|Прививка от гриппа|Flu shot|proc_room|L|1
"""

# сцены — библиотека картинок, из которой собираются все ролики
SCENES = {
    "lab_draw": "процедурный кабинет: забор крови", "lab_cup": "сдача мочи/кала: контейнер, туалет клиники",
    "swab": "взятие мазка из носа и горла", "us_room": "кабинет УЗИ", "func_room": "кабинет функциональной диагностики",
    "func_treadmill": "беговая дорожка / велоэргометр с ЭКГ", "xr_room": "рентген-кабинет", "ct_room": "кабинет КТ",
    "mri_room": "кабинет МРТ", "mammo_room": "маммограф", "dent_xray": "панорамный рентген зубов",
    "endo_room": "эндоскопический кабинет", "proc_room": "процедурный / малая операционная", "gyn_chair": "гинекологическое кресло",
    "uro_room": "кабинет уролога", "ent_room": "кабинет ЛОРа", "eye_room": "кабинет окулиста", "dent_chair": "стоматологическое кресло",
    "or_room": "операционная", "ward": "палата", "cath_lab": "рентгеноперационная (ангиограф)", "rehab_room": "зал реабилитации",
    "office": "кабинет врача", "home": "дома: подготовка",
}

if __name__ == "__main__":
    here = Path(__file__).parent
    items = []
    for line in ROWS.strip().splitlines():
        i, sec, ru, en, scene, review, freq = line.split("|")
        assert sec in SECTIONS and scene in SCENES, line
        items.append(dict(id=i, section=sec, ru=ru, en=en, scene=scene, review=review, freq=int(freq), code=""))
    ids = [x["id"] for x in items]
    assert len(ids) == len(set(ids)), "дубли id"
    (here / "catalog.json").write_text(json.dumps({"sections": SECTIONS, "scenes": SCENES, "items": items}, ensure_ascii=False, indent=1))
    with open(here / "catalog.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id", "Раздел", "Услуга", "English", "Сцена", "Вычитка", "Частота"])
        for x in items:
            w.writerow([x["id"], SECTIONS[x["section"]], x["ru"], x["en"], SCENES[x["scene"]], x["review"], x["freq"]])
    by = lambda k: {v: sum(1 for x in items if x[k] == v) for v in sorted({x[k] for x in items})}
    print(len(items), "услуг;", "вычитка", by("review"), "; частота", by("freq"), "; сцен", len(SCENES))
