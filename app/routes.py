from flask import Blueprint, request, jsonify
from app.utils import shorten_url, is_valid_url, bad_request, extract_url, get_json_body

main_bp = Blueprint("main", __name__)

short_urls = {}

@main_bp.route("/", methods=["GET", "POST", "DELETE"])
def manage_urls():
    if request.method == "GET": # get all existing short ids
        ids = list(short_urls.keys())
        return jsonify({"value": ids if ids else None}), 200

    elif request.method == "POST": # shorten a url and insert it into dict
        req_body = get_json_body()
        long_url = extract_url(req_body)

        if not long_url or not is_valid_url(long_url):
            return bad_request()

        short_id = shorten_url()
        short_urls[short_id] = long_url
        return jsonify({"id": short_id}), 201

    elif request.method == "DELETE": # delete existing ids (404 as specified)
        short_urls.clear()
        return "", 404

@main_bp.route("/<id>", methods=["GET", "PUT", "DELETE"])
def handle_url(id):
    if request.method == "GET": # resolve a short id to its original url
        long_url = short_urls.get(id)
        if long_url is None:
            return jsonify({"error": f"Short URL ID: {id} not found"}), 404

        # return resolved url in response body
        resp = jsonify({"value": long_url})
        resp.status_code = 301
        return resp

    elif request.method == "PUT": # update mapping for existing short id
        if id not in short_urls:
            return jsonify({"error": f"Short URL ID: {id} not found"}), 404

        req_body = get_json_body()
        new_url = extract_url(req_body)

        # validate updated url before saving it
        if not new_url or not is_valid_url(new_url):
            return bad_request()

        short_urls[id] = new_url
        return jsonify({"message": f"URL for short ID {id} updated successfully"}), 200

    elif request.method == "DELETE": # delete mapping for an existing short id
        if id in short_urls:
            del short_urls[id]
            return "", 204

        return jsonify({"error": f"Short URL ID: {id} not found"}), 404