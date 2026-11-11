"""One-time helper: get the TikTok refresh token for the GitHub secrets.

NOT YET TESTED against TikTok: check it against the current TikTok docs.

1. Create an app at developers.tiktok.com, add the Content Posting API product
   with the video.publish scope, and register an https redirect URI.
2. python tools/get_tiktok_token.py
3. Open the printed link, approve, then paste the full address you land on
   (it contains ?code=...). The page itself may show an error; that is fine.
Copy the printed values into GitHub secrets TIKTOK_CLIENT_KEY,
TIKTOK_CLIENT_SECRET, TIKTOK_REFRESH_TOKEN. Run on your own computer only.
"""
import urllib.parse

import requests

key = input("Client key: ").strip()
secret = input("Client secret: ").strip()
redirect = input("Registered redirect URI: ").strip()

query = urllib.parse.urlencode({
    "client_key": key, "scope": "user.info.basic,video.publish",
    "response_type": "code", "redirect_uri": redirect, "state": "kidschannel"})
print("\nOpen this link:\nhttps://www.tiktok.com/v2/auth/authorize/?" + query)

landed = input("\nPaste the full address you were sent to: ").strip()
code = urllib.parse.parse_qs(urllib.parse.urlparse(landed).query)["code"][0]

r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data={
    "client_key": key, "client_secret": secret, "code": code,
    "grant_type": "authorization_code", "redirect_uri": redirect}, timeout=60)
data = r.json()
if "refresh_token" not in data:
    raise SystemExit(f"Failed: {data}")
print("\nTIKTOK_CLIENT_KEY     =", key)
print("TIKTOK_CLIENT_SECRET  =", secret)
print("TIKTOK_REFRESH_TOKEN  =", data["refresh_token"])
