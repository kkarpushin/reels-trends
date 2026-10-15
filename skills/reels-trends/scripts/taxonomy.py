"""Default label taxonomy for any niche. Names are shown in the report (ru or en); hints are for the labelling agents.
Override per run with config.json -> "labels": {"formats": [[name, hint], ...], "creators": [...], "speech": [...]}.
"""
FORMATS = [
    ('Процесс крупным планом, ASMR', 'Process close-up, ASMR', 'the work itself in close-up (hands, tools, product), little or no explanation; calm and aesthetic'),
    ('Процесс + обучающий текст на экране', 'Footage + educational on-screen text', 'real footage with an educational overlay for customers: a thesis, anatomy, a diagram, 1-3 lines; nobody talks'),
    ('Зрелище: необычный процесс', 'Spectacle: unusual process', 'shock or novelty value of what happens: extreme, rare, satisfying, dramatic'),
    ('Видимый результат, до / после', 'Visible result, before / after', 'the result is the point: before/after, transformation, measurable change'),
    ('Клиентский путь: сходи со мной', 'Customer journey: come with me', 'POV or vlog of a customer going through the service step by step, often with the price'),
    ('Реакция или отзыв клиента', 'Customer reaction or testimonial', "the customer's emotions or words are the point"),
    ('Урок для профессионалов', 'Lesson for professionals', 'teaches peers a technique, protocol or business skill'),
    ('Сделай сам: повтори дома', 'DIY: try it at home', 'teaches the viewer to do it themselves (self-care, recipe, routine, exercise)'),
    ('Эксперт объясняет, разбор мифа', 'Expert explains, myth busting', 'a person talks to camera or a voice-over explains why; myths, mistakes, warnings'),
    ('Тир-лист и быстрые вердикты', 'Tier list and quick verdicts', 'rapid ratings: top or trash, yes or no, 0 of 10'),
    ('Скетч и юмор', 'Skit and humour', "skits, memes, 'types of customers', work life, funny animals"),
    ('Атмосфера и промо', 'Atmosphere and promo', 'cinematic showcase of the place, team or product without a story'),
    ('Тест товара', 'Product test', 'a product or gadget is demonstrated, tested or reviewed'),
    ('Цена, акция, оффер', 'Price, deal, offer', 'price, discount, giveaway or booking offer is the main message'),
    ('Тренд, липсинк, танец', 'Trend, lip-sync, dance', 'a trend format where the niche is only a backdrop'),
    ('AI-генерация', 'AI-generated', 'AI-generated or AI-animated video or images'),
    ('Другое', 'Other', 'none of the above'),
]
CREATORS = [
    ('Бизнес: салон, клиника, магазин', 'Business: salon, clinic, shop'),
    ('Частный специалист', 'Independent specialist'),
    ('Школа или курсы', 'School or courses'),
    ('Блогер или клиент', 'Blogger or customer'),
    ('Бренд или продавец товара', 'Brand or product seller'),
    ('Медиа или паблик', 'Media or public page'),
    ('Другое', 'Other'),
]
SPEECH = [
    ('Говорит в кадре', 'Talks to camera'),
    ('Закадровый голос', 'Voice-over'),
    ('Только текст на экране', 'On-screen text only'),
    ('Без слов: звук или музыка', 'No words: sound or music'),
]
LANG_NAMES = {'ru': 'Russian', 'en': 'English', 'uk': 'Ukrainian', 'es': 'Spanish', 'pt': 'Portuguese', 'de': 'German', 'kk': 'Kazakh'}


def taxonomy(cfg):
    i = 0 if cfg['report_language'] == 'ru' else 1
    lab = cfg.get('labels') or {}
    formats = [tuple(x) for x in lab['formats']] if lab.get('formats') else [(f[i], f[2]) for f in FORMATS]
    creators = list(lab['creators']) if lab.get('creators') else [c[i] for c in CREATORS]
    speech = list(lab['speech']) if lab.get('speech') else [s[i] for s in SPEECH]
    return formats, creators, speech
