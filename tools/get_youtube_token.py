"""One-time helper: get the YouTube refresh token for the GitHub secrets.

1. In Google Cloud Console enable YouTube Data API v3 and create an OAuth
   client of type "Desktop app". Download it as client_secret.json.
2. pip install google-auth-oauthlib
3. python tools/get_youtube_token.py client_secret.json
Sign in with the channel's Google account. Copy the three values it prints
into GitHub secrets YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
IMPORTANT: in Google Cloud > OAuth consent screen, set the publishing status to
"In production". While it says "Testing", Google expires the token after 7 days
and the daily posting silently stops. Check the token still works after 8 days.
Run this on your own computer only; never commit client_secret.json.
"""
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    sys.argv[1], ["https://www.googleapis.com/auth/youtube.upload"])
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
print("\nYT_CLIENT_ID     =", creds.client_id)
print("YT_CLIENT_SECRET =", creds.client_secret)
print("YT_REFRESH_TOKEN =", creds.refresh_token)
