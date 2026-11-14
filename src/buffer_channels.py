"""Find your Buffer channel ids automatically (standard library only).

The workflow only needs BUFFER_API_KEY. It asks Buffer which channels are connected and
uses the YouTube one and the TikTok one. If you have several of one kind, or want to
pin one, set BUFFER_YOUTUBE_CHANNEL_ID / BUFFER_TIKTOK_CHANNEL_ID as secrets.
"""
import json
import os
import urllib.request

URL = "https://api.buffer.com"
SERVICES = ("youtube", "tiktok")


def _ask(query):
    req = urllib.request.Request(
        URL, data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"Bearer {os.environ['BUFFER_API_KEY']}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as reply:
        data = json.load(reply)
    if data.get("errors"):
        raise RuntimeError(f"Buffer error: {data['errors']}")
    return data["data"]


def all_channels(ask=_ask):
    """[{id, name, service}] for every connected channel in every organization."""
    found = []
    for org in ask("{ account { organizations { id name } } }")["account"]["organizations"]:
        found += ask('{ channels(input: {organizationId: "%s"}) { id name service } }' % org["id"])["channels"]
    return found


def channel_ids(env=os.environ, ask=_ask):
    """{"youtube": id, "tiktok": id} for the platforms we can post to. Secrets win over discovery."""
    ids = {s: env[f"BUFFER_{s.upper()}_CHANNEL_ID"] for s in SERVICES if env.get(f"BUFFER_{s.upper()}_CHANNEL_ID")}
    if not env.get("BUFFER_API_KEY") or len(ids) == len(SERVICES):
        return ids
    try:
        for ch in all_channels(ask):
            service = str(ch.get("service", "")).lower()
            if service in SERVICES and service not in ids:
                ids[service] = ch["id"]
    except Exception as err:  # without a lookup, only pinned channels are used
        print(f"::warning::Could not look up Buffer channels: {err}")
    return ids
