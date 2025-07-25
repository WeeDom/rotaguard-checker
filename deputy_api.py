#! /usr/bin/env python3
# deputy_api.py
import requests
import json
import os
from datetime import datetime, timedelta

TOKEN_FILE = "tokens.json"

tokens = {}
base_url = ""

def save_tokens(data):
    global tokens, base_url
    tokens = {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": (datetime.utcnow() + timedelta(seconds=data["expires_in"])).isoformat(),
        "base_url": data["endpoint"]
    }
    base_url = tokens["base_url"]
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

def load_tokens():
    global tokens, base_url
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            tokens = json.load(f)
            base_url = tokens["base_url"]
    else:
        raise FileNotFoundError("No saved tokens found.")

def is_token_expired():
    return datetime.utcnow() > datetime.fromisoformat(tokens["expires_at"])

def refresh_access_token():
    print("[*] Refreshing access token...")
    resp = requests.post(
        f"{base_url}/oauth/access_token",
        data={
            "client_id": DEPUTY_CLIENT_ID,
            "client_secret": DEPUTY_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
            "scope": "longlife_refresh_token",
        },
    )
    resp.raise_for_status()
    print("[+] Token refreshed.")
    save_tokens(resp.json())

# deputy_api.py
def exchange_code_for_tokens(code):
    print(f"[*] Exchanging {code} for access + refresh tokens...")
    data = {
        "client_id": DEPUTY_CLIENT_ID,
        "client_secret": DEPUTY_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": code,
        "scope": "longlife_refresh_token"
    }

    resp = requests.post("https://once.deputy.com/my/oauth/access_token", data=data)
    print(f"[=] Exchange status: {resp.status_code}")
    print(f"[=] Response: {resp.text}...")

    resp.raise_for_status()
    resp_json = resp.json()

    tokens = {
        "access_token": resp_json["access_token"],
        "refresh_token": resp_json["refresh_token"],
        "expires_at": (datetime.now() + timedelta(seconds=resp_json["expires_in"])).isoformat(),
        "base_url": f"https://{resp_json['endpoint']}"
    }

    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)
    print("[+] Tokens received.")


def get_deputy(endpoint, **kwargs):
    if not tokens:
        load_tokens()
    if is_token_expired():
        refresh_access_token()
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {tokens['access_token']}"
    resp = requests.get(f"{base_url}{endpoint}", headers=headers, **kwargs)
    if resp.status_code == 401:
        print("[!] Access token expired — retrying after refresh.")
        refresh_access_token()
        headers["Authorization"] = f"Bearer {tokens['access_token']}"
        resp = requests.get(f"{base_url}{endpoint}", headers=headers, **kwargs)
    resp.raise_for_status()
    return resp.json()

# Load site-specific configuration from tokens.json
SITE_CONFIG_KEYS = ["DEPUTY_CLIENT_ID", "DEPUTY_CLIENT_SECRET", "REDIRECT_URI"]

def load_site_config():
    global DEPUTY_CLIENT_ID, DEPUTY_CLIENT_SECRET, REDIRECT_URI
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            config = json.load(f)
            for key in SITE_CONFIG_KEYS:
                if key in config:
                    globals()[key] = config[key]
    else:
        raise FileNotFoundError("No site configuration found in tokens.json.")

# Ensure site-specific configuration is loaded before use
load_site_config()

# TEST
if __name__ == "__main__":
    # Use this only once to get new tokens
    # code = "3ee9fb09a38cd56cae92cce5364b5f1b"
    # exchange_code_for_tokens(code)
    load_tokens()
    # print("[*] Fetching 'me' endpoint...")
    # user = get_deputy("/api/v1/me")
    # print(json.dumps(user, indent=2))
