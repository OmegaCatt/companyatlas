import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from server import create_server


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.server = create_server(port=0, database_path=Path(cls.temp.name) / "atlas.sqlite", api_key="")
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        cls.temp.cleanup()

    def request(self, path, *, method="GET", body=None, cookie=None, extra_headers=None):
        headers = dict(extra_headers or {})
        if cookie:
            headers["Cookie"] = cookie
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        request = urllib.request.Request(self.base + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                return response.status, json.load(response), response.headers
        except urllib.error.HTTPError as error:
            return error.code, json.load(error), error.headers

    def login(self, role):
        status, result, headers = self.request("/api/login", method="POST", body={"role": role})
        self.assertEqual(status, 200)
        self.assertEqual(result["role"], role)
        return headers["Set-Cookie"].split(";", 1)[0]

    def test_login_and_backend_filtering(self):
        operations = self.login("operations")
        status, overview, _ = self.request("/api/overview", cookie=operations)
        self.assertEqual(status, 200)
        self.assertNotIn("hr-record", [file["id"] for file in overview["files"]])
        self.assertEqual(self.request("/api/files/hr-record", cookie=operations)[0], 404)
        self.assertEqual(self.request("/api/files/hr-record?role=leadership", cookie=operations)[0], 404)
        self.assertEqual(self.request("/api/evals", cookie=operations)[0], 403)
        people = self.login("people")
        status, overview, _ = self.request("/api/overview", cookie=people)
        self.assertEqual(status, 200)
        self.assertNotIn("orders", overview["metrics"])
        self.assertEqual(self.request("/api/files/hr-record", cookie=people)[0], 200)
        status, answer, _ = self.request("/api/ask", method="POST", body={"question": "Kolik objednávek bylo v roce 2024?"}, cookie=people)
        self.assertEqual((status, answer["kind"]), (403, "denied"))
        self.assertNotIn("count", answer)

    def test_exact_query_and_sources_over_http(self):
        cookie = self.login("operations")
        status, answer, _ = self.request("/api/ask", method="POST", body={"question": "Kolik objednávek bylo v roce 2024?"}, cookie=cookie)
        self.assertEqual((status, answer["count"]), (200, 12))
        self.assertEqual(answer["sources"][0]["id"], "orders-2024")

    def test_content_search_is_role_filtered_and_returns_metadata_only(self):
        self.assertEqual(self.request('/api/search?q=za%C5%A1kolen%C3%AD')[0], 401)
        people = self.login('people')
        status, result, _ = self.request('/api/search?q=za%C5%A1kolen%C3%AD', cookie=people)
        self.assertEqual(status, 200)
        self.assertTrue(result['files'])
        self.assertTrue(all('content' not in item for item in result['files']))
        status, content_match, _ = self.request('/api/search?q=zastupov%C3%A1n%C3%AD', cookie=people)
        self.assertEqual(status, 200)
        self.assertIn('hr-leave', [item['id'] for item in content_match['files']])
        self.assertEqual(self.request('/api/search?q=objedn%C3%A1vek', cookie=people)[1]['files'], [])
        operations = self.login('operations')
        self.assertEqual(self.request('/api/search?q=za%C5%A1kolen%C3%AD', cookie=operations)[1]['files'], [])
        self.assertEqual(self.request('/api/search?q=ab', cookie=operations)[0], 400)

    def test_rejects_cross_origin_oversize_and_bad_role(self):
        status, _, _ = self.request("/api/login", method="POST", body={"role": "root"})
        self.assertEqual(status, 400)
        status, _, _ = self.request("/api/login", method="POST", body={"role": "leadership"}, extra_headers={"Origin": "https://attacker.example"})
        self.assertEqual(status, 403)
        status, _, _ = self.request("/api/health", extra_headers={"Host": "attacker.example"})
        self.assertEqual(status, 403)
        cookie = self.login("operations")
        status, _, _ = self.request("/api/ask", method="POST", body={"question": "x" * 5000}, cookie=cookie)
        self.assertEqual(status, 400)

    def test_demo_qa_panel_and_security_headers(self):
        owner = self.login("leadership")
        status, result, headers = self.request("/api/evals", cookie=owner)
        self.assertEqual(status, 200)
        self.assertTrue(all(item["passed"] for item in result["checks"]))
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
        self.assertEqual(self.request("/api/overview")[0], 401)


if __name__ == "__main__":
    unittest.main()
