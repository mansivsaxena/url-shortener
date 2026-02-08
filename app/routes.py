from flask import Blueprint, request, jsonify
from app.utils import shorten_url, is_valid_url, bad_request, extract_url, get_json_body, is_valid_custom_id

main_bp = Blueprint('main', __name__)

short_urls = {}

@main_bp.route("/", methods=["GET", "POST", "DELETE"])
def manage_urls():
    """
        GET: Get all short URL IDs with optional filtering by domain or substring, and sorting by short ID/long URL
        POST: Shorten a new URL provided in the JSON body and return the generated ID
        DELETE: Clear all stored URL entries
    """
    if request.method == "GET":
        domain = request.args.get("domain")
        contains = request.args.get("contains")
        sort_by = request.args.get("sort")  # can be "short"/"long"

        items = list(short_urls.items())

        # filtering
        if domain:
            items = [(k, v) for k, v in items if domain in v]
        if contains:
            items = [(k, v) for k, v in items if contains in v]

        # sorting
        if sort_by == "short":
            items.sort(key=lambda x: x[0])
        elif sort_by == "long":
            items.sort(key=lambda x: x[1])

        result = {k: v for k, v in items}

        return jsonify({"value": result if result else None}), 200
    
    elif request.method == "POST":
        req_body = get_json_body()
        long_url = extract_url(req_body)
        if not long_url:
            return bad_request()

        if not is_valid_url(long_url):
            return bad_request()

        custom_id = req_body.get("custom_id") if req_body else None
    
        if custom_id:
            custom_id = custom_id.strip().lower()
            if not is_valid_custom_id(custom_id):
                return jsonify({
                    "error": "Invalid custom ID. Must be 1-50 alphanumeric characters (hyphens and underscores allowed, but not at start/end)"
                }), 400
            
            if custom_id in short_urls:
                return jsonify({
                    "error": "Custom ID already exists. Please choose a different one."
                }), 400
            
            short_id = custom_id
        else:
            short_id = shorten_url()

        short_urls[short_id] = long_url
        return jsonify({"id": short_id}), 201
    
    elif request.method == "DELETE": 
        short_urls.clear()
        return "", 404

@main_bp.route("/<id>", methods=["GET", "PUT", "DELETE"])
def handle_url(id):
    """
        :param id: the short URL ID to retrieve, update, or delete
        GET: Redirect to the long URL mapped to the short ID
        PUT: Update the long URL for the given short ID with a new URL provided
        DELETE: Remove the short URL entry for the given ID
    """
    if request.method == "GET":
        long_url = short_urls.get(id)
        if long_url:
            resp = jsonify({"value": long_url})
            resp.status_code = 301
            return resp
        else:
            return jsonify({"error": f"Short URL ID: {id} not found"}), 404 
        
    elif request.method == "PUT":
        if id not in short_urls:
            return jsonify({"error": f"Short URL ID: {id} not found"}), 404

        req_body = get_json_body()
        new_url = extract_url(req_body)
        if not new_url:
            return bad_request()

        if not is_valid_url(new_url):
            return bad_request()

        short_urls[id] = new_url  
        return jsonify({"message": f"URL for short ID {id} updated to {new_url} successfully"}), 200
    
    elif request.method == "DELETE": 
        if id in short_urls:
            del short_urls[id]
            return jsonify({"message": ""}), 204 # 204 doesnt allow any response body so empty message
        else:
            return jsonify({"error": f"Short URL ID: {id} not found"}), 404
 
@main_bp.route("/bulk", methods=["POST"])
def bulk_shorten():
    """
        POST: Shorten multiple URLs provided in the request body and return a mapping of generated IDs to original URLs, and show any failed entries
    """
    req_body = get_json_body()

    if not isinstance(req_body, dict):
        return bad_request()

    urls = req_body.get("values")
    if not isinstance(urls, list) or not urls:
        return bad_request()

    success = {}
    failed = []

    for url in urls:
        if not isinstance(url, str) or not url or not is_valid_url(url):
            failed.append(url)
            continue

        short_id = shorten_url()
        short_urls[short_id] = url
        success[short_id] = url

    return jsonify({
        "success": success,
        "failed": failed
    }), 201
