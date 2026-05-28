from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.requests import Request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data.db"


class IngestItem(BaseModel):
    source: str = Field(..., examples=["email", "document", "finance", "chat", "calendar"])
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    event_date: date | None = None


class QueryRequest(BaseModel):
    question: str


@dataclass
class StoredItem:
    id: int
    source: str
    title: str
    content: str
    tags: list[str]
    event_date: str | None
    created_at: str


def get_fernet() -> Fernet:
    key = os.getenv("APP_SECRET_KEY")
    if not key:
        raise RuntimeError("APP_SECRET_KEY is required")
    return Fernet(key.encode() if isinstance(key, str) else key)


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                encrypted_content BLOB NOT NULL,
                tags TEXT NOT NULL,
                event_date TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def encrypt_text(text: str) -> bytes:
    return get_fernet().encrypt(text.encode("utf-8"))


def decrypt_text(blob: bytes) -> str:
    return get_fernet().decrypt(blob).decode("utf-8")


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))


def score_match(question: str, item: StoredItem) -> int:
    q_tokens = tokenize(question)
    corpus = f"{item.title} {item.content} {' '.join(item.tags)} {item.source}".lower()
    i_tokens = tokenize(corpus)
    return len(q_tokens & i_tokens)


def fetch_all_records() -> list[StoredItem]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, source, title, encrypted_content, tags, event_date, created_at FROM records ORDER BY created_at DESC"
        ).fetchall()

    items: list[StoredItem] = []
    for row in rows:
        content = decrypt_text(row[3])
        tags = [t.strip() for t in row[4].split(",") if t.strip()]
        items.append(
            StoredItem(
                id=row[0],
                source=row[1],
                title=row[2],
                content=content,
                tags=tags,
                event_date=row[5],
                created_at=row[6],
            )
        )
    return items


def detect_alerts(items: list[StoredItem]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    today = date.today()

    for item in items:
        haystack = f"{item.title} {item.content}".lower()

        if item.event_date:
            dt = date.fromisoformat(item.event_date)
            days = (dt - today).days
            if 0 <= days <= 14:
                alerts.append(
                    {
                        "type": "due_soon",
                        "severity": "high" if days <= 3 else "medium",
                        "title": f"Due in {days} day(s): {item.title}",
                        "source": item.source,
                    }
                )

        if "renew" in haystack or "expires" in haystack or "expiration" in haystack:
            alerts.append(
                {
                    "type": "renewal",
                    "severity": "medium",
                    "title": f"Renewal/expiry mention: {item.title}",
                    "source": item.source,
                }
            )

        if any(word in haystack for word in ["monthly", "subscription", "auto-debit", "autopay"]):
            alerts.append(
                {
                    "type": "subscription",
                    "severity": "low",
                    "title": f"Possible recurring payment: {item.title}",
                    "source": item.source,
                }
            )

        if any(word in haystack for word in ["submit", "upload", "required", "missing"]):
            alerts.append(
                {
                    "type": "missing_doc",
                    "severity": "medium",
                    "title": f"Possible pending submission: {item.title}",
                    "source": item.source,
                }
            )

    return alerts[:50]


app = FastAPI(title="Personal AI Ops Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/ingest")
def ingest(item: IngestItem) -> dict[str, Any]:
    encrypted = encrypt_text(item.content)
    now = datetime.utcnow().isoformat()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO records(source, title, encrypted_content, tags, event_date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (item.source, item.title, encrypted, ",".join(item.tags), item.event_date.isoformat() if item.event_date else None, now),
        )
        conn.commit()

    return {"ok": True, "message": "Record stored securely."}


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    items = fetch_all_records()
    alerts = detect_alerts(items)

    return {
        "counts": {
            "records": len(items),
            "urgent": len([a for a in alerts if a["severity"] == "high"]),
            "upcoming": len([a for a in alerts if a["severity"] == "medium"]),
        },
        "alerts": alerts,
        "recent": [
            {"id": i.id, "title": i.title, "source": i.source, "created_at": i.created_at, "tags": i.tags}
            for i in items[:10]
        ],
    }


@app.post("/api/query")
def query(payload: QueryRequest) -> dict[str, Any]:
    items = fetch_all_records()
    if not items:
        raise HTTPException(status_code=404, detail="No records found. Ingest data first.")

    ranked = sorted(items, key=lambda i: score_match(payload.question, i), reverse=True)
    top = [i for i in ranked[:5] if score_match(payload.question, i) > 0]

    return {
        "question": payload.question,
        "answers": [
            {
                "title": i.title,
                "source": i.source,
                "event_date": i.event_date,
                "tags": i.tags,
                "snippet": (i.content[:250] + "...") if len(i.content) > 250 else i.content,
            }
            for i in top
        ],
        "hint": "For production, replace keyword matching with embeddings + LLM reasoning.",
    }
