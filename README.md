# Kids Learning Cartoons: automated YouTube channel

Makes short, gentle learning videos for kids under 12 from simple lesson files.
Runs free on GitHub Actions. No paid tools.

**Pipeline:** `lessons/**/*.json` -> Kokoro voice (pitched up to sound younger) -> code-made backing tune -> flat vector cartoon frames -> ffmpeg -> YouTube (marked "made for kids").

## Try it on your computer
```bash
sudo apt install ffmpeg espeak-ng      # macOS: brew install ffmpeg espeak-ng
pip install -r requirements.txt
python src/make_video.py lessons/numbers/counting_ducks.json
# no Kokoro yet? test with silent audio:
python src/make_video.py lessons/numbers/counting_ducks.json --fake-tts
```
Result: `out/video.mp4`.

## Put it on GitHub and automate it
1. Create a new GitHub repo and push this folder.
2. Create the YouTube channel. In Google Cloud Console, enable **YouTube Data API v3**, create an OAuth client (Desktop app), and get a **refresh token** for your channel (one-time sign-in script, e.g. Google's `youtube-api-samples` OAuth quickstart).
3. Repo Settings -> Secrets -> Actions: add `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.
4. The workflow `.github/workflows/daily.yml` runs daily and uploads as **private**. Watch each video, then switch `PRIVACY` to `public` once you trust it.

## Add a lesson
Copy `lessons/numbers/counting_ducks.json`, change the text, `count` and `animal` (`duck`, `chick`, `fish`). The safety filter in `src/safety.py` rejects violent or unkind words and long sentences. New animals or topics (adding, plurals, animal sounds) only need a new draw function in `src/render.py`.

## Important notes
- **Kid voice:** Kokoro has no child voices. We pitch up a bright voice. Never clone a real child's voice without written parental consent.
- **Singing:** Kokoro speaks; it does not sing. Lessons are rhythmic chants over a generated tune. For true singing, add a licensed singing tool later.
- **Made for kids:** every upload sets `selfDeclaredMadeForKids`. This turns off comments and personalized ads, which is expected for kids channels (COPPA).
- **YouTube API:** new API projects often upload as locked-private until Google audits them. Request the audit early (YouTube API compliance form), or upload by hand until approved.
- **Style:** this is simple 2D vector style. Disney-quality 3D cannot be made by free code; it needs paid AI video tools.
