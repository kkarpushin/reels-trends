# config.json

One file per research run, in the run folder. Only `niche`, `segments` and `relevance_regex` are really needed; everything else has defaults (see `DEFAULTS` in `scripts/common.py`).

```json
{
  "niche": "coffee shops in Kazakhstan",
  "report_language": "ru",
  "date_from": "2026-09-15",
  "date_to": "2026-10-15",
  "budget_usd": 8,
  "engine": "auto",
  "segments": {
    "RU": {"min_views": 3000, "queries": [["кофейня", 120], ["кофейня алматы", 60], ["латте арт", 60], ["бариста", 60]]},
    "KK": {"min_views": 1000, "queries": [["кофеханасы", 60], ["кофе алматы", 60]]},
    "EN": {"min_views": 10000, "queries": [["coffee shop almaty", 60]]}
  },
  "relevance_regex": "coffee|кофе|кофейн|латте|latte|espresso|эспрессо|бариста|barista|капучино|cappuccino|кофехана",
  "exclude_regex": "coffee table|журнальный столик",
  "topics": [
    ["Латте-арт", "latte ?art|латте ?арт"],
    ["Бариста за работой", "barista|бариста"],
    ["Интерьер и атмосфера", "interior|интерьер|уютн|cozy|atmosphere|атмосфер"]
  ],
  "fallback_topic": "Общее про кофейни",
  "focus_topics": ["Латте-арт"],
  "profiles": {"floor_by_lang": {"RU": 5000, "KK": 2000, "default": 10000}, "max_authors": 800},
  "leaders": {"top_x": 60, "x_min_plays": 10000, "top_plays": 20, "per_author": 3,
              "lang_quota": {"RU": 12}, "lang_quota_default": 6, "lang_min_plays": {"KK": 2000}, "lang_min_plays_default": 3000}
}
```

## Fields

| field | what it does | default |
|---|---|---|
| `niche` | shown to the labelling agents and in the report | |
| `report_language` | `ru` or `en`: UI strings, taxonomy names, language of labels | `ru` |
| `date_from`, `date_to` | inclusive publication window, `YYYY-MM-DD` | last 30 days |
| `budget_usd` | hard cap for Apify spend of this run; scripts refuse to go over it | 10 |
| `engine` | `auto` (memo23 on paid plans, hashtag on free), `memo23`, `hashtag` | `auto` |
| `segments` | language or market groups, see below | |
| `relevance_regex` | case-insensitive; a reel is kept only if caption, hashtags, username, name, location or alt text match | keep all |
| `exclude_regex` | case-insensitive; matching reels are dropped | adult spam |
| `topics` | `[name, regex]` pairs, first match wins, checked on caption + hashtags + username + name | none |
| `fallback_topic` | topic for reels that match nothing | `Общее` / `General` |
| `focus_topics` | topics broken down by language in stats | none |
| `profiles.floor_by_lang` | an author gets a profile (and an ×) only if one of their reels has at least this many views; keys are segment codes plus `default` | 10000 |
| `profiles.max_authors` | cap on profiles fetched (biggest reels first) | 1500 |
| `leaders.top_x` | how many reels with the highest × enter the leaders | 100 |
| `leaders.x_min_plays` | views floor for that global × ranking (kills tiny flukes) | 20000 |
| `leaders.top_plays` | plus this many most-viewed reels | 30 |
| `leaders.lang_quota`, `lang_quota_default` | plus the best × inside every language with at least `lang_min_reels` reels | 7 |
| `leaders.lang_min_plays`, `lang_min_plays_default` | views floor for the per-language ranking | 5000 |
| `leaders.per_author` | max leaders from one account | 3 |
| `x_floor` | author median below this is raised to it | 1000 |
| `transcripts`, `frames`, `country_for_leaders` | switch enrichment steps off | true |
| `labels` | replace the default taxonomy: `{"formats": [[name, hint], ...], "creators": [...], "speech": [...]}` | see `scripts/taxonomy.py` |
| `search.*` | `coverage` (`comprehensive` walks hashtag feeds too), `queries_per_run`, `default_max_per_query`, `deadline_sec`, `hashtag_results`, `keyword_results` | see defaults |

## Segments

A segment is a language or a market with its own queries and views floor. The code (`RU`, `EN`, `ES`, `ID`...) is also used as the language when a caption has no text, so use language codes. No underscores in segment codes.

```json
"ES": {"min_views": 5000, "queries": [["masaje", 120], ["masaje relajante", 60]], "hashtags": ["masaje", "masajes"]}
```

- `queries`: `[phrase, max results]` or just a phrase (then `search.default_max_per_query` is used). memo23 searches captions, alt text, usernames, locations and audio titles for whole words, and in `comprehensive` mode also walks the matching hashtag feeds.
- `hashtags`: used only by the hashtag engine; if absent it uses the queries without spaces.
- `min_views`: memo23 drops reels below it before billing. Scale it to the market: about 10000 for English, 3000-5000 for Spanish, Portuguese, Russian, Turkish, 1000-2000 for smaller languages and for small local markets.

## Writing good queries

- Write each market's queries in its own language and script. English words return reels from the whole world; a Russian-speaking market needs Cyrillic queries, Japan needs Japanese, and so on.
- Mix the head term (`massage`), service names (`lymphatic drainage`, `head spa`), problems (`back pain massage`), places (`massage dubai`), and the profession (`massage therapist`). Give head terms 100-120 results, the rest 40-60.
- Add trending service names you expect, even in languages where you think they are rare. If a finding will say "nobody does X in language Y", you must have searched X in language Y's own words.
- 8-30 queries for each big market, 3-6 for small ones. A worldwide run of 19 languages used 144 queries.
- City names narrow a local study (`кофейня алматы`), but people rarely put the city in the caption; use the location tag and the bio instead (they are in the data).

## relevance_regex and topics

- Use word stems, not whole words: `массаж|масаж|massag|masaj|masaż` catches every form. Add the niche word in every script you searched.
- Test the regex on the merge output: look at a sample of dropped and kept captions. A merge that keeps 98% of what the search returned is normal for memo23 (it already matched the query).
- Topics: 8-12, from specific to generic, because the first match wins. Typical order: special audiences and products first, then subtopics, then broad goals (pain, relaxation), then the fallback.
- Body-area words alone (`back`, `neck`) say little about the topic; prefer problem and goal words.

## Budget guide (Apify prices of October 2026, paid tier)

| step | price | typical worldwide run | typical single market |
|---|---|---|---|
| memo23 search | about $0.0011-0.0015 per reel found | 6000 reels, $6.5 | 1000 reels, $1.2 |
| hashtag search (free plan) | $0.0026 per result, old posts included | | 600 results, $1.6 |
| profiles | $0.002-0.0026 each | 2200, $4.4 | 400, $0.9 |
| country of leaders | +$0.005 each (paid plans) | 200, $1.4 | 60, $0.4 |
| transcripts | about $0.004-0.0055 each | 220, $0.9 | 60, $0.3 |

Free Apify plans include $5 of usage per month. `check.py` prints what is left.
