"""Upload out/video.mp4 to YouTube, marked "made for kids".

Needs three GitHub secrets: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
(see README, step 4). Defaults to PRIVATE so you can review before publishing.
"""
import json
import os
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def main(out_dir="out"):
    out = Path(out_dir)
    meta = json.loads((out / "meta.json").read_text())
    creds = Credentials(
        None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    yt = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title": meta["title"][:100],
            "description": meta.get("description", "")
            + "\n\nMade with code. Safe, gentle learning for kids.",
            "tags": meta.get("tags", []),
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": os.environ.get("PRIVACY", "private"),
            "selfDeclaredMadeForKids": True,  # required for kids content (COPPA)
        },
    }
    media = MediaFileUpload(str(out / "video.mp4"), chunksize=-1, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    print("Uploaded:", f"https://youtu.be/{resp['id']}")


if __name__ == "__main__":
    main(*sys.argv[1:])
