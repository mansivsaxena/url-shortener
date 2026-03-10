from collections import OrderedDict
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from url_shortener_service.utils import (
    shorten_url,
    is_valid_url,
    bad_request,
    extract_url,
    get_json_body,
    is_valid_custom_id,
    parse_expiration,
    cleanup_expired_urls,
    require_authenticated_user,
)
from models import User, db, URL

main_bp = Blueprint("main", __name__)

@main_bp.route("/", methods=["GET", "POST", "DELETE"])
def manage_urls():
    """
        GET: Get all short URL IDs with optional filtering by a substring, and sorting by short ID/long URL
        POST: Shorten a new URL provided in the JSON body (if valid URL format) and return the generated ID
        DELETE: Clear all stored URL entries
        Bonus:
            - Support custom short IDs
            - URL expiration times in POST body
            - Expiration check before all endpoints to remove expired URLs
            - Analytics for each short URL (click count, last accessed time)

        Assignment 2 addition: 
            - Validate JWT token in Authorization header
            - Verify token by calling auth_service API 
            - Allow access to URLs owned by the user identified in the token payload
    """
    username, auth_error = require_authenticated_user(request)
    if auth_error:
        return auth_error

    cleanup_expired_urls()

    owner_id = User.query.filter_by(username=username).first().id

    if request.method == "GET":
        contains = request.args.get("contains")
        sort_by = request.args.get("sort_by")  # has to be either "short"/"long"

        items = [(url.short_code, url.long_url) for url in URL.query.filter_by(owner_id=owner_id).all()]

        # filtering
        if contains:
            items = [(k, v) for k, v in items if contains in v]

        # sorting
        if sort_by == "short":
            items.sort(key=lambda x: x[0])
        elif sort_by == "long":
            items.sort(key=lambda x: x[1])

        return jsonify({"value": OrderedDict(items) if items else None}), 200
    
    elif request.method == "POST":
        req_body = get_json_body()
        long_url = extract_url(req_body)

        if not long_url or not is_valid_url(long_url):
            return bad_request()

        try: # expiration
            exp_dt = parse_expiration(req_body)
        except ValueError:
            return bad_request()

        custom_id = req_body.get("custom_id") if req_body else None
        short_urls = {url.short_code for url in URL.query.all()}
        if custom_id:
            custom_id = custom_id.strip().lower()
            if custom_id in short_urls:
                return jsonify({
                    "error": "ID already exists. Please choose a different one."
                }), 400
            
            if not is_valid_custom_id(custom_id):
                return jsonify({
                    "error": "Invalid custom ID. Must be 1-50 alphanumeric characters (hyphens and underscores allowed, but not at start/end)"
                }), 400
            
            short_id = custom_id
        else:
            short_id = shorten_url()
            while short_id in short_urls:     
                short_id = shorten_url()

        new_url_entry = URL(short_code=short_id, long_url=long_url, owner_id=owner_id, expires_at=exp_dt)
        db.session.add(new_url_entry)
        db.session.commit()
        return jsonify({"id": short_id}), 201

    elif request.method == "DELETE":
        URL.query.filter_by(owner_id=owner_id).delete()
        db.session.commit()

        return "", 404

@main_bp.route("/<id>", methods=["GET", "PUT", "DELETE"])
def handle_url(id):
    """
        :param id: the short URL ID to retrieve, update, or delete
        GET: Redirect to the long URL mapped to the short ID
        PUT: Update the long URL for the given short ID with a new URL provided
        DELETE: Remove the short URL entry for the given ID

        Assignment 2 addition: Authentication (described above)
    """
    if request.method == "GET":
        cleanup_expired_urls()
        
        url_entry = URL.query.filter_by(short_code=id).first()
        if url_entry:
            url_entry.click_count += 1
            url_entry.last_accessed = datetime.now(timezone.utc)
            db.session.commit()
            return jsonify({"value": url_entry.long_url}), 301
        else:
            return jsonify({"error": f"Short URL ID: {id} not found"}), 404 

    username, auth_error = require_authenticated_user(request)
    if auth_error:
        return auth_error

    cleanup_expired_urls()

    short_urls = {url.short_code for url in URL.query.all()}
    owner_id = URL.query.filter_by(short_code=id).first().owner_id
    username_from_db = User.query.filter_by(id=owner_id).first().username
    
    if request.method == "PUT":
        if id not in short_urls:
            return jsonify({"error": f"Short URL ID: {id} not found"}), 404
        if username != username_from_db:
            return "forbidden", 403

        req_body = get_json_body()
        new_url = extract_url(req_body)

        if not new_url or not is_valid_url(new_url):
            return bad_request()

        update_entry = URL.query.filter_by(short_code=id).first()
        update_entry.long_url = new_url
        db.session.commit()
        return jsonify({"message": f"URL for short ID {id} updated successfully"}), 200

    elif request.method == "DELETE": 
        if id not in short_urls:
            return jsonify({"error": f"Short URL ID: {id} not found"}), 404
        owner_id = URL.query.filter_by(short_code=id).first().owner_id
        username_from_db = User.query.filter_by(id=owner_id).first().username
        if username != username_from_db:
            return "forbidden", 403

        URL.query.filter_by(short_code=id).delete()
        db.session.commit()

        # 204 doesnt allow any response body so empty message
        return "", 204
 
@main_bp.route("/bulk", methods=["POST"])
def bulk_shorten():
    """
        POST: Shorten multiple URLs provided in the request body and return a mapping of generated IDs to original URLs, and show any failed entries
        Assignment 2 addition: Authentication (described above)
    """
    username, auth_error = require_authenticated_user(request)
    if auth_error:
        return auth_error

    existing_codes = {url.short_code for url in URL.query.all()}
    cleanup_expired_urls()
    owner_id = User.query.filter_by(username=username).first().id

    req_body = get_json_body()
    if not isinstance(req_body, dict):
        return bad_request()

    urls = req_body.get("values")
    success = {}
    failed = []
    new_url_objects = [] 

    for url in urls:
        if not isinstance(url, str) or not url or not is_valid_url(url):
            failed.append(url)
            continue

        short_id = shorten_url()
        while short_id in existing_codes or short_id in success:
            short_id = shorten_url()
        
        success[short_id] = url
        
        new_url_objects.append(URL(
            short_code=short_id, 
            long_url=url, 
            owner_id=owner_id
        ))

    if new_url_objects:
        db.session.add_all(new_url_objects)
        db.session.commit()

    return jsonify({
        "success": success,
        "failed": failed
    }), 201