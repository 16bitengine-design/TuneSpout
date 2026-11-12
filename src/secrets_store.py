"""Keep a rotated TikTok refresh token safe in a public repo.

TikTok may hand back a new refresh token every time we refresh, and says to use
the new one. GitHub will not let a workflow change its own secrets, so the new
token is saved encrypted in the `state` branch. STATE_KEY (any long random
text, stored as a GitHub secret) is the password. Without it the token cannot
be read, even though the file is public.
"""
import base64
import hashlib
import json
from pathlib import Path


def _fernet(passphrase):
    from cryptography.fernet import Fernet
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(passphrase.encode()).digest()))


def fingerprint(value):
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def save_token(path, passphrase, token, secret_value):
    """Store `token`, tagged with which TIKTOK_REFRESH_TOKEN secret it replaces."""
    payload = json.dumps({"token": token, "for_secret": fingerprint(secret_value)}).encode()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_fernet(passphrase).encrypt(payload))


def load_token(path, passphrase, secret_value):
    """The saved token, or None if there is none, the key is wrong, or you have since
    put a fresh token in the secret (a new secret always wins over an old saved one)."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        data = json.loads(_fernet(passphrase).decrypt(path.read_bytes()))
    except Exception:
        return None
    return data["token"] if data.get("for_secret") == fingerprint(secret_value) else None
