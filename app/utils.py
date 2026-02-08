import json
import re
from datetime import datetime, timezone

from flask import request

BASE62_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

url_counter = 0

# regex pattern to validate urls with protocol
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

# regex pattern to validate partial urls without protocol
PARTIAL_URL_PATTERN = re.compile(
    r'^(?:www\.)?'  # optional www.
    r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,}',  # domain name
    re.IGNORECASE
)

def is_valid_url(url):
    if URL_PATTERN.match(url):
        return True
    
    # accept partial urls (www.google.com, google.com)
    return PARTIAL_URL_PATTERN.match(url) is not None

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

    req_body = (request.data or b"").strip()
    if not req_body:
        return None
    try:
        return json.loads(req_body.decode("utf-8"))
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

###
###    ------ Utils for Bonus Features ------
###

def is_valid_custom_id(custom_id):
    if not custom_id:
        return False
    if len(custom_id) < 1 or len(custom_id) > 50:
        return False
    
    if not (custom_id[0].isalnum() and custom_id[-1].isalnum()):
        return False
    
    allowed = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    if not all(c in allowed for c in custom_id):
        return False
    
    return True

def parse_expiration(body):
    if not isinstance(body, dict):
        return None

    if "expires_at" in body:
        expiry_datetime = body["expires_at"]
        try:
            dt = datetime.fromisoformat(str(expiry_datetime).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (ValueError, TypeError):
            raise ValueError("Invalid expires_at format; expected ISO-8601")
        
def expiration_check(short_urls, analytics, expirations):
    now = datetime.now(timezone.utc)
    expired_ids = [
        short_id for short_id, exp in expirations.items()
        if exp is not None and now >= exp
    ]
    for short_id in expired_ids:
        short_urls.pop(short_id, None)
        analytics.pop(short_id, None)
        expirations.pop(short_id, None)
    return expired_ids
