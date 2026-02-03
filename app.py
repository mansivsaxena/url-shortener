from flask import Flask, redirect, request, jsonify
import random
import string 

app = Flask(__name__)

short_urls = {}

def shorten_url(length=7):
    # todo - implement a proper algorithm for encoding
    output_str = ""
    for _ in range(length):
        s = random.choice(string.ascii_letters)
        output_str += s

    return output_str

# todo - url regex validation, checks for if url exists in dict - format errors accordingly
# todo - error messages format them to be specific
@app.route("/", methods=["GET", "POST", "DELETE"])
def manage_urls():
    if request.method == "GET": # get all short url IDs
        return jsonify(list(short_urls.keys())), 200
    elif request.method == "POST": # shorten a url and insert in dict, json body with "url" field needed
        req_body = request.get_json()
        if not req_body or "url" not in req_body:
            return jsonify({"error": "error"}), 400
        long_url = req_body["url"]
        id = shorten_url()
        while id in short_urls:  
            id = shorten_url()
        short_urls[id] = long_url
        return jsonify({"id": id}), 201
    elif request.method == "DELETE": 
        # todo - implementation - delete all? - left ambiguous in pdf
        return "", 404

@app.route("/:id", methods=["GET", "PUT", "DELETE"])
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
            return jsonify({"error": "error"}), 400
        if id not in short_urls:
            return "", 404
        short_urls[id] = req_body["url"]
        return "", 200
    elif request.method == "DELETE": 
        if id in short_urls:
            del short_urls[id]
            return "", 204
        else:
            return "", 404
    
if __name__ == "__main__":
    app.run(debug=True)