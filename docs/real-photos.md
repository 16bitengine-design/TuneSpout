# Real photos rule

Anything that exists in the real world and is named in a lesson (duck, ducklings, frog, dog, cat,
kitten, table, tree, fruit, money, house ...) is shown as a **real photograph**, never a drawing.
Cartoon characters (Amina, Jomo, Mei, Kofi, Yumbi, Lumbo) stay animated and react to the photo.

## How it works
1. `Lexicon.find_terms(script)` finds real-world words (plurals and baby animals included).
2. `get_photo(term)` uses the local cache, then your Cloudinary library, then downloads a new photo (Openverse -> Wikimedia Commons).
   Candidates are rejected if tags look unsafe, if the photo is small (<800px) or blurry.
3. `make_card()` builds a 9:16 card. The **whole** photo is shown, never cropped, with the word under it.
4. `plan_cues()` shows each photo the moment its word is sung (karaoke timestamps).
5. `apply_cue()` cuts from the cartoon frame to the photo card (with a short fade).

## Scripts
- Write words normally: `The duck and her ducklings met a frog.`
- Words that also mean something else are only matched when tagged: `[[orange]]` (fruit), `[[bear]]`.
  Run `strip_tags()` before TTS and subtitles.
- Add new things in `config/real_world_terms.json`. Banned words (e.g. pig) are refused at load time.

## GitHub setup (no new keys)
- Photos come from **Openverse** and **Wikimedia Commons**: no key, CC0 / public domain only.
  `PIXABAY_API_KEY` and `PEXELS_API_KEY` are optional extras; leave them out.
- Found photos are saved in your Cloudinary account (folder `tunespout-photos/`) using the
  `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY` and `CLOUDINARY_API_SECRET` secrets that
  `buffer_post.py` already uses. Each word is downloaded once, then reused by every later run.
  Add those three to the video-building step's `env:` if they are not there yet.
- To pre-load words (and get a review sheet), run:
  `python src/real_photos.py fetch duck duckling frog dog cat --sheet out/photo_review.png`

## Integration in the video builder (src/make_video.py frame loop)
```python
from real_photos import Lexicon, plan_cues, prepare_cues, active_cue, apply_cue, credits_text
lex = Lexicon.load()
cues = plan_cues(word_timestamps, lex)        # word times from the voice alignment
cues, records = prepare_cues(cues, lex)       # fetch photos + render cards
...
frame = apply_cue(render.draw_scene(sc, t), active_cue(cues, t), t)   # t = seconds in the episode
...
description += "\n\n" + credits_text(records)                         # credits: description only
```

## Copyright policy (strict)
- **Credits go in the video description only.** `credits_text(records)` builds them; nothing is
  ever drawn on the video or the cards.
- **Accepted licences:** CC0 / public domain (Openverse, Wikimedia). Pixabay / Pexels licences only if you add those optional keys.
  CC BY is **off by default** (set `ALLOW_CC_BY=1` to allow it, credited in the description).
  ShareAlike, NonCommercial, NoDerivatives and "all rights reserved" are never accepted.
- **Rights a licence does not cover are filtered by tags:** photos tagged with people (model
  releases), logos, brands, toys, artwork, statues, posters, mascots or stock-agency names are skipped.
- Every cached photo keeps a record (source, author, page link, licence, date fetched) in
  `cache/photos/<word>.json`, so you can prove where each image came from.
- Tags are not perfect: always glance at the review sheet for new words, and remove any photo that
  shows a person, a logo, a brand or someone's artwork. If in doubt, delete it and refresh.
- This is practical risk reduction, not legal advice.

## Review and licensing notes
- Photos are cached by word, so each is fetched once. Open `output/photo_review.png` (contact sheet)
  after adding new words and delete any cache entry you dislike, then re-run the fetch command.
- Automatic checks cannot see watermarks, logos or people. Review new words once.
- Money: coins are safe; some countries restrict reproducing banknotes. Check your own currency's rules.
- Wikimedia CC-BY photos need credit; `credits_text()` produces it for the description.
