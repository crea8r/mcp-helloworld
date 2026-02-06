from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DB_PATH = os.environ.get("DB_PATH", "notes.db")


class ServiceError(Exception):
    def __init__(self, message: str, code: str = "bad_request") -> None:
        super().__init__(message)
        self.code = code


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS note_tags (
            note_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            UNIQUE(note_id, tag_id),
            FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE,
            FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    conn.close()


def _note_row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "content": row["content"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _tags_for_note(conn: sqlite3.Connection, note_id: int) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT t.id, t.name
        FROM tags t
        JOIN note_tags nt ON nt.tag_id = t.id
        WHERE nt.note_id = ?
        ORDER BY t.name ASC
        """,
        (note_id,),
    )
    return [{"id": r["id"], "name": r["name"]} for r in cur.fetchall()]


def create_note(title: str, content: str) -> Dict[str, Any]:
    if not title or not content:
        raise ServiceError("title and content are required")
    conn = _connect()
    cur = conn.cursor()
    now = _utc_now()
    cur.execute(
        """
        INSERT INTO notes (title, content, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (title, content, now, now),
    )
    note_id = cur.lastrowid
    conn.commit()
    cur.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    note = _note_row_to_dict(cur.fetchone())
    note["tags"] = []
    conn.close()
    return note


def list_notes() -> List[Dict[str, Any]]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notes ORDER BY updated_at DESC")
    rows = cur.fetchall()
    result = []
    for row in rows:
        note = _note_row_to_dict(row)
        note["tags"] = _tags_for_note(conn, note["id"])
        result.append(note)
    conn.close()
    return result


def get_note(note_id: int) -> Dict[str, Any]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ServiceError("Note not found", code="not_found")
    note = _note_row_to_dict(row)
    note["tags"] = _tags_for_note(conn, note_id)
    conn.close()
    return note


def update_note(note_id: int, title: Optional[str] = None, content: Optional[str] = None) -> Dict[str, Any]:
    if title is None and content is None:
        raise ServiceError("No fields to update")
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ServiceError("Note not found", code="not_found")
    new_title = title if title is not None else row["title"]
    new_content = content if content is not None else row["content"]
    now = _utc_now()
    cur.execute(
        """
        UPDATE notes
        SET title = ?, content = ?, updated_at = ?
        WHERE id = ?
        """,
        (new_title, new_content, now, note_id),
    )
    conn.commit()
    cur.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    note = _note_row_to_dict(cur.fetchone())
    note["tags"] = _tags_for_note(conn, note_id)
    conn.close()
    return note


def delete_note(note_id: int) -> Dict[str, Any]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT id FROM notes WHERE id = ?", (note_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ServiceError("Note not found", code="not_found")
    cur.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted", "id": note_id}


def create_tag(name: str) -> Dict[str, Any]:
    if not name:
        raise ServiceError("name is required")
    conn = _connect()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO tags (name) VALUES (?)", (name,))
        tag_id = cur.lastrowid
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.close()
        raise ServiceError("Tag already exists", code="conflict") from exc
    conn.close()
    return {"id": tag_id, "name": name}


def list_tags() -> List[Dict[str, Any]]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM tags ORDER BY name ASC")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r["id"], "name": r["name"]} for r in rows]


def attach_tags(note_id: int, tag_ids: List[int]) -> Dict[str, Any]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT id FROM notes WHERE id = ?", (note_id,))
    if not cur.fetchone():
        conn.close()
        raise ServiceError("Note not found", code="not_found")
    for tag_id in tag_ids:
        cur.execute("SELECT id FROM tags WHERE id = ?", (tag_id,))
        if not cur.fetchone():
            conn.close()
            raise ServiceError(f"Tag not found: {tag_id}", code="not_found")
        cur.execute(
            "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)",
            (note_id, tag_id),
        )
    conn.commit()
    tags = _tags_for_note(conn, note_id)
    conn.close()
    return {"note_id": note_id, "tags": tags}


def attach_tags_by_name(note_id: int, names: List[str]) -> Dict[str, Any]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT id FROM notes WHERE id = ?", (note_id,))
    if not cur.fetchone():
        conn.close()
        raise ServiceError("Note not found", code="not_found")
    tag_ids: List[int] = []
    for name in names:
        cur.execute("SELECT id FROM tags WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            tag_ids.append(row["id"])
        else:
            cur.execute("INSERT INTO tags (name) VALUES (?)", (name,))
            tag_ids.append(cur.lastrowid)
    for tag_id in tag_ids:
        cur.execute(
            "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)",
            (note_id, tag_id),
        )
    conn.commit()
    tags = _tags_for_note(conn, note_id)
    conn.close()
    return {"note_id": note_id, "tags": tags}


def detach_tag(note_id: int, tag_id: int) -> Dict[str, Any]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM note_tags WHERE note_id = ? AND tag_id = ?", (note_id, tag_id))
    conn.commit()
    tags = _tags_for_note(conn, note_id)
    conn.close()
    return {"note_id": note_id, "tags": tags}


def _tokenize(query: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z0-9]+", query.lower())
    return [t for t in tokens if t]


def _sentence_split(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _sentence_score(sentence: str, tokens: List[str]) -> int:
    score = 0
    for token in tokens:
        if re.search(rf"\b{re.escape(token)}\b", sentence, flags=re.IGNORECASE):
            score += 1
    return score


def search_notes(query: str) -> Dict[str, Any]:
    tokens = _tokenize(query)
    if not tokens:
        raise ServiceError("Query has no searchable tokens")
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notes")
    notes = cur.fetchall()

    results = []
    for row in notes:
        content = row["content"]
        sentences = _sentence_split(content)
        scored_sentences = []
        note_score = 0
        for sentence in sentences:
            s_score = _sentence_score(sentence, tokens)
            if s_score > 0:
                scored_sentences.append({"sentence": sentence, "score": s_score})
                note_score += s_score
        if note_score > 0:
            scored_sentences.sort(key=lambda x: x["score"], reverse=True)
            note = _note_row_to_dict(row)
            note["tags"] = _tags_for_note(conn, note["id"])
            results.append(
                {
                    "note": note,
                    "score": note_score,
                    "top_sentences": scored_sentences[:5],
                }
            )

    results.sort(key=lambda x: x["score"], reverse=True)
    conn.close()
    return {"query": query, "tokens": tokens, "results": results}


init_db()
