"""Post out/video_vertical.mp4 to TikTok with the Content Posting API.

Needs secrets TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_REFRESH_TOKEN.

IMPORTANT: until TikTok audits your app, every post is forced to private
(SELF_ONLY). Set TIKTOK_PRIVACY=PUBLIC_TO_EVERYONE only after the audit passes.
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

API = "https://open.tiktokapis.com"


def get_access_token():
    r = requests.post(f"{API}/v2/oauth/token/", data={
        "client_key": os.environ["TIKTOK_CLIENT_KEY"],
        "client_secret": os.environ["TIKTOK_CLIENT_SECRET"],
        "grant_type": "refresh_token",
        "refresh_token": os.environ["TIKTOK_REFRESH_TOKEN"],
    }, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "access_token" not in data:
        raise SystemExit(f"TikTok token refresh failed: {data.get('error_description') or data.get('error')}")
    if data.get("refresh_token") and data["refresh_token"] != os.environ["TIKTOK_REFRESH_TOKEN"]:
        # Never print the token (logs are visible). Re-run tools/get_tiktok_token.py if posting stops working.
        print("Note: TikTok issued a new refresh token. The saved one may stop working before it expires.")
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

    for _ in range(40):  # wait up to about 6 minutes
        st = post("/v2/post/publish/status/fetch/", token, {"publish_id": init["publish_id"]})
        print("TikTok status:", st["status"])
        if st["status"] == "PUBLISH_COMPLETE":
            print(f"Posted to TikTok as {privacy}.")
            return
        if st["status"] == "FAILED":
            raise SystemExit(f"TikTok failed: {st.get('fail_reason')}")
        time.sleep(10)
    raise SystemExit("TikTok is still processing; check the TikTok app.")


if __name__ == "__main__":
    main(*sys.argv[1:])
