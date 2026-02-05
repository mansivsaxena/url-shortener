import random
import re

BASE62_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

url_counter = random.randint(100000, 999999)

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
    re.IGNORECASE
)

def validate_url(url):
    return len(url) > 0 and URL_PATTERN.match(url) is not None

def shorten_url():
    # increment counter and convert to base62
    global url_counter
    url_counter += 1

    num = url_counter
    if num == 0:
        return BASE62_CHARS[0]

    result = ""
    while num > 0:
        result = BASE62_CHARS[num % 62] + result
        num = num // 62
    return result
