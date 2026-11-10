"""Local-only portfolio server for CompanyAtlas."""

from __future__ import annotations

import json
import re
import secrets
import threading
import auth
import documents as document_store
import time
from contextlib import closing
from datetime import datetime, timezone
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from ai import AIUnavailable, MODEL, answer_with_ai, read_api_key
from core import (
    ROLE_GROUPS,
    ROLE_NAMES,
    ROOT,
    answer_order_count,
    answer_question,
    audit,
    connect,
    get_document,
    init_database,
    is_order_count_question,
    metrics,
    search_documents,
    visible_documents,
)


WEB_ROOT = ROOT / "web"
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/simple.css": ("simple.css", "text/css; charset=utf-8"),
    "/favicon.svg": ("favicon.svg", "image/svg+xml"),
}
COOKIE_NAME = "atlas_demo_session"
MAX_BODY = 4096


class RateLimited(RuntimeError):
    pass


class AppState:
    def __init__(self, database_path: Path, api_key: str = "", ai_transport=None):
        self.database_path = database_path
        self.api_key = api_key
        self.ai_transport = ai_transport
        self.sessions = {}
        self.login_attempts = []
        self.import_slots = threading.BoundedSemaphore(2)
        self.lock = threading.Lock()
        self.ai_slots = threading.BoundedSemaphore(2)
        self.ai_window_start = time.monotonic()
        self.ai_count = 0
        database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(connect(database_path)) as connection:
            init_database(connection)
            auth.init(connection)

    def create_session(self, user):
        token=secrets.token_urlsafe(32)
        with self.lock:
            self.sessions={key:value for key,value in self.sessions.items() if value[2]>time.monotonic()}
            if len(self.sessions)>=1000:raise ValueError('Limit relací byl vyčerpán.')
            self.sessions[token]=(user['username'],user['revision'],time.monotonic()+3600)
        return token

    def session_identity(self,token):
        with self.lock:value=self.sessions.get(token)
        if not value or value[2]<=time.monotonic():return None
        with closing(connect(self.database_path)) as connection:return auth.identity(connection,value[0],value[1])

    def session_role(self,token):
        user=self.session_identity(token)
        return user['role'] if user else None

    def answer_ai(self, question: str, documents: list[dict]) -> dict:
        if not self.api_key:
            raise AIUnavailable("AI není na místním serveru nastavena.")
        if not self.ai_slots.acquire(blocking=False):
            raise RateLimited("Právě běží dvě AI odpovědi. Zkuste to za chvíli.")
        try:
            with self.lock:
                if time.monotonic() - self.ai_window_start >= 86400:
                    self.ai_window_start = time.monotonic()
                    self.ai_count = 0
                if self.ai_count >= 20:
                    raise RateLimited("Denní limit 20 AI dotazů byl vyčerpán.")
                self.ai_count += 1
            return answer_with_ai(question, documents, self.api_key, transport=self.ai_transport)
        finally:
            self.ai_slots.release()


def quality_checks(connection) -> list[dict]:
    checks = [
        ("Počet objednávek 2024", answer_order_count(connection, "operations", "Kolik objednávek bylo v roce 2024?")["count"] == 12),
        ("Součet hodnoty objednávek 2024", answer_question(connection, "operations", "Jaká byla celková hodnota objednávek v roce 2024?")["amountCzk"] == 210300),
        ("Filtr zákazníka", answer_order_count(connection, "operations", "Kolik objednávek 2024 bylo pro Studio Javor?")["count"] == 5),
        ("Nejednoznačný zákazník", len(answer_order_count(connection, "operations", "Kolik objednávek bylo pro Novák?").get("options", [])) == 2),
        ("Personální tým nečte objednávky", answer_order_count(connection, "people", "Kolik objednávek 2024?")["kind"] == "denied"),
        ("Provoz nečte osobní složku", get_document(connection, "operations", "hr-record") is None),
        ("Personální tým nečte plán vedení", get_document(connection, "people", "leadership-plan") is None),
        ("Provozní vyhledávání nevydá HR dokument", all(item["id"] != "hr-record" for item in search_documents(connection, "operations", "osobní složka Kláry"))),
    ]
    return [{"name": name, "passed": passed} for name, passed in checks]


class AtlasHandler(BaseHTTPRequestHandler):
    server_version = "CompanyAtlas/0.1"

    @property
    def state(self) -> AppState:
        return self.server.state

    def log_message(self, *_args):
        # Questions and session tokens must not enter access logs.
        return

    def _headers(self, status: int, content_type: str, length: int, extra: dict | None = None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()

    def _json(self, status: int, data: dict | list, extra: dict | None = None):
        body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8", len(body), extra)
        self.wfile.write(body)

    def _read_json(self,limit=MAX_BODY) -> dict:
        if self.headers.get("Content-Type", "").split(";", 1)[0].lower() != "application/json":
            raise ValueError("Očekávám JSON požadavek.")
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError as error:
            raise ValueError("Neplatná délka požadavku.") from error
        if length < 2 or length > limit:
            raise ValueError("Požadavek je příliš velký nebo prázdný.")
        self.connection.settimeout(10)
        try:
            data = json.loads(self.rfile.read(length))
        finally:
            self.connection.settimeout(None)
        if not isinstance(data, dict):
            raise ValueError("Očekávám JSON objekt.")
        return data

    def _session_token(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            return None
        token = cookie[COOKIE_NAME].value if COOKIE_NAME in cookie else ""
        return token

    def _session_role(self):
        return self.state.session_role(self._session_token())

    def _require_role(self) -> str | None:
        role = self._session_role()
        if not role:
            self._json(HTTPStatus.UNAUTHORIZED, {"error": "Přihlaste se ukázkovým účtem."})
        return role

    def _valid_host(self) -> bool:
        if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
            self._json(HTTPStatus.FORBIDDEN, {"error": "Místní server přijímá jen adresu 127.0.0.1."})
            return False
        return True

    def do_GET(self):
        if not self._valid_host():
            return
        path = urlsplit(self.path).path
        if path in STATIC_FILES:
            filename, content_type = STATIC_FILES[path]
            body = (WEB_ROOT / filename).read_bytes()
            self._headers(HTTPStatus.OK, content_type, len(body))
            self.wfile.write(body)
            return
        if path == "/api/health":
            self._json(HTTPStatus.OK, {"ok": True, "aiConfigured": bool(self.state.api_key), "model": MODEL})
            return
        if path == "/api/session":
            user=self.state.session_identity(self._session_token())
            with closing(connect(self.state.database_path)) as connection:version=document_store.revision(connection)
            self._json(HTTPStatus.OK,{"role":user["role"] if user else None,"username":user["username"] if user else None,"catalogRevision":version})
            return
        if not path.startswith("/api/"):
            self._json(HTTPStatus.NOT_FOUND, {"error": "Nenalezeno."})
            return
        role = self._require_role()
        if not role:
            return
        with closing(connect(self.state.database_path)) as connection:
            if path == "/api/overview":
                self._json(HTTPStatus.OK, {"role": role, "name": ROLE_NAMES[role], "metrics": metrics(connection, role), "files": visible_documents(connection, role),"catalogRevision":document_store.revision(connection)})
            elif path == "/api/search":
                query = parse_qs(urlsplit(self.path).query).get("q", [""])[0].strip()
                if not 3 <= len(query) <= 100:
                    self._json(HTTPStatus.BAD_REQUEST, {"error": "Hledaný text musí mít 3 až 100 znaků."})
                    return
                matches = search_documents(connection, role, query, limit=30)
                self._json(HTTPStatus.OK, {"files": [{key: item[key] for key in ("id", "path", "title", "group_name", "kind", "description")} for item in matches]})
            elif path.startswith("/api/files/"):
                document_id = path.removeprefix("/api/files/")
                if not re.fullmatch(r"[a-z0-9-]{1,40}", document_id):
                    self._json(HTTPStatus.NOT_FOUND, {"error": "Soubor nebyl nalezen."})
                    return
                document = get_document(connection, role, document_id)
                if not document:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "Soubor nebyl nalezen."})
                    return
                requested=parse_qs(urlsplit(self.path).query).get("version",[None])[0]
                if requested is not None and requested!=str(document["version"]):
                    self._json(409,{"error":"Verze dokumentu se změnila. Obnovte podklady."});return
                audit(connection, role, "open_file", "allowed")
                self._json(HTTPStatus.OK, document)
            elif path == "/api/users" and role=="leadership":
                self._json(200,{"users":[dict(row) for row in connection.execute("SELECT username,role,active FROM users ORDER BY username")]})
            elif path == "/api/evals":
                if role != "leadership":
                    self._json(HTTPStatus.FORBIDDEN, {"error": "K této části nemáte přístup."})
                    return
                self._json(HTTPStatus.OK, {"checks": quality_checks(connection)})
            elif path == "/api/audit":
                if role != "leadership":
                    self._json(HTTPStatus.FORBIDDEN, {"error": "K této části nemáte přístup."})
                    return
                rows = [dict(row) for row in connection.execute("SELECT created_at, role, event, result FROM audit ORDER BY id DESC LIMIT 30")]
                self._json(HTTPStatus.OK, {"events": rows})
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "Nenalezeno."})

    def do_POST(self):
        if not self._valid_host():
            return
        path = urlsplit(self.path).path
        expected_origin = f"http://{self.headers.get('Host', '')}"
        origin = self.headers.get("Origin")
        if origin and origin != expected_origin:
            self._json(HTTPStatus.FORBIDDEN, {"error": "Cizí stránka nesmí volat místní API."})
            return
        if self.headers.get("Sec-Fetch-Site", "") == "cross-site":
            self._json(HTTPStatus.FORBIDDEN, {"error": "Cizí stránka nesmí volat místní API."})
            return
        try:
            body = self._read_json(2_800_000 if path=="/api/documents/import" and self._session_role()=="leadership" else MAX_BODY)
        except (ValueError, TimeoutError, OSError) as error:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(error) if isinstance(error, ValueError) else "Neplatný požadavek."})
            return
        if path == '/api/logout':
            with self.state.lock:self.state.sessions.pop(self._session_token(),None)
            self._json(200,{'ok':True},{'Set-Cookie':f'{COOKIE_NAME}=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'});return
        if path == '/api/login':
            if not isinstance(body.get('username'),str) or not isinstance(body.get('password'),str):self._json(400,{'error':'Zadejte účet a heslo.'});return
            with self.state.lock:
                now=time.monotonic();self.state.login_attempts=[value for value in self.state.login_attempts if value>now-60]
                if len(self.state.login_attempts)>=30:self._json(429,{'error':'Příliš mnoho pokusů. Zkuste později.'});return
                self.state.login_attempts.append(now)
            with closing(connect(self.state.database_path)) as connection:user=auth.authenticate(connection,body['username'],body['password'])
            if not user:self._json(401,{'error':'Neplatné přihlášení nebo neaktivní účet.'});return
            token=self.state.create_session(user)
            self._json(200,{'role':user['role'],'username':user['username']},{'Set-Cookie':f'{COOKIE_NAME}={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600'});return
        role = self._require_role()
        if not role:
            return
        if path in ['/api/documents/import','/api/documents/remove','/api/users/toggle']:
            if role!='leadership':self._json(403,{'error':'Správa je povolená jen vedení.'});return
            try:
                with closing(connect(self.state.database_path)) as connection:
                    if path=='/api/documents/import':
                        if not self.state.import_slots.acquire(blocking=False):self._json(429,{'error':'Probíhají dvě čtení dokumentů.'});return
                        try:result=document_store.import_document(connection,body)
                        finally:self.state.import_slots.release()
                    elif path=='/api/documents/remove':document_store.remove_document(connection,body.get('id'),body.get('expectedVersion'));result={'removed':True}
                    else:auth.toggle(connection,body.get('username'),body.get('active'));result={'updated':True}
                    audit(connection,role,'manage','done')
                self._json(200,result)
            except Exception as error:self._json(400,{'error':str(error) if isinstance(error,ValueError) else 'Čtení nebo změna dokumentu selhala.'})
            return
        if path != "/api/ask":
            self._json(HTTPStatus.NOT_FOUND, {"error": "Nenalezeno."})
            return
        question = body.get("question")
        if not isinstance(question, str) or not 5 <= len(question.strip()) <= 500:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "Dotaz musí mít 5 až 500 znaků."})
            return
        try:
            with closing(connect(self.state.database_path)) as connection:
                result = answer_question(connection, role, question.strip(), self.state.answer_ai if self.state.api_key else None)
                audit(connection, role, "ask", result["kind"])
            if self._session_role()!=role:
                self._json(401,{"error":"Oprávnění se změnila. Přihlaste se znovu."});return
            status = HTTPStatus.FORBIDDEN if result["kind"] == "denied" else HTTPStatus.OK
            self._json(status, result)
        except RateLimited as error:
            self._json(HTTPStatus.TOO_MANY_REQUESTS, {"error": str(error)})
        except AIUnavailable as error:
            self._json(HTTPStatus.BAD_GATEWAY, {"error": str(error)})


def create_server(port: int = 4182, database_path: Path | None = None, api_key: str | None = None, ai_transport=None) -> ThreadingHTTPServer:
    database_path = database_path or ROOT / "data" / "companyatlas.sqlite"
    state = AppState(database_path, read_api_key(ROOT) if api_key is None else api_key, ai_transport)
    server = ThreadingHTTPServer(("127.0.0.1", port), AtlasHandler)
    server.state = state
    return server


if __name__ == "__main__":
    server = create_server()
    print("CompanyAtlas: http://127.0.0.1:4182", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
