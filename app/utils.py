import json
import re
import string
import secrets

from flask import request

BASE62_CHARS = string.ascii_letters + string.digits
used_numbers = set()

def generate_random_number(bits=36):
    '''
    Using 2^36 because 2^36 = approx 62^6, so we get IDs of length 6
    '''
    return secrets.randbits(bits)

# regex pattern to validate urls with protocol
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

# regex pattern to validate partial urls without protocol
PARTIAL_URL_PATTERN = re.compile(
    r'^(?:www\.)?'  # optional www.
    r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,}',  # domain name
    re.IGNORECASE
)

def is_valid_url(url):
    # check full url with protocol
    if URL_PATTERN.match(url):
        return True
    
    # also accept partial urls (www.google.com, google.com)
    return PARTIAL_URL_PATTERN.match(url) is not None

def is_valid_custom_id(custom_id):
    if not custom_id:
        return False
    #do we need like reserved ids?
    if len(custom_id) < 1 or len(custom_id) > 50:
        return False
    
    if not (custom_id[0].isalnum() and custom_id[-1].isalnum()):
        return False
    
    allowed = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    if not all(c in allowed for c in custom_id):
        return False
    
    return True

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
    while True:
        num = generate_random_number()
        if num not in used_numbers:
            used_numbers.add(num)
            break

    if num == 0:
        return BASE62_CHARS[0]

    result = ""
    while num > 0:
        result = BASE62_CHARS[num % 62] + result
        num = num // 62
    return result