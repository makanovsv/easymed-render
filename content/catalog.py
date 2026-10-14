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
ast_alt|lab|Печёночные пробы (АЛТ, АСТ, билирубин)|Liver function tests (ALT, AST, bilirubin)|lab_draw|L|1
kidney_tests|lab|Почечные пробы (креатинин, мочевина, СКФ)|Kidney function tests (creatinine, urea, eGFR)|lab_draw|L|1
electrolytes|lab|Электролиты крови (калий, натрий, кальций)|Blood electrolytes (potassium, sodium, calcium)|lab_draw|L|2
uric_acid|lab|Мочевая кислота|Uric acid test|lab_draw|L|2
b12_folate|lab|Витамин B12 и фолиевая кислота|Vitamin B12 and folate|lab_draw|L|2
magnesium|lab|Магний крови|Blood magnesium|lab_draw|L|3
insulin|lab|Инсулин и индекс HOMA|Insulin and HOMA index|lab_draw|L|2
cpeptide|lab|С-пептид|C-peptide test|lab_draw|L|3
anti_tpo|lab|Антитела к щитовидной железе (АТ-ТПО)|Thyroid antibodies (anti-TPO)|lab_draw|L|2
cortisol|lab|Кортизол|Cortisol test|lab_draw|L|2
prolactin|lab|Пролактин|Prolactin test|lab_draw|L|2
amh|lab|АМГ (антимюллеров гормон)|AMH (anti-Müllerian hormone)|lab_draw|L|2
testosterone|lab|Тестостерон|Testosterone test|lab_draw|L|2
progesterone|lab|Прогестерон|Progesterone test|lab_draw|L|3
pth|lab|Паратгормон|Parathyroid hormone (PTH)|lab_draw|L|3
ddimer|lab|D-димер|D-dimer test|lab_draw|L|2
inr|lab|МНО при приёме варфарина|INR test on warfarin|lab_draw|L|2
troponin|lab|Тропонин|Troponin test|lab_draw|L|3
bnp|lab|NT-proBNP (сердечный пептид)|NT-proBNP heart test|lab_draw|L|3
esr|lab|СОЭ|ESR (sedimentation rate)|lab_draw|L|1
rheum_factor|lab|Ревмофактор и АЦЦП|Rheumatoid factor and anti-CCP|lab_draw|L|2
ana|lab|Антинуклеарные антитела (АНА)|Antinuclear antibodies (ANA)|lab_draw|L|3
celiac|lab|Анализ на целиакию|Coeliac disease blood test|lab_draw|L|3
hpylori|lab|Анализ на хеликобактер|Helicobacter pylori test|lab_cup|L|2
urea_breath|lab|Дыхательный тест на хеликобактер|Urea breath test for H. pylori|lab_cup|L|2
hpv|lab|ВПЧ-тест|HPV test|gyn_chair|L|2
sti_pcr|lab|ПЦР на половые инфекции|STI PCR test|gyn_chair|L|2
torch|lab|TORCH-инфекции перед беременностью|TORCH infections before pregnancy|lab_draw|L|2
covid_ag|lab|Экспресс-тест на COVID-19 и грипп|Rapid COVID-19 and flu test|swab|L|2
strep_test|lab|Экспресс-тест на стрептококк (ангина)|Rapid strep throat test|swab|L|2
throat_culture|lab|Мазок из зева на флору|Throat culture|swab|L|2
quantiferon|lab|Квантифероновый тест на туберкулёз|QuantiFERON TB blood test|lab_draw|L|3
mantoux|lab|Проба Манту и Диаскинтест|Mantoux and Diaskintest skin tests|proc_room|L|1
parasites|lab|Анализ на паразитов (яйца глист)|Stool test for parasites|lab_cup|L|2
enterobiasis|lab|Соскоб на энтеробиоз|Pinworm tape test|lab_cup|L|2
calprotectin|lab|Фекальный кальпротектин|Faecal calprotectin|lab_cup|L|3
urine_nechip|lab|Анализ мочи по Нечипоренко|Nechiporenko urine test|lab_cup|L|2
urine_zimn|lab|Анализ мочи по Зимницкому|Zimnitsky urine test|lab_cup|L|3
microalb|lab|Микроальбумин в моче|Urine microalbumin|lab_cup|L|2
drug_test|lab|Тест на наркотики (моча)|Urine drug test|lab_cup|L|2
alcohol_test|lab|Медосвидетельствование на алкоголь|Alcohol breath and blood test|office|L|3
genetic_nipt|lab|НИПТ — неинвазивный пренатальный тест|NIPT prenatal blood test|lab_draw|L|2
prenatal_screen|lab|Биохимический скрининг беременных|Prenatal biochemical screening|lab_draw|L|1
karyotype|lab|Кариотип|Karyotype test|lab_draw|L|3
newborn_screen|lab|Неонатальный скрининг (пяточка)|Newborn heel-prick screening|lab_draw|L|1
bilirubin_baby|lab|Билирубин у новорождённого|Newborn bilirubin test|lab_draw|L|2
blood_kids|lab|Анализ крови у ребёнка|Blood test in a child|lab_draw|L|1
urine_kids|lab|Как собрать мочу у малыша|Collecting urine from a baby|lab_cup|L|1
allergy_skin|lab|Кожные аллергопробы|Skin prick allergy test|proc_room|L|2
food_intol|lab|Анализ на пищевую непереносимость|Food intolerance test|lab_draw|L|3
sweat_test|lab|Потовый тест|Sweat test|proc_room|L|3
blood_culture|lab|Посев крови|Blood culture|lab_draw|L|3
wound_culture|lab|Посев из раны|Wound swab culture|proc_room|L|3
fungal_scrape|lab|Соскоб на грибок кожи и ногтей|Skin and nail fungus scraping|proc_room|L|2
ige_total|lab|Общий IgE|Total IgE test|lab_draw|L|3
homocysteine|lab|Гомоцистеин|Homocysteine test|lab_draw|L|3
lupus_ac|lab|Анализ на тромбофилию|Thrombophilia tests|lab_draw|L|3
us_salivary|us|УЗИ слюнных желёз|Salivary gland ultrasound|us_room|L|3
us_soft|us|УЗИ мягких тканей|Soft tissue ultrasound|us_room|L|2
us_pleura|us|УЗИ плевральной полости|Pleural ultrasound|us_room|L|3
us_follicle|us|Фолликулометрия|Follicle tracking ultrasound|us_room|L|2
us_cervix|us|УЗИ шейки матки при беременности (цервикометрия)|Cervical length ultrasound in pregnancy|us_room|L|2
us_doppler_preg|us|Допплер при беременности|Pregnancy Doppler ultrasound|us_room|L|2
us_preg3|us|УЗИ в третьем триместре|Third-trimester ultrasound|us_room|L|1
us_kids_abd|us|УЗИ живота у ребёнка|Abdominal ultrasound in a child|us_room|L|1
us_heart_kids|us|УЗИ сердца у ребёнка|Heart ultrasound in a child|us_room|L|2
us_kidney_vessels|us|УЗИ сосудов почек|Renal artery ultrasound|us_room|L|3
us_head_neck_vessels|us|Дуплекс сосудов головы и шеи|Head and neck vessel duplex|us_room|L|2
us_tcd|us|Транскраниальная допплерография|Transcranial Doppler|us_room|L|3
us_penis|us|Допплер сосудов полового члена|Penile Doppler ultrasound|us_room|L|3
us_abd_aorta|us|УЗИ брюшной аорты|Abdominal aorta ultrasound|us_room|L|3
tee|us|Чреспищеводная ЭхоКГ|Transoesophageal echocardiogram|endo_room|M|3
stress_echo|us|Стресс-ЭхоКГ|Stress echocardiogram|func_treadmill|M|3
ecg_kids|func|ЭКГ у ребёнка|ECG in a child|func_room|L|1
holter_bp_kids|func|Суточный мониторинг давления у подростка|24-hour blood pressure in teens|func_room|L|3
reg|func|Реоэнцефалография (РЭГ)|Rheoencephalography (REG)|func_room|L|3
eeg_video|func|Видео-ЭЭГ мониторинг|Video EEG monitoring|func_room|L|3
eeg_kids|func|ЭЭГ у ребёнка|EEG in a child|func_room|L|2
evoked|func|Вызванные потенциалы|Evoked potentials test|func_room|L|3
spiro_test|func|Спирометрия с бронхолитиком|Spirometry with bronchodilator|func_room|L|2
bodyplet|func|Бодиплетизмография|Body plethysmography|func_room|L|3
dlco|func|Диффузионный тест лёгких|Lung diffusion test (DLCO)|func_room|L|3
pulse_ox|func|Пульсоксиметрия ночная|Overnight pulse oximetry|home|L|3
abi|func|Лодыжечно-плечевой индекс|Ankle-brachial index|func_room|L|3
tilt|func|Тилт-тест|Tilt table test|func_room|M|3
ph_metry|func|Суточная pH-метрия|24-hour pH monitoring|endo_room|M|3
manometry|func|Манометрия пищевода|Oesophageal manometry|endo_room|M|3
vng|func|Видеонистагмография|Videonystagmography|ent_room|L|3
xr_sinus|rad|Рентген пазух носа|Sinus X-ray|xr_room|L|2
xr_abdomen|rad|Обзорный рентген живота|Abdominal X-ray|xr_room|L|3
xr_joints|rad|Рентген суставов|Joint X-ray|xr_room|L|1
xr_hip_baby|rad|Рентген тазобедренных суставов у малыша|Hip X-ray in a baby|xr_room|L|3
xr_flatfoot|rad|Рентген стоп на плоскостопие|Foot X-ray for flat feet|xr_room|L|2
xr_scoliosis|rad|Рентген позвоночника на сколиоз|Scoliosis spine X-ray|xr_room|L|2
xr_kids_chest|rad|Рентген лёгких у ребёнка|Chest X-ray in a child|xr_room|L|2
opg|rad|Панорамный снимок зубов (ОПТГ)|Dental panoramic X-ray|dent_xray|L|1
cbct|rad|КТ зубов (КЛКТ)|Dental CBCT scan|dent_xray|L|2
ct_sinus|rad|КТ пазух носа|Sinus CT|ct_room|L|2
ct_spine|rad|КТ позвоночника|Spine CT|ct_room|L|2
ct_kidney|rad|КТ почек (камни)|Kidney stone CT|ct_room|L|2
ct_coronary|rad|КТ-коронарография|CT coronary angiography|ct_room|M|2
ct_calcium|rad|Кальциевый индекс сердца|Coronary calcium score|ct_room|L|3
ct_colono|rad|Виртуальная колоноскопия|CT colonography|ct_room|L|3
ct_joint|rad|КТ сустава|Joint CT|ct_room|L|3
mri_pelvis|rad|МРТ малого таза|Pelvic MRI|mri_room|L|2
mri_prostate|rad|МРТ предстательной железы|Prostate MRI|mri_room|L|2
mri_breast|rad|МРТ молочных желёз|Breast MRI|mri_room|L|3
mri_heart|rad|МРТ сердца|Cardiac MRI|mri_room|L|3
mri_vessels|rad|МР-ангиография сосудов головы|Brain MR angiography|mri_room|L|2
mri_kids|rad|МРТ ребёнку (с седацией)|MRI for a child (with sedation)|mri_room|M|2
mri_pituitary|rad|МРТ гипофиза|Pituitary MRI|mri_room|L|3
scinti_bone|rad|Сцинтиграфия скелета|Bone scan|ct_room|L|3
scinti_thyroid|rad|Сцинтиграфия щитовидной железы|Thyroid scan|ct_room|L|3
hsg|rad|Проверка проходимости маточных труб (ГСГ)|Fallopian tube test (HSG)|xr_room|M|2
sigmoido|endo|Ректороманоскопия|Sigmoidoscopy|endo_room|M|2
ercp|endo|ЭРХПГ|ERCP|endo_room|H|3
eus|endo|Эндосонография (ЭУС)|Endoscopic ultrasound (EUS)|endo_room|M|3
polypectomy|endo|Удаление полипа при колоноскопии|Polyp removal during colonoscopy|endo_room|M|2
fgds_kids|endo|ФГДС ребёнку|Gastroscopy for a child|endo_room|M|3
rhinoscopy|endo|Эндоскопия носа|Nasal endoscopy|ent_room|L|2
uretero|endo|Уретероскопия|Ureteroscopy|uro_room|H|3
inj_sc|proc|Подкожная инъекция|Subcutaneous injection|proc_room|L|1
inj_iv|proc|Внутривенная инъекция|Intravenous injection|proc_room|L|1
insulin_pen|proc|Как делать уколы инсулина|How to inject insulin|home|L|1
glucometer|proc|Как мерить сахар глюкометром|How to check blood sugar at home|home|L|1
bp_home|proc|Как правильно мерить давление дома|How to measure blood pressure at home|home|L|1
nebulizer|proc|Ингаляция через небулайзер|Nebuliser treatment|home|L|1
inhaler|proc|Как пользоваться ингалятором|How to use an inhaler|home|L|1
spacer_kids|proc|Ингалятор со спейсером у ребёнка|Inhaler with spacer for a child|home|L|2
oxygen|proc|Кислородная терапия|Oxygen therapy|ward|L|3
blood_transf|proc|Переливание крови|Blood transfusion|ward|H|3
iron_iv|proc|Капельница с железом|Iron infusion|proc_room|M|2
vit_drip|proc|Витаминная капельница|Vitamin drip|proc_room|M|3
plasma_donation|proc|Сдача крови донором|Blood donation|lab_draw|L|2
nasogastric|proc|Установка назогастрального зонда|Nasogastric tube|ward|M|3
paracentesis|proc|Лапароцентез|Abdominal fluid drainage (paracentesis)|proc_room|H|3
thoracentesis|proc|Плевральная пункция|Pleural tap (thoracentesis)|proc_room|H|3
bone_marrow|proc|Пункция костного мозга|Bone marrow biopsy|proc_room|H|3
liver_biopsy|proc|Биопсия печени|Liver biopsy|proc_room|H|3
kidney_biopsy|proc|Биопсия почки|Kidney biopsy|proc_room|H|3
lymph_biopsy|proc|Биопсия лимфоузла|Lymph node biopsy|proc_room|M|3
trigger_inj|proc|Блокада при боли в спине|Spinal pain injection (nerve block)|proc_room|M|2
prp|proc|PRP-терапия суставов|PRP joint injections|proc_room|M|2
cast|proc|Наложение гипса|Plaster cast|proc_room|L|2
cast_off|proc|Снятие гипса|Cast removal|proc_room|L|2
splint|proc|Ортез и шина после травмы|Splint and brace after injury|proc_room|L|2
ingrown_nail|proc|Удаление вросшего ногтя|Ingrown toenail removal|proc_room|M|2
foreign_body|proc|Удаление инородного тела (заноза, рыболовный крючок)|Foreign body removal|proc_room|M|2
burn_care|proc|Перевязка ожога|Burn dressing|proc_room|M|2
stitches|proc|Наложение швов на рану|Wound stitches|proc_room|M|1
ear_pierce|proc|Прокол мочек ушей|Ear piercing|proc_room|L|2
acne|derm|Приём по акне|Acne consultation|office|L|2
chem_peel|derm|Химический пилинг|Chemical peel|proc_room|M|2
laser_hair|derm|Лазерная эпиляция|Laser hair removal|proc_room|M|2
botox|derm|Ботулинотерапия (ботокс)|Botulinum toxin (Botox)|proc_room|M|2
fillers|derm|Контурная пластика (филлеры)|Dermal fillers|proc_room|M|2
mole_laser|derm|Удаление родинки лазером|Laser mole removal|proc_room|M|2
cyst_removal|derm|Удаление атеромы|Sebaceous cyst removal|proc_room|M|2
keloid|derm|Лечение келоидного рубца|Keloid scar treatment|proc_room|M|3
vitiligo_uv|derm|Фототерапия кожи|Skin phototherapy (UV)|proc_room|L|3
psoriasis|derm|Приём при псориазе|Psoriasis consultation|office|L|2
hyperhidrosis|derm|Лечение потливости|Excessive sweating treatment|proc_room|M|3
hair_loss|derm|Трихоскопия (выпадение волос)|Trichoscopy for hair loss|proc_room|L|2
dent_kids|dent|Первый визит ребёнка к стоматологу|Child's first dental visit|dent_chair|L|1
dent_clean|dent|Профессиональная чистка зубов|Professional teeth cleaning|dent_chair|L|1
fluoride|dent|Фторирование зубов|Fluoride treatment|dent_chair|L|2
milk_tooth|dent|Удаление молочного зуба|Baby tooth extraction|dent_chair|M|2
pulpitis|dent|Лечение пульпита|Pulpitis treatment|dent_chair|M|1
gum_treat|dent|Лечение дёсен (кюретаж)|Gum treatment (deep cleaning)|dent_chair|M|2
veneers|dent|Виниры|Veneers|dent_chair|M|2
bridge|dent|Мостовидный протез|Dental bridge|dent_chair|M|2
denture|dent|Съёмный протез|Removable denture|dent_chair|M|2
aligners|dent|Элайнеры (капы для выравнивания)|Clear aligners|dent_chair|L|2
sinus_lift|dent|Синус-лифтинг|Sinus lift|dent_chair|H|3
bone_graft|dent|Костная пластика перед имплантацией|Bone graft before implant|dent_chair|H|3
night_guard|dent|Капа от бруксизма|Night guard for teeth grinding|dent_chair|L|2
dent_sedation|dent|Лечение зубов под седацией|Dental treatment under sedation|dent_chair|M|3
dent_kids_ga|dent|Лечение зубов ребёнку под наркозом|Dental treatment for a child under anaesthesia|dent_chair|H|3
tooth_sens|dent|Лечение чувствительности зубов|Sensitive teeth treatment|dent_chair|L|2
inlay|dent|Вкладка на зуб|Dental inlay|dent_chair|M|3
dent_xray_bw|dent|Прицельный снимок зуба|Dental bitewing X-ray|dent_xray|L|1
eye_kids|eye|Проверка зрения у ребёнка|Eye test for a child|eye_room|L|1
glasses|eye|Подбор очков|Glasses prescription|eye_room|L|1
contacts|eye|Подбор контактных линз|Contact lens fitting|eye_room|L|2
perimetry|eye|Поля зрения (периметрия)|Visual field test|eye_room|L|2
dilated|eye|Осмотр с расширением зрачка|Dilated eye exam|eye_room|L|1
gonioscopy|eye|Гониоскопия|Gonioscopy|eye_room|L|3
dry_eye|eye|Диагностика сухого глаза|Dry eye testing|eye_room|L|2
eye_inj|eye|Укол в глаз (интравитреальная инъекция)|Eye injection (intravitreal)|eye_room|M|2
laser_retina|eye|Лазерная коагуляция сетчатки|Retinal laser treatment|eye_room|M|3
yag|eye|ЯГ-лазер после катаракты|YAG laser after cataract surgery|eye_room|M|3
chalazion|eye|Удаление халязиона|Chalazion removal|eye_room|M|2
tear_duct|eye|Зондирование слёзного канала у малыша|Tear duct probing in a baby|eye_room|M|3
strabismus|eye|Операция при косоглазии|Strabismus surgery|or_room|H|3
glaucoma_laser|eye|Лазерное лечение глаукомы|Glaucoma laser treatment|eye_room|M|3
eye_angio|eye|Флюоресцентная ангиография глаза|Eye fluorescein angiography|eye_room|M|3
ent_visit|ent|Приём ЛОР-врача|ENT consultation|ent_room|L|1
ent_kids|ent|ЛОР-осмотр ребёнка|ENT check for a child|ent_room|L|1
ear_tubes|ent|Шунтирование барабанной перепонки|Ear tubes (grommets)|or_room|H|3
paracentesis_ear|ent|Прокол барабанной перепонки|Eardrum puncture (myringotomy)|ent_room|M|3
tonsil_wash|ent|Промывание миндалин|Tonsil washing|ent_room|L|2
nose_bleed|ent|Остановка носового кровотечения|Nosebleed treatment|ent_room|M|2
nasal_polyps|ent|Удаление полипов носа|Nasal polyp removal|or_room|H|3
sinus_surg|ent|Операция на пазухах (FESS)|Sinus surgery (FESS)|or_room|H|3
turbinate|ent|Радиоволновая конхотомия|Turbinate reduction|ent_room|M|3
hearing_aid|ent|Подбор слухового аппарата|Hearing aid fitting|ent_room|L|2
oae_baby|ent|Аудиоскрининг новорождённого|Newborn hearing screening|ent_room|L|1
vestibular|ent|Обследование при головокружении|Dizziness assessment|ent_room|L|2
snoring|ent|Лечение храпа|Snoring treatment|ent_room|M|3
preg_first|gyn|Постановка на учёт по беременности|First pregnancy visit|gyn_chair|L|1
preg_visits|gyn|Плановые визиты при беременности|Routine pregnancy check-ups|gyn_chair|L|1
gtt_preg|gyn|Глюкозотест при беременности|Glucose test in pregnancy|lab_draw|L|1
amnio|gyn|Амниоцентез|Amniocentesis|us_room|H|3
cvs|gyn|Биопсия ворсин хориона|Chorionic villus sampling|us_room|H|3
postpartum|gyn|Осмотр после родов|Postpartum check-up|gyn_chair|L|1
breastfeed|gyn|Консультация по грудному вскармливанию|Breastfeeding consultation|office|L|2
epidural|gyn|Эпидуральная анестезия в родах|Epidural in labour|ward|H|2
induction|gyn|Стимуляция родов|Labour induction|ward|H|2
abortion_med|gyn|Медикаментозное прерывание беременности|Medical abortion|gyn_chair|H|3
miscarriage|gyn|Помощь при выкидыше|Miscarriage care|gyn_chair|H|3
ectopic|gyn|Внематочная беременность|Ectopic pregnancy treatment|or_room|H|3
erosion|gyn|Лечение эрозии шейки матки|Cervical erosion treatment|gyn_chair|M|2
leep|gyn|Конизация шейки матки|Cervical cone biopsy (LEEP)|gyn_chair|H|3
cervix_biopsy|gyn|Биопсия шейки матки|Cervical biopsy|gyn_chair|M|2
endometrial|gyn|Пайпель-биопсия эндометрия|Endometrial biopsy|gyn_chair|M|2
contraception|gyn|Подбор контрацепции|Choosing contraception|office|L|1
implant_contra|gyn|Контрацептивный имплант|Contraceptive implant|proc_room|M|3
menopause|gyn|Приём при менопаузе|Menopause consultation|office|L|2
ovary_cyst|gyn|Лапароскопия кисты яичника|Ovarian cyst laparoscopy|or_room|H|3
iui|gyn|Внутриматочная инсеминация|Intrauterine insemination (IUI)|gyn_chair|M|3
egg_freeze|gyn|Заморозка яйцеклеток|Egg freezing|gyn_chair|H|3
pelvic_floor|gyn|Тренировка мышц тазового дна|Pelvic floor training|rehab_room|L|2
mammologist|gyn|Приём маммолога|Breast specialist consultation|office|L|1
uro_kids|uro|Приём детского уролога|Paediatric urology visit|uro_room|L|2
vasectomy|uro|Вазэктомия|Vasectomy|or_room|H|3
varicocele|uro|Операция при варикоцеле|Varicocele surgery|or_room|H|3
hydrocele|uro|Операция при водянке яичка|Hydrocele surgery|or_room|H|3
turp|uro|ТУР простаты|Prostate surgery (TURP)|or_room|H|3
kidney_stone_lith|uro|Контактная литотрипсия|Laser kidney stone removal|or_room|H|3
bladder_inst|uro|Инстилляция мочевого пузыря|Bladder instillation|uro_room|M|3
urodynamics|uro|Уродинамическое исследование|Urodynamic test|uro_room|M|3
ed_treat|uro|Лечение эректильной дисфункции|Erectile dysfunction treatment|office|L|2
prostate_massage|uro|Секрет простаты|Prostate fluid test|uro_room|M|3
catheter_home|uro|Уход за катетером дома|Caring for a urinary catheter at home|home|L|3
cystostomy|uro|Замена цистостомы|Suprapubic catheter change|uro_room|M|3
cardiologist|cardio|Приём кардиолога|Cardiology consultation|office|L|1
angiography_legs|cardio|Ангиография сосудов ног|Leg angiography|cath_lab|H|3
carotid_stent|cardio|Стентирование сонной артерии|Carotid stenting|cath_lab|H|3
cardioversion|cardio|Кардиоверсия|Cardioversion|ward|H|3
icd|cardio|Имплантация кардиовертера-дефибриллятора|ICD implantation|cath_lab|H|3
pacemaker_check|cardio|Проверка кардиостимулятора|Pacemaker check|func_room|L|2
sclerotherapy|cardio|Склеротерапия вен|Vein sclerotherapy|proc_room|M|2
compression|cardio|Подбор компрессионного трикотажа|Compression stockings fitting|office|L|2
cabg|cardio|Аортокоронарное шунтирование|Coronary bypass surgery (CABG)|or_room|H|3
valve|cardio|Замена клапана сердца|Heart valve replacement|or_room|H|3
lap_chole_prep|surg|Подготовка к лапароскопии|Preparing for laparoscopic surgery|ward|M|1
hernia_post|surg|Послеоперационная грыжа|Incisional hernia repair|or_room|H|3
fissure|surg|Лечение анальной трещины|Anal fissure treatment|proc_room|M|2
pilonidal|surg|Удаление эпителиального копчикового хода|Pilonidal sinus surgery|or_room|H|3
hemorrhoid_band|surg|Лигирование геморроя кольцами|Haemorrhoid banding|proc_room|M|2
varicose_surg|surg|Флебэктомия|Varicose vein surgery|or_room|H|3
carpal|surg|Операция при туннельном синдроме запястья|Carpal tunnel release|or_room|H|2
trigger_finger|surg|Операция при щёлкающем пальце|Trigger finger release|proc_room|M|3
bunion|surg|Операция на косточке стопы (Hallux valgus)|Bunion surgery|or_room|H|3
acl|surg|Пластика передней крестообразной связки|ACL reconstruction|or_room|H|3
shoulder_scope|surg|Артроскопия плеча|Shoulder arthroscopy|or_room|H|3
fracture_fix|surg|Металлоостеосинтез при переломе|Fracture fixation surgery|or_room|H|2
implant_removal|surg|Удаление металлоконструкции|Hardware removal after fracture|or_room|H|3
bariatric|surg|Бариатрическая операция|Weight-loss surgery|or_room|H|3
breast_lump|surg|Секторальная резекция молочной железы|Breast lump removal|or_room|H|3
mastectomy|surg|Мастэктомия|Mastectomy|or_room|H|3
colectomy|surg|Резекция кишки|Bowel resection|or_room|H|3
stomach_surg|surg|Операция на желудке|Stomach surgery|or_room|H|3
spleen|surg|Удаление селезёнки|Splenectomy|or_room|H|3
adrenal|surg|Удаление надпочечника|Adrenalectomy|or_room|H|3
nephrectomy|surg|Удаление почки|Nephrectomy|or_room|H|3
spine_fusion|surg|Спондилодез|Spinal fusion|or_room|H|3
brain_tumor|surg|Операция на головном мозге|Brain surgery|or_room|H|3
hernia_kids|surg|Операция при паховой грыже у ребёнка|Inguinal hernia repair in a child|or_room|H|2
phimosis_kids|surg|Лечение фимоза у мальчика|Phimosis treatment in a boy|uro_room|M|2
cleft|surg|Операция при расщелине губы и нёба|Cleft lip and palate surgery|or_room|H|3
plastic_eyelid|surg|Блефаропластика|Eyelid surgery (blepharoplasty)|or_room|H|3
rhinoplasty|surg|Ринопластика|Rhinoplasty|or_room|H|3
liposuction|surg|Липосакция|Liposuction|or_room|H|3
breast_aug|surg|Увеличение груди|Breast augmentation|or_room|H|3
anest_kids|anest|Наркоз у ребёнка|Anaesthesia for a child|or_room|H|2
nerve_block|anest|Проводниковая анестезия|Nerve block anaesthesia|or_room|H|3
preop|anest|Осмотр анестезиолога перед операцией|Pre-operative anaesthesia assessment|office|M|1
stroke_rehab|rehab|Реабилитация после инсульта|Rehabilitation after stroke|rehab_room|L|2
knee_rehab|rehab|Реабилитация после замены сустава|Rehabilitation after joint replacement|rehab_room|L|2
cardio_rehab|rehab|Кардиореабилитация|Cardiac rehabilitation|rehab_room|L|3
back_rehab|rehab|Лечебная гимнастика при боли в спине|Exercise therapy for back pain|rehab_room|L|1
kinesio|rehab|Кинезиотейпирование|Kinesiology taping|rehab_room|L|2
electro|rehab|Электрофорез|Electrophoresis|rehab_room|L|2
magnet|rehab|Магнитотерапия|Magnetic therapy|rehab_room|L|2
ultrasound_ther|rehab|Ультразвуковая терапия|Therapeutic ultrasound|rehab_room|L|3
laser_ther|rehab|Лазеротерапия|Low-level laser therapy|rehab_room|L|3
hydro|rehab|Гидрокинезотерапия (бассейн)|Hydrotherapy|rehab_room|L|3
kids_massage|rehab|Массаж ребёнку|Massage for a baby|rehab_room|L|1
speech|rehab|Занятия с логопедом|Speech therapy|office|L|2
ot|rehab|Эрготерапия|Occupational therapy|rehab_room|L|3
acupuncture|rehab|Иглорефлексотерапия|Acupuncture|rehab_room|L|2
manual|rehab|Мануальная терапия|Manual therapy|rehab_room|M|2
neurologist|visit|Приём невролога|Neurology consultation|office|L|1
endocrinologist|visit|Приём эндокринолога|Endocrinology consultation|office|L|1
gastro|visit|Приём гастроэнтеролога|Gastroenterology consultation|office|L|1
pulmonologist|visit|Приём пульмонолога|Pulmonology consultation|office|L|2
allergist|visit|Приём аллерголога|Allergy consultation|office|L|2
rheumatologist|visit|Приём ревматолога|Rheumatology consultation|office|L|2
nephrologist|visit|Приём нефролога|Nephrology consultation|office|L|3
hematologist|visit|Приём гематолога|Haematology consultation|office|L|3
oncologist|visit|Приём онколога|Oncology consultation|office|L|2
surgeon|visit|Приём хирурга|Surgical consultation|office|L|1
orthopedist|visit|Приём травматолога-ортопеда|Orthopaedic consultation|office|L|1
psychiatrist|visit|Приём психиатра|Psychiatric consultation|office|L|2
psychologist|visit|Приём психолога|Psychologist session|office|L|1
psychotherapist|visit|Приём психотерапевта|Psychotherapy session|office|L|2
infectious|visit|Приём инфекциониста|Infectious disease consultation|office|L|3
dermatologist|visit|Приём дерматолога|Dermatology consultation|office|L|1
geneticist|visit|Приём генетика|Genetic counselling|office|L|3
nutritionist|visit|Приём диетолога|Dietitian consultation|office|L|2
sports_med|visit|Допуск к спорту|Sports medical clearance|office|L|2
driver_cert|visit|Медкомиссия для водительских прав|Driver's medical exam|office|L|1
work_cert|visit|Профосмотр для работы|Occupational health check|office|L|1
school_cert|visit|Справка в школу и детский сад|School and kindergarten health form|office|L|1
newborn_visit|visit|Первый осмотр новорождённого|Newborn first check|office|L|1
baby_month|visit|Осмотр малыша в 1 месяц|One-month baby check|office|L|1
teen_check|visit|Осмотр подростка|Teen health check|office|L|2
elderly_check|visit|Профилактический осмотр после 60|Health check after 60|office|L|2
telemed|visit|Онлайн-консультация врача|Online doctor consultation|home|L|1
emergency|visit|Что делать в приёмном покое|What happens in the emergency room|ward|L|1
ambulance|visit|Когда и как вызывать скорую|When and how to call an ambulance|home|L|1
hospital_stay|visit|Госпитализация: что взять и что будет|Going into hospital: what to bring|ward|L|1
discharge|visit|Выписка из больницы|Hospital discharge|ward|L|2
vacc_hpv|vacc|Прививка от ВПЧ|HPV vaccine|proc_room|L|2
vacc_hepb|vacc|Прививка от гепатита B|Hepatitis B vaccine|proc_room|L|2
vacc_tetanus|vacc|Прививка от столбняка (АДС)|Tetanus booster|proc_room|L|2
vacc_measles|vacc|Прививка от кори (КПК)|MMR vaccine|proc_room|L|1
vacc_pneumo|vacc|Прививка от пневмококка|Pneumococcal vaccine|proc_room|L|2
vacc_covid|vacc|Прививка от COVID-19|COVID-19 vaccine|proc_room|L|2
vacc_travel|vacc|Прививки перед поездкой|Travel vaccines|proc_room|L|3
vacc_rabies|vacc|Прививка от бешенства после укуса|Rabies vaccine after a bite|proc_room|M|2
vacc_bcg|vacc|БЦЖ новорождённому|BCG vaccine for a newborn|proc_room|L|1
vacc_rota|vacc|Прививка от ротавируса|Rotavirus vaccine|proc_room|L|2
vacc_preg|vacc|Прививки при беременности|Vaccines in pregnancy|proc_room|L|2
vacc_chickenpox|vacc|Прививка от ветрянки|Chickenpox vaccine|proc_room|L|3
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
