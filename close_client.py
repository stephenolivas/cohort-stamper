"""Shared Close API client with rate limiting and retry logic."""

import os
import time
import requests

CLOSE_API_KEY = os.environ["CLOSE_API_KEY"]
BASE_URL = "https://api.close.com/api/v1"
SLEEP = 0.5  # seconds between every API call — do not remove

session = requests.Session()
session.auth = (CLOSE_API_KEY, "")


def api_get(path, params=None, retry=5):
    """GET with rate limiting and 429 backoff."""
    url = f"{BASE_URL}{path}"
    for attempt in range(retry):
        time.sleep(SLEEP)
        resp = session.get(url, params=params, timeout=30)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 10))
            print(f"[rate limit] sleeping {wait}s", flush=True)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"GET {path} failed after {retry} attempts")


def api_put(path, body, retry=5):
    """PUT with rate limiting and 429 backoff."""
    url = f"{BASE_URL}{path}"
    for attempt in range(retry):
        time.sleep(SLEEP)
        resp = session.put(url, json=body, timeout=30)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 10))
            print(f"[rate limit] sleeping {wait}s", flush=True)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"PUT {path} failed after {retry} attempts")
