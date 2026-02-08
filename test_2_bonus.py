import unittest
import requests
import json
import time
from datetime import datetime, timezone, timedelta


class TestBonusFeatures(unittest.TestCase):
    base_url = "http://127.0.0.1:8000"

    def tearDown(self):
        requests.delete(f"{self.base_url}/")

    # custom id: create and retrieve
    def test_custom_id_basic(self):
        resp = requests.post(f"{self.base_url}/", json={"value": "https://example.com", "custom_id": "my-link"})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["id"], "my-link")
        resp2 = requests.get(f"{self.base_url}/my-link")
        self.assertEqual(resp2.status_code, 301)
        self.assertEqual(resp2.json()["value"], "https://example.com")

    # custom id: duplicate should 400
    def test_custom_id_duplicate(self):
        requests.post(f"{self.base_url}/", json={"value": "https://google.com", "custom_id": "taken"})
        resp = requests.post(f"{self.base_url}/", json={"value": "https://bing.com", "custom_id": "taken"})
        self.assertEqual(resp.status_code, 400)

    # analytics: click count increments
    def test_analytics_click_count(self):
        sid = requests.post(f"{self.base_url}/", json={"value": "https://example.com"}).json()["id"]
        for i in range(1, 4):
            r = requests.get(f"{self.base_url}/{sid}")
            self.assertEqual(r.json()["analytics"]["click_count"], i)

    # analytics: last_accessed gets set
    def test_analytics_last_accessed(self):
        sid = requests.post(f"{self.base_url}/", json={"value": "https://example.com"}).json()["id"]
        r = requests.get(f"{self.base_url}/{sid}")
        last = r.json()["analytics"]["last_accessed"]
        self.assertIsNotNone(last)
        self.assertIn("T", last)

    # analytics: PUT should keep click count
    def test_put_keeps_analytics(self):
        sid = requests.post(f"{self.base_url}/", json={"value": "https://example.com"}).json()["id"]
        requests.get(f"{self.base_url}/{sid}")
        requests.get(f"{self.base_url}/{sid}")
        requests.put(f"{self.base_url}/{sid}", data=json.dumps({"url": "https://changed.com"}))
        r = requests.get(f"{self.base_url}/{sid}")
        self.assertEqual(r.json()["value"], "https://changed.com")
        self.assertEqual(r.json()["analytics"]["click_count"], 3)

    # expiration: expired URL should 404
    def test_expiration_real(self):
        expires = (datetime.now(timezone.utc) + timedelta(seconds=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        sid = requests.post(f"{self.base_url}/", json={
            "value": "https://example.com", "expires_at": expires
        }).json()["id"]
        self.assertEqual(requests.get(f"{self.base_url}/{sid}").status_code, 301)
        time.sleep(3)
        self.assertEqual(requests.get(f"{self.base_url}/{sid}").status_code, 404)

    # filtering: by substring
    def test_filter_by_contains(self):
        requests.post(f"{self.base_url}/", json={"value": "https://en.wikipedia.org/wiki/Python"})
        requests.post(f"{self.base_url}/", json={"value": "https://google.com"})
        resp = requests.get(f"{self.base_url}/", params={"contains": "wikipedia"})
        urls = resp.json()["value"]
        self.assertIsNotNone(urls)
        for url in urls.values():
            self.assertIn("wikipedia", url)

    # sorting: by short id
    def test_sort_by_short(self):
        requests.post(f"{self.base_url}/", json={"value": "https://a.com"})
        requests.post(f"{self.base_url}/", json={"value": "https://b.com"})
        requests.post(f"{self.base_url}/", json={"value": "https://c.com"})
        resp = requests.get(f"{self.base_url}/", params={"sort_by": "short"})
        keys = list(resp.json()["value"].keys())
        self.assertEqual(keys, sorted(keys))

    # bulk: shorten multiple urls at once
    def test_bulk_shorten(self):
        resp = requests.post(f"{self.base_url}/bulk", json={
            "values": ["https://google.com", "https://github.com", "https://stackoverflow.com"]
        })
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(len(resp.json()["success"]), 3)
        self.assertEqual(len(resp.json()["failed"]), 0)

    # bulk: created urls should be GETable
    def test_bulk_urls_are_accessible(self):
        resp = requests.post(f"{self.base_url}/bulk", json={
            "values": ["https://example.com/page1", "https://example.com/page2"]
        })
        for sid, url in resp.json()["success"].items():
            r = requests.get(f"{self.base_url}/{sid}")
            self.assertEqual(r.status_code, 301)
            self.assertEqual(r.json()["value"], url)


if __name__ == "__main__":
    unittest.main()
