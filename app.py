from flask import Flask, redirect, request
import random
import string 

app = Flask(__name__)

short_urls = {}

def shorten_url(length=7):
    output_str = ""
    for _ in range(length):
        s = random.choice(string.ascii_letters)
        output_str += s

    return output_str

@app.route("/", methods = ["GET", "POST"])
def index():
    if request.method == "POST":
        long_url = request.form['long_url']
        short_url = shorten_url()
        while short_url in short_urls:  # Better way to ensure uniqueness
            short_url = shorten_url()
        short_urls[short_url] = long_url
        return f"Shortened URL: {request.url_root}{short_url}"
    
@app.route("/<short_url>")
def redirect_url(short_url):
    long_url = short_urls.get(short_url)
    if long_url:
        return redirect(long_url)
    else:
        return f"URL not found, current dictionary of URLs: {short_urls}", 404
    
if __name__ == "__main__":
    app.run(debug=True)