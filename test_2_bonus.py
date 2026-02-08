import re
import unittest
import requests

URL = "http://127.0.0.1:8000"

class TestBonus(unittest.TestCase):

    def _post(self, body):
        return requests.post(f"{URL}/", json=body)

    def _get(self, sid):
        return requests.get(f"{URL}/{sid}", allow_redirects=False)

    def tearDown(self):
        requests.delete(f"{URL}/")

    def test_clicks_and_timestamp(self):
        sid = self._post({"value": "https://example.com"}).json()["id"]
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|\+00:00)$")
        for i in range(1, 4):
            body = self._get(sid).json()
            self.assertEqual(body["clicks"], i)
            self.assertRegex(body["last_accessed"], pattern)

    def test_no_analytics_on_404(self):
        self.assertNotIn("clicks", self._get("bogus").json())

    def test_put_preserves_clicks(self):
        sid = self._post({"value": "https://example.com"}).json()["id"]
        self._get(sid); self._get(sid)
        requests.put(f"{URL}/{sid}", json={"url": "https://example.com/new"})
        body = self._get(sid).json()
        self.assertEqual(body["value"], "https://example.com/new")
        self.assertEqual(body["clicks"], 3)

    def test_delete_clears_analytics(self):
        sid = self._post({"value": "https://example.com"}).json()["id"]
        self._get(sid)
        requests.delete(f"{URL}/{sid}")
        self.assertEqual(self._get(sid).status_code, 404)

    def test_expires_at_in_past_is_dead(self):
        sid = self._post({"value": "https://example.com", "expires_at": "2020-01-01T00:00:00Z"}).json()["id"]
        self.assertEqual(self._get(sid).status_code, 404)

    def test_bad_expires_at_returns_400(self):
        self.assertEqual(self._post({"value": "https://example.com", "expires_at": "nah"}).status_code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)
