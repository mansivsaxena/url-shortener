from flask import Blueprint, request, jsonify
from app.utils import shorten_url, is_valid_url, bad_request, extract_url, get_json_body, is_valid_custom_id

main_bp = Blueprint('main', __name__)

short_urls = {}

@main_bp.route("/", methods=["GET", "POST", "DELETE"])
def manage_urls():
    if request.method == "GET": # get all short url IDs
        ids = list(short_urls.keys())
        return jsonify({"value": ids if ids else None}), 200
    
    elif request.method == "POST": # shorten a url and insert in dict, json body with "url"/"value" field needed
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
    if request.method == "GET": #redirect to the url which maps to "id"
        long_url = short_urls.get(id)
        if long_url:
            resp = jsonify({"value": long_url})
            resp.status_code = 301
            return resp
        else:
            return jsonify({"error": f"Short URL ID: {id} not found"}), 404 
        
    elif request.method == "PUT": # change the long url which maps to "id"
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
            return jsonify({"message": ""}), 204 #204 doesnt allow any response body so empty message
        else:
            return jsonify({"error": f"Short URL ID: {id} not found"}), 404
 