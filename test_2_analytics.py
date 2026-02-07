import unittest
import re
import requests

BASE_URL = "http://127.0.0.1:8000"
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|\+00:00)$")


class TestAnalytics(unittest.TestCase):

    def _post(self, url="https://example.com"):
        r = requests.post(f"{BASE_URL}/", json={"value": url})
        self.assertEqual(r.status_code, 201)
        return r.json()["id"]

    def _get(self, sid):
        return requests.get(f"{BASE_URL}/{sid}", allow_redirects=False)

    def tearDown(self):
        requests.delete(f"{BASE_URL}/")

    def test_clicks_and_timestamp(self):
        sid = self._post()
        for i in range(1, 4):
            body = self._get(sid).json()
            self.assertEqual(body["clicks"], i)
            self.assertRegex(body["last_accessed"], ISO_RE)

    def test_no_analytics_on_404(self):
        body = self._get("bogus").json()
        self.assertNotIn("clicks", body)

    def test_delete_id_clears_analytics(self):
        sid = self._post()
        self._get(sid)
        requests.delete(f"{BASE_URL}/{sid}")
        self.assertEqual(self._get(sid).status_code, 404)

    def test_delete_all_clears_analytics(self):
        s1, s2 = self._post(), self._post("https://example.com/2")
        self._get(s1)
        self._get(s2)
        requests.delete(f"{BASE_URL}/")
        self.assertEqual(self._get(s1).status_code, 404)
        self.assertEqual(self._get(s2).status_code, 404)

    def test_put_preserves_clicks(self):
        sid = self._post()
        self._get(sid)
        self._get(sid)
        requests.put(f"{BASE_URL}/{sid}", json={"url": "https://example.com/new"})
        body = self._get(sid).json()
        self.assertEqual(body["value"], "https://example.com/new")
        self.assertEqual(body["clicks"], 3)

    def test_counters_are_independent(self):
        a, b = self._post(), self._post("https://example.com/b")
        self._get(a)
        self._get(a)
        self._get(b)
        self.assertEqual(self._get(a).json()["clicks"], 3)
        self.assertEqual(self._get(b).json()["clicks"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
