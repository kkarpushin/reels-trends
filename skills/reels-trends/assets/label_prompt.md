You are labelling Instagram Reels for a research report: "what flies on Instagram Reels in the niche: {NICHE}", reels posted {DATE_FROM} to {DATE_TO}. The reader wants formats to copy for their own business.

Input: `{BATCH}`, a JSON list of reels. For each reel you get author info, plays, `x_vs_author_median` (how many times the reel beat the author's usual views), caption, speech transcript (may be empty) and `frames`: a JPEG strip with 4 frames of the video (0.6 s, 30%, 55%, 85%), or `cover` if frames are missing.

For EVERY reel: open the frames image (or cover) with the Read tool and look at it, then read caption and transcript. The first frame usually shows the hook (on-screen text). Then write one JSON object per reel.

Write the result as a JSON array to `{OUT}` with the Write tool (valid JSON, UTF-8, no comments, same order as the input). Fields:

- `code`: copy from input.
- `relevant`: false only if the reel is not about the niche at all (the niche word is just a hashtag, an unrelated meme, news, a recipe) or if it advertises sexual services. Humour, products, DIY and behind-the-scenes content about the niche are relevant.
- `flag`: null, or a short English reason when the reel is relevant but should not be copied as a format: "sexualised" (the main draw is a model's body or face as an object of attraction, or the account funnels to "exclusive content"), "repost" (clearly someone else's video re-uploaded), "scam" (fake news, miracle cures). Leave null in normal cases.
- `format`: exactly one value from this list (the dominant one):
{FORMATS}
- `topic`: exactly one from: {TOPICS}
- `creator`: one of: {CREATORS}
- `speech`: one of: {SPEECH}
- `hook_orig`: the hook of the first seconds in the original language: on-screen text from frame 1 if any, else the first spoken sentence, else the first line of the caption. Max 160 characters. Copy it exactly. If there is no text at all, write an empty string.
- `hook_tr`: natural {LANG} translation of `hook_orig` (copy if already {LANG}). Max 160 characters.
- `what`: one {LANG} sentence, max 20 words: what the viewer actually sees and hears.
- `why`: one {LANG} phrase, max 15 words: the most likely reason it beat the author's usual views, tied to what you saw.
- `country`: the country if clearly evident (location tag, city in caption or bio, currency, phone code), else null. English name.

Write plainly and concretely. Do not research anything on the web. Do not modify any other files. After writing the file, reply with one line: how many reels you wrote, how many are `relevant: false` and how many have a `flag`.
