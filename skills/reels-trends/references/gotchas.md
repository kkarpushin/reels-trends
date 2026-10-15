# Lessons from real runs

Collected on a dental study (Russian and Ukrainian, September 2026, $4) and a worldwide massage study (19 languages, 5 300 reels, October 2026, $13).

## Apify and the actors
- **memo23 on a free plan** logs "This user is not paying, restricted to 1 query and a few results" and runs only the first query. `check.py` detects the plan and switches to the hashtag engine. For serious research a paid plan is worth it: memo23 filters dates and views on the server and does not bill misses.
- **memo23 `comprehensive` coverage** also walks hashtag feeds; in the massage run it added most of the results at no extra cost per miss. 72 runs of 2 queries finished in 25 minutes in parallel.
- **The hashtag engine** returns a hashtag's "top" posts over years. In a two-week window only 4 of 34 results were fresh for Russian coffee hashtags; for popular English hashtags most were fresh. Use a 30-60 day window, more specific and trending hashtags and `hashtag_results` of 100+, and look at `outside_dates` in the merge output.
- **Keyword mode of the hashtag scraper** returns a mix of years; it helps coverage but not freshness.
- **The `about` section** (country of the account) costs $0.005 extra per profile and works on paid plans only. Fetch it for leader authors only.
- **Transcripts on a free plan** are limited to 5 links per run; `transcripts.py` splits automatically.
- **Video and cover links expire** within days. Run `media.py` soon after the search.
- **Prices change.** The scripts read live prices from the actors for the dry run; the ledger in `work/spend.jsonl` has the real spend.

## Search design
- English queries pull reels from everywhere (India, the Gulf, the Philippines, Latin America). For a specific market, query in its language; for a worldwide study, query in each language you want covered.
- **Absence claims need matching queries.** In the massage run, the Russian list had "массаж головы" but not "хэд спа". Before writing "head spa is nearly absent in Russian" we ran 9 Cyrillic head-spa queries; they found 28 reels, so the gap was real. Always do this check before a gap finding.
- Hashtags are spammed: lawyers, rodeo champions and football memes tag #massage. `relevance_regex` catches some of it; the labelling agents catch the rest (`relevant: false`).
- Many captions are hashtags only. Language detection then falls back to the query language; English-only queries leave such reels as `xx`.

## The × metric
- × = views / max(author median of recent videos, 1000). The floor stops tiny accounts from getting absurd values, but leaders with ×1000+ are still common: a reel that broke out of a 1 000-view account.
- Small accounts have the highest median × (accounts under 1 000 followers: ×18-28 in both studies; over 100 000: ×3-6). Say that reach does not need followers, and do not compare × across follower buckets as if it were quality.
- Profiles are fetched only above a views floor, so × exists for about two thirds of reels. Medians by topic or language are over the reels that have it.

## Labelling
- **Look at the frames.** In the massage run the reel with 21.9 M views had no massage hands on screen at all: a close-up of a woman's face, with "biomechanics" only in the caption. Captions and transcripts alone would have mislabelled it.
- Agents in different batches make different calls on borderline cases (exercise clips, testimonials, AI anatomy). Fix them in `overrides.json` with one rule each.
- **Content farms.** In English massage, the highest multipliers belonged to accounts based in Serbia and Russia posting 9-15 second clips of attractive models, pseudo-scientific captions ("BIOMECHANICS:") and links to "exclusive content". They are real competitors for attention, but not a format to recommend. Flag them, report them in one finding, keep them out of ideas.
- **Reposts.** Spectacle clips (50 cupping cups at once, 19.6 M) were re-uploaded by accounts in other countries; one account named after a Vietnamese clinic is based in Pakistan according to Instagram. `about.py` makes this visible.
- Hooks without on-screen text become the first spoken sentence, which can be weak ("Okay, I got it"). Pick quotes for the hooks section by hand.

## Pipeline mechanics
- Re-running `profiles.py` adds new authors and keeps countries already found. Re-running `leaders.py` is safe: transcripts, frames and labels are stored by reel code in separate files.
- `search.py --only SEG --tag extra2` adds a supplement without touching earlier raw files; run `merge.py` and the later steps again after it.
- Run with plain `python3` (or `python3 -P`); every script adds its own folder to the import path.
