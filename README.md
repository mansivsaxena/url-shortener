# UvA - Web Services and Cloud-Based Systems

## Group 9 - Assignment 1 URL Shortener

Directories

```
url-shortener/
├── app/
│   ├── __init__.py    
│   ├── config.py          # config
│   ├── routes.py          # API endpoints
│   └── utils.py           # helper functions
├── run.py                 # start app 
├── test_1_marking_mk2.py  # mandatory tests
├── test_2_bonus.py  # additional bonus tests
├── read_from.csv          # test data
└── requirements.txt       # python dependencies
```

Starting the server -

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python run.py
```

The app will be available at http://127.0.0.1:8000

4. In another terminal, run the unit tests:

```bash
source .venv/bin/activate
python test_1_marking_mk2.py
```

## API (summary)

- GET `/` — list all short IDs 
- POST `/` — create a short URL (`{"value": "<url>"}`)
- GET `/<id>` — redirect (301) to the original URL
- PUT `/<id>` — update mapping (`{"value": "<new_url>"}`)
- DELETE `/<id>` — delete mapping

## Bonus features
- Sorting and Filtering: GET `/` with `sort_by=short` or `sort_by=long` to sort by short ID or original URL, and `contains=<substring>` to filter short URLs that contain a specific substring in the original URL
- Expiration: POST `/` with `{"value": "<url>", "expires_at": <timestamp>}` to set an expiration time for the short URL
- Analytics: Tracks the number of times the short URL has been accessed and the timestamps of latest access
- Custom short IDs: POST `/` with `{"value": "<url>", "custom_id": "<custom_id>"}` to specify a custom short ID (unique and alphanumeric)
- Bulk URL shortening: POST `/bulk` with `{"values": ["<url1>", "<url2>", ...]}` to create short URLs for multiple URLs in a single request

Run `python test_2_bonus.py` to test the bonus features.