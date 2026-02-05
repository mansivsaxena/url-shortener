from flask import Blueprint, request, jsonify, redirect
from app.utils import shorten_url, validate_url

main_bp = Blueprint('main', __name__)

short_urls = {}

# todo - url regex validation, checks for if url exists in dict - format errors accordingly
# todo - error messages format them to be specific
@main_bp.route("/", methods=["GET", "POST", "DELETE"])
def manage_urls():
    if request.method == "GET": # get all short url IDs
        return jsonify(list(short_urls.keys())), 200
    
    elif request.method == "POST": # shorten a url and insert in dict, json body with "url" field needed
        req_body = request.get_json()
        if not req_body or "url" not in req_body:
            return jsonify({"error": "Missing 'url' field in request body"}), 400
        long_url = req_body["url"]

        if not validate_url(long_url):
            return jsonify({"error": "Invalid URL format"}), 400
        
        id = shorten_url()
        while id in short_urls:  
            id = shorten_url()
        short_urls[id] = long_url
        return jsonify({"id": id}), 201
    
    elif request.method == "DELETE": 
        # todo - implementation - delete all? - left ambiguous in pdf
        return "", 404

@main_bp.route("/:id", methods=["GET", "PUT", "DELETE"])
def handle_url(id):
    if request.method == "GET": #redirect to the url which maps to "id"
        long_url = short_urls.get(id)
        if long_url:
            return redirect(long_url, code=301)
        else:
            return "", 404 
        
    elif request.method == "PUT": # change the long url which maps to "id"
        req_body = request.get_json()
        if not req_body or "url" not in req_body:
            return jsonify({"error": "Missing 'url' field in request body"}), 400
        if id not in short_urls:
            return jsonify({"error": "Short URL not found"}), 404
        new_url = req_body["url"]
        if not validate_url(new_url):
            return jsonify({"error": "Invalid URL format"}), 400
        
        short_urls[id] = new_url
        return "", 200
    
    elif request.method == "DELETE": 
        if id in short_urls:
            del short_urls[id]
            return "", 204
        else:
            return jsonify({"error": "Short URL not found"}), 404
 