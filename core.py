"""Deterministic data and authorization layer for the fictional company."""

from __future__ import annotations

import csv
import json
import re
import sqlite3
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SAMPLE_ROOT = ROOT / "sample_data"
ROLE_GROUPS = {
    "operations": ("shared", "orders", "operations"),
    "people": ("shared", "people"),
    "leadership": ("shared", "orders", "operations", "people", "leadership"),
}
ROLE_NAMES = {
    "operations": "Provoz a nákup",
    "people": "Péče o lidi",
    "leadership": "Vedení",
}
STOP_WORDS = {"a", "co", "do", "je", "jak", "jaka", "jake", "kdy", "kde", "ma", "na", "od", "pro", "se", "si", "to", "ve", "v", "z", "za", "the", "what", "how", "in", "for", "of"}


def connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database(connection: sqlite3.Connection) -> None:
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            path TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            group_name TEXT NOT NULL,
            kind TEXT NOT NULL,
            description TEXT NOT NULL,
            content TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            placed_date TEXT NOT NULL,
            customer TEXT NOT NULL,
            status TEXT NOT NULL,
            amount_czk INTEGER NOT NULL,
            source_document_id TEXT NOT NULL REFERENCES documents(id),
            source_row INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(placed_date);
        CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer);
        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            role TEXT NOT NULL,
            event TEXT NOT NULL,
            result TEXT NOT NULL
        );
    """)
    if connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]:
        return
    manifest = json.loads((SAMPLE_ROOT / "manifest.json").read_text(encoding="utf-8"))
    with connection:
        for item in manifest:
            source_path = (SAMPLE_ROOT / item["path"]).resolve()
            if not source_path.is_relative_to(SAMPLE_ROOT.resolve()) or not source_path.is_file():
                raise ValueError("Invalid sample document path")
            content = source_path.read_text(encoding="utf-8-sig")
            connection.execute(
                "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?)",
                (item["id"], item["path"], item["title"], item["group"], item["kind"], item["description"], content),
            )
            if item["kind"] == "csv":
                with source_path.open(encoding="utf-8-sig", newline="") as source:
                    reader = csv.DictReader(source)
                    if reader.fieldnames != ["id", "datum", "zakaznik", "status", "castka_czk"]:
                        raise ValueError("Unexpected orders CSV columns")
                    for row_number, row in enumerate(reader, start=2):
                        amount = int(row["castka_czk"])
                        if amount < 0 or row["status"] not in {"dokoncena", "stornovana"}:
                            raise ValueError("Invalid order fixture")
                        connection.execute(
                            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (row["id"], row["datum"], row["zakaznik"], row["status"], amount, item["id"], row_number),
                        )


def allowed_groups(role: str) -> tuple[str, ...]:
    if role not in ROLE_GROUPS:
        raise ValueError("Unknown role")
    return ROLE_GROUPS[role]


def visible_documents(connection: sqlite3.Connection, role: str) -> list[dict]:
    groups = allowed_groups(role)
    placeholders = ",".join("?" for _ in groups)
    rows = connection.execute(
        f"SELECT id, path, title, group_name, kind, description FROM documents WHERE group_name IN ({placeholders}) ORDER BY path",
        groups,
    ).fetchall()
    return [dict(row) for row in rows]


def get_document(connection: sqlite3.Connection, role: str, document_id: str) -> dict | None:
    groups = allowed_groups(role)
    placeholders = ",".join("?" for _ in groups)
    row = connection.execute(
        f"SELECT id, path, title, group_name, kind, description, content FROM documents WHERE id = ? AND group_name IN ({placeholders})",
        (document_id, *groups),
    ).fetchone()
    return dict(row) if row else None


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.lower())
    return "".join(character for character in decomposed if unicodedata.category(character) != "Mn")


def search_documents(connection: sqlite3.Connection, role: str, question: str, limit: int = 3) -> list[dict]:
    tokens = [token for token in re.findall(r"[a-z0-9]{3,}", normalize(question)) if token not in STOP_WORDS]
    if not tokens:
        return []
    candidates = []
    for item in visible_documents(connection, role):
        document = get_document(connection, role, item["id"])
        haystack = normalize(document["title"] + " " + document["description"] + " " + document["content"])
        score = sum(2 if token in normalize(document["title"]) else 1 for token in tokens if token in haystack)
        if score:
            document["score"] = score
            candidates.append(document)
    return sorted(candidates, key=lambda doc: (-doc["score"], doc["path"]))[:limit]


def order_intent(question: str) -> str | None:
    text = normalize(question)
    if "objednav" not in text:
        return None
    if re.search(r"\b(cena|hodnota|castka|staly|stoji|suma|celkova|total|cost)\b", text):
        return "amount"
    if re.search(r"\b(kolik|pocet|spocitat|how many|count)\b", text):
        return "count"
    return None


def is_order_count_question(question: str) -> bool:
    return order_intent(question) == "count"


def _customer_filter(question: str) -> str | None:
    match = re.search(r"\b(?:pro|zakaznika|klienta)\s+([^?.,]+)", normalize(question))
    if not match:
        return None
    candidate = re.sub(r"\s+(?:v|za)\s+roce\s+20\d{2}.*$", "", match.group(1)).strip()
    candidate = re.sub(r"\s+v\s+20\d{2}.*$", "", candidate).strip()
    return candidate or None


def answer_order_count(connection: sqlite3.Connection, role: str, question: str, mode: str = "count") -> dict:
    if "orders" not in allowed_groups(role):
        return {"kind": "denied", "answer": "K této oblasti dat nemáte přístup.", "sources": []}
    year_match = re.search(r"\b20\d{2}\b", question)
    year = year_match.group(0) if year_match else None
    customer_fragment = _customer_filter(question)
    if customer_fragment:
        names = [row[0] for row in connection.execute("SELECT DISTINCT customer FROM orders") if customer_fragment in normalize(row[0])]
        if not names:
            return {"kind": "clarification", "answer": "Zákazníka podle tohoto názvu jsem nenašel. Upřesněte jeho jméno.", "sources": []}
        if len(names) > 1:
            return {"kind": "clarification", "answer": "Název odpovídá více zákazníkům. Kterého máte na mysli?", "options": sorted(names), "sources": []}
        customer = names[0]
    else:
        customer = None
    conditions = []
    parameters: list[str] = []
    if year:
        conditions.append("substr(placed_date, 1, 4) = ?")
        parameters.append(year)
    if customer:
        conditions.append("customer = ?")
        parameters.append(customer)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    rows = [dict(row) for row in connection.execute(
        "SELECT id, placed_date, customer, status, amount_czk, source_document_id, source_row FROM orders" + where + " ORDER BY placed_date, id",
        parameters,
    )]
    aggregate = connection.execute(
        "SELECT COUNT(*) AS total, COALESCE(SUM(status = 'dokoncena'), 0) AS completed, "
        "COALESCE(SUM(status = 'stornovana'), 0) AS cancelled, COALESCE(SUM(amount_czk), 0) AS amount "
        "FROM orders" + where,
        parameters,
    ).fetchone()
    completed = aggregate["completed"]
    cancelled = aggregate["cancelled"]
    amount = aggregate["amount"]
    scope = f"v roce {year}" if year else "ve všech dostupných letech"
    if customer:
        scope += f" pro zákazníka {customer}"
    source_ids = sorted({row["source_document_id"] for row in rows})
    sources = []
    for source_id in source_ids:
        document = get_document(connection, role, source_id)
        sources.append({"id": source_id, "title": document["title"], "rows": [row["source_row"] for row in rows if row["source_document_id"] == source_id]})
    answer = (
        f"Celková hodnota objednávek {scope}: {amount:,} Kč. Započítané záznamy: {aggregate['total']}. Stornované: {cancelled} (evidovaná částka 0 Kč)."
        if mode == "amount" else
        f"Počet objednávek {scope}: {aggregate['total']}. Dokončené: {completed}. Stornované: {cancelled}. Do celkového počtu zahrnuji i stornované objednávky."
    ).replace(",", " ")
    return {
        "kind": "metric",
        "answer": answer,
        "count": aggregate["total"],
        "amountCzk": amount,
        "completed": completed,
        "cancelled": cancelled,
        "scope": {"year": year, "customer": customer},
        "sources": sources,
        "rows": rows,
        "method": "Přesný výběr a součet nad tabulkou orders v SQLite; rok podle data objednávky.",
    }


def answer_question(connection: sqlite3.Connection, role: str, question: str, ai_answer=None) -> dict:
    allowed_groups(role)
    intent = order_intent(question)
    if intent:
        return answer_order_count(connection, role, question, intent)
    documents = search_documents(connection, role, question)
    if not documents:
        return {"kind": "not_found", "answer": "V souborech, ke kterým máte přístup, jsem nenašel podklad pro spolehlivou odpověď.", "sources": []}
    sources = [{"id": doc["id"], "title": doc["title"]} for doc in documents]
    if ai_answer is None:
        return {"kind": "sources", "answer": "Našel jsem související podklady. Pro souhrnnou odpověď je potřeba zapnuté AI.", "sources": sources}
    result = ai_answer(question, documents)
    evidence = result.get("evidence", [])
    by_id = {doc["id"]: doc for doc in documents}
    valid = isinstance(evidence, list) and 0 < len(evidence) <= 5 and all(
        isinstance(item, dict)
        and isinstance(item.get("source_id"), str)
        and isinstance(item.get("quote"), str)
        and 12 <= len(item["quote"]) <= 500
        and item["source_id"] in by_id
        and item["quote"] in by_id[item["source_id"]]["content"]
        for item in evidence
    )
    if not valid or not isinstance(result.get("answer"), str) or not result["answer"].strip():
        return {"kind": "not_found", "answer": "Z nalezených podkladů se nepodařilo sestavit doloženou odpověď.", "sources": sources}
    selected = [{"id": item["source_id"], "title": by_id[item["source_id"]]["title"], "quote": item["quote"]} for item in evidence]
    return {"kind": "document", "answer": result["answer"].strip()[:3000], "sources": selected, "method": "AI shrnula pouze povolené dokumenty. Doslovné citáty systém ověřil proti zdrojům; jejich význam musí zkontrolovat člověk."}


def metrics(connection: sqlite3.Connection, role: str) -> dict:
    documents = visible_documents(connection, role)
    groups = sorted({item["group_name"] for item in documents})
    result = {"documents": len(documents), "groups": groups}
    if "orders" in allowed_groups(role):
        result["orders"] = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    return result


def audit(connection: sqlite3.Connection, role: str, event: str, result: str) -> None:
    with connection:
        connection.execute("INSERT INTO audit(role, event, result) VALUES (?, ?, ?)", (role, event[:30], result[:30]))
