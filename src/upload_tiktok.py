"""Post out/video_vertical.mp4 to TikTok with the Content Posting API.

Needs secrets TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_REFRESH_TOKEN,
and STATE_KEY (any long random text) so a rotated refresh token can be saved.
Writes out/result_tiktok.json for the daily record.

IMPORTANT: until TikTok audits your app, every post is forced to private
(SELF_ONLY). Set TIKTOK_PRIVACY=PUBLIC_TO_EVERYONE only after the audit passes.
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

import secrets_store

API = "https://open.tiktokapis.com"


def get_access_token():
    """Refresh the access token. TikTok may return a NEW refresh token and says to
    use it from then on, so a rotated one is saved (encrypted) in the state branch."""
    secret_rt = os.environ["TIKTOK_REFRESH_TOKEN"]
    key = os.environ.get("STATE_KEY", "")
    token_file = Path(os.environ.get("STATE_DIR", "state")) / "tiktok_token.enc"
    saved = secrets_store.load_token(token_file, key, secret_rt) if key else None
    refresh_token = saved or secret_rt

    r = requests.post(f"{API}/v2/oauth/token/", data={
        "client_key": os.environ["TIKTOK_CLIENT_KEY"],
        "client_secret": os.environ["TIKTOK_CLIENT_SECRET"],
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "access_token" not in data:
        raise SystemExit(f"TikTok token refresh failed: {data.get('error_description') or data.get('error')}")
    new = data.get("refresh_token")
    if new and new != refresh_token:  # never print tokens: logs are visible
        if key:
            secrets_store.save_token(token_file, key, new, secret_rt)
            print("TikTok issued a new refresh token; saved it encrypted for tomorrow.")
        else:
            print("::warning::TikTok issued a new refresh token but STATE_KEY is not set, so it "
                  "cannot be saved. The TIKTOK_REFRESH_TOKEN secret may stop working. "
                  "Add a STATE_KEY secret (any long random text) and run again.")
    return data["access_token"]


def post(path, token, body):
    r = requests.post(f"{API}{path}", json=body, timeout=60, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8"})
    data = r.json()
    if data.get("error", {}).get("code") not in (None, "ok"):
        raise SystemExit(f"TikTok error on {path}: {data['error']}")
    return data["data"]


def main(out_dir="out"):
    out = Path(out_dir)
    meta = json.loads((out / "tiktok.json").read_text())
    video = out / "video_vertical.mp4"
    size = video.stat().st_size
    token = get_access_token()

    info = post("/v2/post/publish/creator_info/query/", token, {})
    wanted = os.environ.get("TIKTOK_PRIVACY", "SELF_ONLY")
    privacy = wanted if wanted in info["privacy_level_options"] else "SELF_ONLY"
    if privacy != wanted:
        print(f"{wanted} is not allowed for this account; using {privacy}.")

    # our videos are small: one chunk (TikTok allows single chunks up to 64 MB)
    if size > 64_000_000:
        raise SystemExit("Video is over 64 MB; add chunked upload before posting this.")
    init = post("/v2/post/publish/video/init/", token, {
        "post_info": {
            "title": meta["caption"],
            "privacy_level": privacy,
            "disable_comment": os.environ.get("TIKTOK_COMMENTS", "off") != "on",
            "disable_duet": True,
            "disable_stitch": True,
            "brand_content_toggle": False,
            "brand_organic_toggle": False,
            "is_aigc": bool(meta.get("is_aigc", True)),
        },
        "source_info": {"source": "FILE_UPLOAD", "video_size": size,
                        "chunk_size": size, "total_chunk_count": 1},
    })

    with open(video, "rb") as f:
        r = requests.put(init["upload_url"], data=f.read(), timeout=300, headers={
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{size - 1}/{size}"})
    if r.status_code not in (200, 201, 206):
        raise SystemExit(f"TikTok upload failed: HTTP {r.status_code} {r.text[:200]}")

    result = {"publish_id": init["publish_id"], "privacy": privacy}
    for _ in range(40):  # wait up to about 6 minutes
        st = post("/v2/post/publish/status/fetch/", token, {"publish_id": init["publish_id"]})
        print("TikTok status:", st["status"])
        if st["status"] == "PUBLISH_COMPLETE":
            print(f"Posted to TikTok as {privacy}.")
            (out / "result_tiktok.json").write_text(json.dumps(dict(result, status="posted")))
            return
        if st["status"] == "FAILED":
            raise SystemExit(f"TikTok failed: {st.get('fail_reason')}")
        time.sleep(10)
    # Uploaded but TikTok is slow. Record it anyway: retrying could post the same video twice.
    print("::warning::TikTok is still processing this video. Check the TikTok app.")
    (out / "result_tiktok.json").write_text(json.dumps(dict(result, status="processing")))


if __name__ == "__main__":
    main(*sys.argv[1:])
