# content.json and overrides.json

## work/overrides.json (your review of the agents' labels)

```json
{
  "patch": {"DdqjlCHhc3r": {"relevant": false}, "DeBgSNVy0Ve": {"format": "Процесс крупным планом, ASMR"}},
  "flagged": {"DdZ015oJcUy": "sexualised", "DeH9KF9Rxsl": "repost"},
  "unflag": ["DeEwMdhyz0H"]
}
```

- `patch` changes any label field of a reel.
- `flagged` keeps a reel in the data but leaves it out of the format table and ideas; the grid hides it until the viewer presses the button. Use it for content you would not tell a business to copy: sexualised content farms, reposts of someone else's video, scams.
- `unflag` removes a flag an agent set.
- Rules that must be the same for every batch (what counts as relevant, how to treat testimonials, AI animations, exercise-only clips) belong here, not in your head.

## RUN/content.json (the report text)

You write it after `stats.py`, in the report language. Every number in it must come from `work/stats.json` or a snippet you ran over the data.

```json
{
  "meta": {
    "title": "Массажные Reels мира",
    "eyebrow": "Instagram Reels · массаж · весь мир",
    "h1": "Что залетело у массажистов в Reels за месяц",
    "lede": "5 308 рилсов о массаже на 37 языках, опубликованных с 15 сентября по 15 октября 2026 года. Каждый ролик сравнили с обычным уровнем просмотров его автора, чтобы увидеть, что выстрелило благодаря формату, а не за счёт большой аудитории.",
    "period": "15.09–15.10.2026",
    "flaggedLabel": "контент-фермы",
    "formatsNote": "Разметка 185 лидеров по четырём кадрам видео, подписи и речи. «Медиана ×» показывает, во сколько раз ролик обогнал обычные просмотры автора.",
    "topicsNote": "По всем рилсам. Тема определена по подписи и хэштегам.",
    "geoNote": "Язык определён по подписи. В таблице языки, где нашлось от 30 рилсов.",
    "countriesNote": "Страна из раздела Instagram «Об этом аккаунте» для авторов-лидеров.",
    "gridNote": "Лидеры месяца. Цифра на обложке показывает, во сколько раз рилс обогнал медиану своего автора.",
    "ideasTitle": "Что снять в ближайший месяц",
    "ideasNote": "Сценарии из форматов, которые сработали. У каждого есть ссылки на образцы.",
    "hooksNote": "Дословно из первых секунд лидеров. Сверху перевод, ниже оригинал.",
    "audioNote": "70% рилсов на оригинальном звуке.",
    "tagsNote": "Самые частые хэштеги и медиана просмотров рилсов с ними.",
    "method": ["<b>Сбор.</b> ...", "<b>× к медиане автора.</b> ...", "<b>Ограничения.</b> ...", "<b>Стоимость.</b> ..."]
  },
  "findings": [{"title": "Формат сезона: анатомия поверх массажа", "body": "17 лидеров на семи языках... Медиана ×360..."}],
  "formats": {"Процесс крупным планом, ASMR": "Руки, масло, звук процедуры. Без объяснений"},
  "topics": {"Банки и скрейпинг": "Зрелище и финал со следами: 50 банок разом (19,6 млн)"},
  "langMin": 30,
  "langs": {"RU": "Самомассаж лица, банки на холку, head spa с ценой в хуке"},
  "ideas": [{"title": "Анатомия поверх вашего массажа", "hook": "Вот что происходит с узлом в трапеции, когда я на него давлю",
             "why": "17 лидеров на семи языках, медиана ×360. Бразильский ролик набрал 4,2 млн (×1341).", "refs": ["DdZxo29NKV9", "Dd9gBrNMBf5"]}],
  "hooks": ["DdZxo29NKV9", "DdX-iYaB36J"]
}
```

`meta.spent` is filled from the spend ledger unless you set it. `method` items may contain `<b>`; everything else is plain text.

## What to write

**Findings (6-7).** Each is one claim a business owner can act on, with the number that proves it and one concrete example. Good findings from real runs:
- a format that over-performs across several languages (with how many leaders, their median ×, the best example);
- which topics fly relative to the author (× by topic) and which sell but do not travel;
- a gap: a trend big in one language and nearly absent in the user's market, with counts from both (only after checking you searched it in the user's language);
- how leaders talk: on-screen text vs speech vs no words (`leaders_by_speech`);
- reach vs followers (`by_followers`) and length (`by_duration`);
- who wins the top multipliers and whether it is copyable (flagged content farms, reposts, AI pages).

**Format and topic notes.** One short line each: what the leaders in that group actually do, with a quote or a number. A format with fewer than 5 leaders gets "few reels" in the note.

**Language notes.** For each language row: the 1-2 things that fly there, with a country if `about.py` ran.

**Ideas (8-10).** Ready to shoot for the user's business: a title, a hook in the report language that the user can say or put on screen in the first second, why it works with numbers from this run, and 2-3 reel codes as examples. Prefer formats a small business can film in an hour with a phone. Do not base ideas on flagged reels.

**Hooks (12-16 codes).** First seconds of leaders with a clear on-screen text or first sentence; mix languages, formats and countries. Leave out flagged reels and hooks that are only hashtags.

**Method.** How the data was collected (queries, languages, window, views floors), the filters and how many reels were dropped, how × is computed and for how many reels, how leaders were chosen and labelled, limitations, cost.

## Style

Plain, concrete sentences. Numbers in the report language's format (`4,2 млн`, `×1341`). Name the example instead of describing it vaguely ("Бразильский ролик, где узел распускается под пальцами, 4,2 млн"). No marketing adjectives.
