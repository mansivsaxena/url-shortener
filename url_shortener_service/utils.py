import re, json, requests
from datetime import datetime, timezone
from flask import current_app, request

BASE62_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

url_counter = 0

URL_PATTERN = re.compile(
    r'^https?://'                                  
    r'(?:'                                        
        r'(?:'                                     
            r'[A-Z0-9]'                             # domain
            r'(?:[A-Z0-9-]{0,61}[A-Z0-9])?'         
            r'\.'                                   
        r')+'                                       # subdomains allowed
        r'[A-Z]{2,}\.?'                             # TLD 
        r'|localhost'                               # or localhost
        r'|\d{1,3}(?:\.\d{1,3}){3}'                 # or IPv4 
    r')'
    r'(?::\d+)?'                                   # optional ':port'
    r'(?:[/?]\S*)?$',                              # optional path/query
    re.IGNORECASE
)

# without protocol
PARTIAL_URL_PATTERN = re.compile(
    r'^(?:www\.)?'                                 
    r'(?:'                                         # domain 
        r'[A-Z0-9]'
        r'(?:[A-Z0-9-]{0,61}[A-Z0-9])?'
        r'\.'
    r')+'
    r'[A-Z]{2,}\.?$',                              # TLD 
    re.IGNORECASE
)

def is_valid_url(url):
    if URL_PATTERN.match(url):
        return True
    
    # accept partial urls 
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

def cleanup_expired_urls(short_urls, analytics, expirations, owners):
    expired_ids = expiration_check(short_urls, analytics, expirations)
    for short_id in expired_ids:
        owners.pop(short_id, None)

###
###    ------ Utils for Assignment 2 ------
###

def authenticate_request(req):
    # extract token from auth header
    auth_header = (req.headers.get("Authorization") or "").strip()
    if not auth_header:
        return False, None

    # send validation request to auth_service
    base_url = current_app.config.get("AUTH_SERVICE_URL").rstrip("/")
    validate_url = f"{base_url}/users/validate"
    timeout = float(current_app.config.get("AUTH_VALIDATE_TIMEOUT_SECONDS", 1.0))
    response = requests.get(
        validate_url,
        headers={"Authorization": auth_header},
        timeout=timeout,
    )

    # check for unsuccessful response from auth_service
    if response.status_code != 200:
        return False, None

    # parse response and extract username
    try:
        payload = response.json()
    except ValueError:
        return False, None

    username = payload.get("username") if isinstance(payload, dict) else None
    if not isinstance(username, str) or not username:
        return False, None

    return True, username

def require_authenticated_user(req):
    is_valid, username = authenticate_request(req)
    if not is_valid:
        return None, ("forbidden", 403)
    return username, None
