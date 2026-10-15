---
name: reels-trends
description: Research what goes viral on Instagram Reels in any niche, market, language and date range with Apify. Finds reels by multilingual keywords and hashtags, compares every reel with its author's usual views (the × multiplier), labels the leaders' formats from video frames and builds an HTML report with findings and ready-to-shoot ideas. Use when the user asks what works, flies, trends or goes viral on Instagram or Reels for a niche, industry, city, country or set of competitors, e.g. "что залетает в рилс у стоматологов", "тренды Reels для кофеен в Алматы за сентябрь", "what reels go viral for yoga studios in the US this month".
---

# Reels trends research

Finds what went viral on Instagram Reels for a niche in a chosen period and explains why, with a report the user can act on.

The core metric is **× to the author's median**: reel views divided by the median views of the author's recent videos (floor 1,000). It separates reels that flew because of the format from reels that are big only because the account is big.

Scripts live in `${CLAUDE_SKILL_DIR}/scripts/`, reference notes in `${CLAUDE_SKILL_DIR}/references/`. Every script takes the run folder (RUN below) as its first argument and prints what it did and what it cost.

## Before you start

1. **Apify token.** Check `echo ${APIFY_TOKEN:+set}` or the file `~/.config/reels-trends/apify_token`. If neither exists, ask the user to create a token at https://console.apify.com/settings/integrations and save it with `mkdir -p ~/.config/reels-trends && read -s T && echo "$T" > ~/.config/reels-trends/apify_token && chmod 600 ~/.config/reels-trends/apify_token`. On Windows: `setx APIFY_TOKEN "<token>"` and restart the terminal. Never print, log or commit the token.
2. **Python packages.** `python3 -c "import lingua, PIL"`; if it fails: `pip install lingua-language-detector pillow` (add `--user` or use a venv if pip refuses). `ffmpeg` is optional but strongly recommended: without it the agents label leaders from covers only. On Windows use `python` where this file says `python3`.
3. **Brief.** Ask only what you cannot infer, in one message, with defaults:
   - niche, in the user's words (and what to exclude, e.g. "dentistry, not dental students");
   - markets: countries or languages, or "the whole world";
   - period: default the last 30 days; a window that ends today is fine, the newest reels simply have fewer views;
   - budget in USD: default $5 on a free Apify plan, $10-15 on a paid one;
   - report language: default the language the user writes in (UI strings exist for `ru` and `en`).

## Workflow

### 1. Run folder and config
Create `reels-research/<short-slug>/` in the current project (or where the user wants; if the project is a git repo, add `reels-research/` to its `.gitignore`) and write `config.json`. Read `${CLAUDE_SKILL_DIR}/references/config.md` first: it explains every field and how to write good queries. The essentials:
- `segments`: one per language or market, with 8-30 native queries for big markets (real phrases people type, service names, slang) and 3-6 for small ones, plus `min_views` scaled to the market. English queries pull content from the whole world; write each market's queries in its own language.
- `relevance_regex`: word stems of the niche in every language you search (a reel must match it to be kept).
- `exclude_regex`: what must never count (adult services, spam, unrelated meanings of the niche word).
- `topics`: 8-12 subtopics with multilingual regexes, ordered from most specific to most generic, plus `fallback_topic`.
- `focus_topics`: topics you expect to compare across languages.
`${CLAUDE_SKILL_DIR}/references/examples/` has a full worldwide config (massage, 19 languages) and a small free-plan config.

### 2. Account check and cost
```
python3 ${CLAUDE_SKILL_DIR}/scripts/check.py RUN
python3 ${CLAUDE_SKILL_DIR}/scripts/search.py RUN --dry
```
`check.py` reads the plan and picks the engine: **memo23** on paid Apify plans (date and views filters on the server, misses are free) or **hashtag** on the free plan (memo23 serves free accounts only one query with a few results). Tell the user the plan, the engine, the worst-case cost and the budget in one or two lines. The scripts never start runs above the remaining `budget_usd`; raise it only with the user's consent.

### 3. Search and merge
```
python3 ${CLAUDE_SKILL_DIR}/scripts/search.py RUN          # 5-25 min, run it in the background
python3 ${CLAUDE_SKILL_DIR}/scripts/merge.py RUN
```
Read the merge summary before paying for anything else:
- many `not_in_niche`: the regex is too narrow or queries drift; many kept reels off-topic: the regex is too broad;
- a language with very few reels: add queries in that language and run `search.py RUN --only SEG --tag extra2`, then merge again (raw files add up);
- on the hashtag engine, `outside_dates` is often 70-90%: use a 30-60 day window, more and more specific hashtags, larger `search.hashtag_results`, or suggest a paid plan.

### 4. Authors, multiplier, leaders
```
python3 ${CLAUDE_SKILL_DIR}/scripts/profiles.py RUN --dry   # then without --dry
python3 ${CLAUDE_SKILL_DIR}/scripts/score.py RUN
python3 ${CLAUDE_SKILL_DIR}/scripts/leaders.py RUN
```
Profiles are fetched only for authors with a reel above `profiles.floor_by_lang`; tune floors or `--max` to fit the budget. Leaders = global top by × (with a views floor) + top by views + top by × inside each language. Aim for 100-250 leaders on a worldwide run, 30-80 on a single market.

### 5. Enrich the leaders (run the three in parallel)
```
python3 ${CLAUDE_SKILL_DIR}/scripts/transcripts.py RUN
python3 ${CLAUDE_SKILL_DIR}/scripts/about.py RUN        # country of each leader account, paid plans only
python3 ${CLAUDE_SKILL_DIR}/scripts/media.py RUN        # 4-frame strips + covers; CDN links expire in days, so do it soon after search
```

### 6. Label the leaders from frames
```
python3 ${CLAUDE_SKILL_DIR}/scripts/batches.py RUN --size 20
```
It writes `work/label_prompt.md` (the instructions, already filled with this niche's taxonomy) and one batch file per 20 leaders, and prints BATCH and OUT paths. Launch one sub-agent per batch, all in a single message so they run in parallel, with this prompt:

> Read the labelling instructions in RUN/work/label_prompt.md and follow them exactly. In those instructions, {BATCH} = <batch path> and {OUT} = <out path>.

If sub-agents are not available, label the batches yourself with the same instructions. Labels must come from looking at the frames: many reels in visual niches have no speech, and the caption often does not describe what is on screen. Check coverage with `python3 ${CLAUDE_SKILL_DIR}/scripts/labels.py RUN`.

### 7. Review before you count
Open the frames of the top 20 leaders by × and of every reel an agent flagged or marked irrelevant. Make the rules consistent across batches in `work/overrides.json` (format in `${CLAUDE_SKILL_DIR}/references/content.md`): for example, exercise-only reels are not massage; content farms that sell a model's body rather than the service go to `"flagged": {"<reel code>": "sexualised"}`; reposts of someone else's video get `"repost"`. Flagged reels stay in the data and in the report grid (hidden by default) but not in the format table or the ideas.

### 8. Numbers and the story
```
python3 ${CLAUDE_SKILL_DIR}/scripts/stats.py RUN
```
Read the summary and find 6-7 findings that a business owner can act on. Check every claim against the data before writing it:
- a claim that something is missing in a language needs proof that you searched that language with the right words (add queries and re-run if not);
- formats with fewer than 5 leaders get a "few reels" caveat;
- compute any extra number with a short Python snippet over `work/scored.json` and `work/cls/`, never from memory.
Then write `RUN/content.json` following `${CLAUDE_SKILL_DIR}/references/content.md`: findings, notes for formats, topics and languages, 8-10 ideas (title, a hook the user can say on camera, why it works with numbers, 2-3 example reel codes) and 12-16 hooks for the "first seconds" section.

### 9. Report
```
python3 ${CLAUDE_SKILL_DIR}/scripts/build.py RUN
```
Gives `report/index.html` (open in a browser), `report/artifact.html` (body-only version for publishing as a Claude artifact, if the environment has an Artifact tool) and `report/reels.json` (all reels with scores and labels). Tell the user where the report is, what the run cost in total (`work/spend.jsonl`), and the 3-5 most useful findings in plain words.

## Reading the numbers honestly
- The search returns notable reels, not all reels, so medians are higher than a typical account's. Compare groups with each other, not with the user's own numbers.
- × is relative to the author: small accounts produce the biggest multipliers. That is the point (reach does not need followers), but say so.
- The format table describes the leaders, not the whole niche. Topic, duration and follower tables use all reels.
- Reels from the last days of the window are still collecting views.
- Language is not country. Use `about.py` for countries.

More lessons from real runs are in `${CLAUDE_SKILL_DIR}/references/gotchas.md`. Read it before a worldwide or multi-language run.
