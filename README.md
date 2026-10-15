# reels-trends: что залетает в Instagram Reels в вашей нише

Скилл для [Claude Code](https://claude.com/claude-code). Вы пишете Claude обычным языком, например «что залетает в рилс у кофеен Алматы за последний месяц», а он сам:

1. подбирает поисковые запросы и хэштеги на языках нужных рынков;
2. собирает через [Apify](https://apify.com) рилсы за выбранный период, от сотен до нескольких тысяч;
3. сравнивает каждый ролик с обычными просмотрами его автора, чтобы отделить залетевший формат от просто большого аккаунта;
4. отбирает лидеров, скачивает кадры из их видео и размечает формат, тему, хук первых секунд и причину успеха;
5. собирает HTML-отчёт: главные выводы, таблицы форматов, тем и языков, сетка лидеров с фильтрами, первые секунды лидеров и 8–10 готовых сценариев для съёмки со ссылками на образцы.

Один прогон по одному рынку обычно стоит $1–5 на Apify, мировое исследование на 19 языках стоило $13.

## Что понадобится

- **Claude Code**, установленный и залогиненный ([инструкция](https://docs.claude.com/en/docs/claude-code/overview)).
- **Аккаунт Apify** и его API-токен. Бесплатный тариф даёт $5 в месяц, этого хватит на небольшое исследование, но поиск там слабее (подробности ниже). Для регулярной работы лучше любой платный тариф.
- **Python 3.9+** с двумя пакетами и, желательно, **ffmpeg** (по кадрам видео Claude понимает, что происходит в ролике).

## Установка

### Вариант 1. Плагином (удобно обновлять)

В Claude Code выполните по очереди:

```
/plugin marketplace add kkarpushin/reels-trends
/plugin install reels-trends@kkarpushin
```

Обновление позже: `/plugin`, раздел Marketplaces, `kkarpushin`, Update marketplace.

### Вариант 2. Скопировать папку скилла

```bash
git clone https://github.com/kkarpushin/reels-trends.git
cp -r reels-trends/skills/reels-trends ~/.claude/skills/
```

Копируйте именно папку `skills/reels-trends`, а не весь репозиторий.

### Пакеты Python и ffmpeg

```bash
pip install lingua-language-detector pillow
```

Если `pip` ругается на системный Python, добавьте `--user` или используйте виртуальное окружение. ffmpeg: на macOS `brew install ffmpeg`, на Ubuntu `sudo apt install ffmpeg`, на Windows `winget install ffmpeg`.

### Токен Apify

1. Зарегистрируйтесь на [apify.com](https://apify.com).
2. Откройте [Settings → API & Integrations](https://console.apify.com/settings/integrations) и скопируйте Personal API token.
3. Сохраните его в файл (macOS, Linux):

```bash
mkdir -p ~/.config/reels-trends
read -s T && echo "$T" > ~/.config/reels-trends/apify_token && chmod 600 ~/.config/reels-trends/apify_token
```

После `read -s` вставьте токен и нажмите Enter, на экране он не отобразится. На Windows проще задать переменную окружения: `setx APIFY_TOKEN "ваш_токен"` и перезапустить терминал.

Токен даёт доступ к вашему балансу Apify: не публикуйте его и не коммитьте в репозитории.

## Как пользоваться

Откройте Claude Code в любой папке и напишите задачу своими словами:

- «Что залетает в Reels у кофеен Алматы за последние 30 дней? Бюджет $3.»
- «Сделай исследование трендов Reels для стоматологий в Украине и Польше за сентябрь.»
- «Что залетает у фитнес-тренеров по всему миру за последние две недели? Отчёт на английском.»

Можно вызвать скилл и явно: `/reels-trends` (или `/reels-trends:reels-trends`, если ставили плагином).

Claude задаст 2–3 уточняющих вопроса: рынки, период, бюджет. Перед поиском он покажет, сколько это может стоить в худшем случае. Дальше всё идёт само: поиск занимает 5–25 минут, весь прогон с разметкой от 30 минут до полутора часов.

Результат будет в папке `reels-research/<название>/report/`:

- `index.html`: отчёт, откройте в браузере;
- `reels.json`: все найденные рилсы с цифрами и разметкой;
- `artifact.html`: та же страница для публикации артефактом в Claude, если у вас есть такая возможность.

## Как читать отчёт

Главная цифра в отчёте называется **×**: во сколько раз ролик обогнал медиану просмотров последних видео своего автора. ×50 у аккаунта с обычными 2 000 просмотров означает 100 000 просмотров: этот ролик выстрелил благодаря содержанию, а не размеру аккаунта. Поэтому в лидерах много маленьких аккаунтов, и это нормально.

Поиск Instagram отдаёт самые заметные ролики, а не все, поэтому средние цифры в отчёте выше, чем у обычного аккаунта. Сравнивайте форматы и темы между собой.

## Бесплатный и платный Apify

| | бесплатный ($5 в месяц) | платный |
|---|---|---|
| поиск | хэштеги и ключевые слова, Apify берёт деньги и за старые посты, свежих бывает 10–30% | поиск с фильтром по датам и просмотрам, промахи бесплатны |
| страна автора | нет | есть |
| расшифровка речи | по 5 ссылок за запуск | без ограничений |
| разумный масштаб | 1–2 языка, окно 30–60 дней | весь мир |

Скилл сам определяет тариф и выбирает способ поиска.

## Стоимость (цены Apify на октябрь 2026)

| шаг | цена | один рынок | весь мир |
|---|---|---|---|
| поиск рилсов | $0.0011–0.0026 за ролик | $1–2 | $6.5 |
| профили авторов | $0.002–0.0026 за профиль | $0.5–1 | $4.4 |
| страна авторов-лидеров | $0.007 за профиль | $0.4 | $1.4 |
| расшифровка речи | около $0.005 за ролик | $0.3 | $0.9 |

Скрипты не запускают ничего сверх бюджета, который вы назвали. Все траты записываются в `work/spend.jsonl` внутри папки исследования.

## Что внутри

```
skills/reels-trends/
  SKILL.md          порядок работы для Claude
  scripts/          шаги пайплайна: check, search, merge, profiles, score, leaders,
                    transcripts, about, media, batches, labels, stats, build
  assets/           шаблон отчёта и инструкция для разметки
  references/       как писать конфиг и тексты отчёта, грабли из реальных прогонов, примеры конфигов
```

Скрипты можно запускать и вручную: `python3 scripts/<шаг>.py <папка исследования>`. Описание полей конфига лежит в `references/config.md`.

## Ограничения

- Используются сторонние акторы Apify (`memo23/instagram-reels-search-scraper`, `apify/instagram-hashtag-scraper`, `apify/instagram-profile-scraper`, `apple_yang/instagram-transcripts-scraper`). Если автор актора поменяет его, скилл может потребовать правок.
- Собираются только публичные данные Instagram. Используйте их для анализа, а не для перепубликации чужих роликов.
- Кадры и обложки скачиваются на ваш компьютер и в отчёт; ссылки Instagram на видео живут несколько дней.

## Лицензия

MIT. Автор: Константин Карпушин.

---

### English

A Claude Code skill that researches what goes viral on Instagram Reels for any niche, market and period. It searches through Apify in the languages of your markets, scores every reel against its author's median views, labels the leaders' formats from video frames and builds an HTML report with findings and ready-to-shoot ideas. Install with `/plugin marketplace add kkarpushin/reels-trends` and `/plugin install reels-trends@kkarpushin`, save your Apify token to `~/.config/reels-trends/apify_token` (or `APIFY_TOKEN`), run `pip install lingua-language-detector pillow`, then ask Claude, for example: "What reels go viral for yoga studios in the US this month? Budget $5, report in English."
