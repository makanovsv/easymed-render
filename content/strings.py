"""Общие фразы роликов по языкам: подписи глав на экране и связки в озвучке.

Ключи: tell, prep, bring, steps, feel, dur, after, red, outro, disclaimer, kicker.
"""

S = {
    "ru": dict(kicker="как проходит", tell="Обязательно скажите врачу", prep="Как подготовиться", bring="Что взять с собой",
               steps="Как всё проходит", feel="Что вы почувствуете", dur="Сколько длится", after="После", red="Сразу обратитесь к врачу, если",
               disclaimer="Это видео не заменяет консультацию врача. Всегда следуйте инструкциям своей клиники.",
               outro="EasyMed Global. Заранее знать — спокойнее. Подпишитесь на канал, чтобы не пропустить новые видео."),
    "en": dict(kicker="what to expect", tell="Be sure to tell your doctor", prep="How to prepare", bring="What to bring",
               steps="How it goes", feel="What you'll feel", dur="How long it takes", after="Afterwards", red="Contact a doctor straight away if",
               disclaimer="This video does not replace a consultation with a doctor. Always follow your clinic's instructions.",
               outro="EasyMed Global. Knowing in advance is calmer. Subscribe so you don't miss new videos."),
    "kk": dict(kicker="қалай өтеді", tell="Дәрігерге міндетті түрде айтыңыз", prep="Қалай дайындалу керек", bring="Өзіңізбен не алу керек",
               steps="Бәрі қалай өтеді", feel="Не сезінесіз", dur="Қанша уақыт алады", after="Кейін", red="Мына жағдайда бірден дәрігерге барыңыз",
               disclaimer="Бұл бейне дәрігер кеңесінің орнын баспайды. Әрқашан клиникаңыздың нұсқауларын орындаңыз.",
               outro="EasyMed Global. Алдын ала білу — тынышырақ. Жаңа бейнелерді жіберіп алмау үшін арнаға жазылыңыз."),
    "es": dict(kicker="qué esperar", tell="Díselo siempre a tu médico", prep="Cómo prepararte", bring="Qué llevar",
               steps="Cómo es", feel="Qué sentirás", dur="Cuánto dura", after="Después", red="Acude al médico de inmediato si",
               disclaimer="Este video no sustituye la consulta con un médico. Sigue siempre las instrucciones de tu clínica.",
               outro="EasyMed Global. Saber de antemano da más tranquilidad. Suscríbete para no perderte los nuevos videos."),
    "pt": dict(kicker="o que esperar", tell="Avise sempre o seu médico", prep="Como se preparar", bring="O que levar",
               steps="Como é feito", feel="O que você vai sentir", dur="Quanto tempo leva", after="Depois", red="Procure um médico imediatamente se",
               disclaimer="Este vídeo não substitui a consulta com um médico. Siga sempre as orientações da sua clínica.",
               outro="EasyMed Global. Saber antes deixa tudo mais tranquilo. Inscreva-se para não perder os novos vídeos."),
    "ar": dict(kicker="ماذا تتوقع", tell="أخبر طبيبك دائمًا", prep="كيف تستعد", bring="ماذا تحضر معك",
               steps="كيف يتم", feel="ماذا ستشعر", dur="كم يستغرق", after="بعد ذلك", red="اتصل بالطبيب فورًا إذا",
               disclaimer="هذا الفيديو لا يغني عن استشارة الطبيب. اتبع دائمًا تعليمات عيادتك.",
               outro="EasyMed Global. المعرفة المسبقة تمنحك الطمأنينة. اشترك في القناة حتى لا تفوتك الفيديوهات الجديدة."),
    "zh": dict(kicker="会经历什么", tell="一定要告诉医生", prep="如何准备", bring="需要带什么",
               steps="检查过程", feel="你会有什么感觉", dur="需要多长时间", after="之后", red="出现以下情况请立即就医",
               disclaimer="本视频不能替代医生的诊疗建议。请始终遵循你所在医院的要求。",
               outro="EasyMed Global。提前了解，更加安心。 订阅频道，不错过新视频。"),
    "ja": dict(kicker="どんな流れか", tell="必ず医師に伝えること", prep="準備のしかた", bring="持ち物",
               steps="検査の流れ", feel="感じること", dur="かかる時間", after="終わったあと", red="すぐに医師に連絡してほしいとき",
               disclaimer="この動画は医師の診察の代わりにはなりません。必ずかかっている医療機関の指示に従ってください。",
               outro="EasyMed Global。前もって知っておけば、安心です。 新しい動画を見逃さないよう、チャンネル登録をお願いします。"),
    "ko": dict(kicker="어떻게 진행되나요", tell="꼭 의사에게 알리세요", prep="준비 방법", bring="챙겨 갈 것",
               steps="진행 과정", feel="어떤 느낌일까요", dur="걸리는 시간", after="검사 후", red="이럴 때는 바로 의사에게 연락하세요",
               disclaimer="이 영상은 의사의 진료를 대신하지 않습니다. 항상 병원의 안내를 따르세요.",
               outro="EasyMed Global. 미리 알면 더 편안합니다. 새 영상을 놓치지 않도록 채널을 구독해 주세요."),
}

VOICE = {"ru": "ru-RU-DmitryNeural", "en": "en-US-AndrewNeural", "kk": "kk-KZ-DauletNeural", "es": "es-MX-JorgeNeural",
         "pt": "pt-BR-AntonioNeural", "ar": "ar-SA-HamedNeural", "zh": "zh-CN-YunyangNeural", "ja": "ja-JP-KeitaNeural",
         "ko": "ko-KR-InJoonNeural"}
LANGS = list(S)
