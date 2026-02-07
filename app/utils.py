import json
import re
from datetime import datetime, timedelta, timezone

from flask import request

BASE62_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

url_counter = 0

# regex pattern to validate urls
URL_PATTERN = re.compile(
    r'^https?://' # must start with http:// or https://
    r'(?:'
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,}\.?|' # domain name
        r'localhost|' # or localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}' # or ip address
    r')'
    r'(?::\d+)?' # optional port number
    r'(?:/?|[/?]\S+)?$', # optional path
    re.IGNORECASE,
)

def is_valid_url(url):
    return URL_PATTERN.match(url) is not None

def bad_request():
    return "error", 400

def extract_url(body):
    if not isinstance(body, dict):
        return None
    return body.get("url") or body.get("value")

def get_json_body():
    body = request.get_json(silent=True)
    if body is not None:
        return body

    raw = (request.data or b"").strip()
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None

def parse_expiration(body):
    if not isinstance(body, dict):
        return None

    if "expires_at" in body:
        raw = body["expires_at"]
        try:
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (ValueError, TypeError):
            raise ValueError("Invalid expires_at format; expected ISO-8601")

    if "ttl_seconds" in body:
        try:
            ttl = int(body["ttl_seconds"])
            if ttl <= 0:
                raise ValueError("ttl_seconds must be a positive integer")
            return datetime.now(timezone.utc) + timedelta(seconds=ttl)
        except (ValueError, TypeError):
            raise ValueError("Invalid ttl_seconds; expected a positive integer")

def is_expired(short_id, short_urls, analytics, expirations):
    exp = expirations.get(short_id)
    if exp is None:
        return False
    if datetime.now(timezone.utc) >= exp:
        short_urls.pop(short_id, None)
        analytics.pop(short_id, None)
        expirations.pop(short_id, None)
        return True
    return False

def shorten_url():
    global url_counter
    num = url_counter
    url_counter += 1
    if num == 0:
        return BASE62_CHARS[0]

    result = ""
    while num > 0:
        result = BASE62_CHARS[num % 62] + result
        num = num // 62
    return result