"""Post today's video to YouTube and TikTok through Buffer.

  python src/buffer_post.py youtube out
  python src/buffer_post.py tiktok out

Buffer only takes videos from a public web link, so the file is first put on
Cloudinary (free tier). Writes out/result_<platform>.json for the daily record.

Secrets: BUFFER_API_KEY, BUFFER_YOUTUBE_CHANNEL_ID, BUFFER_TIKTOK_CHANNEL_ID,
CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET.
Settings (repo Variables): YT_PRIVACY (private|unlisted|public, default private),
TIKTOK_MODE (draft|post, default draft).
"""
import datetime
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import requests

BUFFER = "https://api.buffer.com"
FILES = {"youtube": "video.mp4", "tiktok": "video_vertical.mp4"}
MUTATION = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess { post { id } }
    ... on MutationError { message }
  }
}"""
KEEP_DAYS = 7


def cloudinary_upload(path, public_id):
    """Signed upload; returns a permanent https link."""
    cloud = os.environ["CLOUDINARY_CLOUD_NAME"]
    secret = os.environ["CLOUDINARY_API_SECRET"]
    params = {"public_id": public_id, "timestamp": str(int(time.time())), "overwrite": "true"}
    to_sign = "&".join(f"{k}={params[k]}" for k in sorted(params))
    signature = hashlib.sha1((to_sign + secret).encode()).hexdigest()
    with open(path, "rb") as f:
        r = requests.post(f"https://api.cloudinary.com/v1_1/{cloud}/video/upload",
                          data={**params, "api_key": os.environ["CLOUDINARY_API_KEY"], "signature": signature},
                          files={"file": f}, timeout=600)
    r.raise_for_status()
    return r.json()["secure_url"]


def cloudinary_prune():
    """Delete our videos older than KEEP_DAYS so the free storage never fills up."""
    cloud = os.environ["CLOUDINARY_CLOUD_NAME"]
    auth = (os.environ["CLOUDINARY_API_KEY"], os.environ["CLOUDINARY_API_SECRET"])
    base = f"https://api.cloudinary.com/v1_1/{cloud}/resources/video/upload"
    try:
        r = requests.get(base, params={"prefix": "tunespout/", "max_results": 500}, auth=auth, timeout=60)
        r.raise_for_status()
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=KEEP_DAYS)
        old = [x["public_id"] for x in r.json().get("resources", [])
               if datetime.datetime.fromisoformat(x["created_at"].replace("Z", "+00:00")) < cutoff]
        if old:
            requests.delete(base, params={"public_ids[]": old}, auth=auth, timeout=60).raise_for_status()
            print(f"Removed {len(old)} old video(s) from Cloudinary.")
    except Exception as err:  # housekeeping must never block posting
        print("Could not tidy Cloudinary:", err)


def build_input(platform, meta, url, env=os.environ):
    """The Buffer createPost input for one platform."""
    body = {
        "channelId": env[f"BUFFER_{platform.upper()}_CHANNEL_ID"],
        "schedulingType": "automatic",
        "mode": "shareNow",
        "aiAssisted": True,
        "assets": [{"video": {"url": url}}],
    }
    if platform == "youtube":
        body["text"] = meta.get("description", "")
        body["metadata"] = {"youtube": {
            "title": meta["title"][:100],
            "categoryId": "27",  # Education
            "madeForKids": True,  # required for kids content (COPPA)
            "privacy": env.get("PRIVACY") or "private",
            "isAiGenerated": True,
            "notifySubscribers": False,
        }}
    else:
        body["text"] = meta["caption"]
        body["metadata"] = {"tiktok": {"isAiGenerated": meta.get("is_aigc", True)}}
        if (env.get("TIKTOK_MODE") or "draft") != "post":
            body["saveToDraft"] = True  # review in Buffer, then publish by hand
    return body


def create_post(body):
    r = requests.post(BUFFER, json={"query": MUTATION, "variables": {"input": body}}, timeout=120,
                      headers={"Authorization": f"Bearer {os.environ['BUFFER_API_KEY']}"})
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise SystemExit(f"Buffer error: {data['errors']}")
    result = data["data"]["createPost"]
    if "post" not in result:
        raise SystemExit(f"Buffer refused the post: {result.get('message')}")
    return result["post"]["id"]


def main(platform, out_dir="out"):
    out = Path(out_dir)
    meta = json.loads((out / ("meta.json" if platform == "youtube" else "tiktok.json")).read_text())
    day = os.environ.get("DAY") or datetime.date.today().isoformat()
    url = cloudinary_upload(out / FILES[platform], f"tunespout/{day}-{platform}")
    post_id = create_post(build_input(platform, meta, url))
    saved_as = "draft" if build_input(platform, meta, url).get("saveToDraft") else "posted"
    print(f"Sent to Buffer ({platform}, {saved_as}).")
    (out / f"result_{platform}.json").write_text(json.dumps({"id": post_id, "status": saved_as}))
    cloudinary_prune()


if __name__ == "__main__":
    main(*sys.argv[1:])
