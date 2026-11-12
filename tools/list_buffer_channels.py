"""One-time helper: find your Buffer channel IDs (for the GitHub secrets).

  BUFFER_API_KEY=... python tools/list_buffer_channels.py

Prints each connected channel's service, name and id. Use the YouTube one as
BUFFER_YOUTUBE_CHANNEL_ID and the TikTok one as BUFFER_TIKTOK_CHANNEL_ID.
"""
import os

import requests


def ask(query):
    r = requests.post("https://api.buffer.com", json={"query": query}, timeout=60,
                      headers={"Authorization": f"Bearer {os.environ['BUFFER_API_KEY']}"})
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise SystemExit(data["errors"])
    return data["data"]


for org in ask("{ account { organizations { id name } } }")["account"]["organizations"]:
    for ch in ask('{ channels(input: {organizationId: "%s"}) { id name service } }' % org["id"])["channels"]:
        print(f'{ch["service"]:10} {ch["name"]:30} {ch["id"]}')
