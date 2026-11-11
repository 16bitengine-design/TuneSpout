# Lesson format

One JSON file per video, saved under `lessons/<topic>/`.

```json
{
  "title": "Count the Ducks! | Counting 1 to 5 Song for Kids",
  "description": "Short, friendly description for parents.",
  "tags": ["counting", "kids song"],
  "voice": "af_heart",
  "speed": 0.9,
  "pitch": 1.2,
  "scenes": [
    {"animal": "duck", "count": 1, "line": "One little duck is swimming in the pond. Quack!"}
  ]
}
```

Rules (enforced by `src/safety.py`):
- At most 25 words per line. Short, simple sentences.
- No violent, scary or unkind words.
- `animal` must exist in `src/render.py` (`duck`, `chick`, `fish`).
