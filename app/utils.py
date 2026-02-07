import json
import re

from flask import request

BASE62_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

url_counter = 0

# regex pattern to validate urls
URL_PATTERN = re.compile(
    r'^https?://'  # must start with http:// or https://
    r'(?:'
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,}\.?|'  # domain name
        r'localhost|'  # or localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'  # or ip address
    r')'
    r'(?::\d+)?'  # optional port number
    r'(?:/?|[/?]\S+)?$',  # optional path
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
