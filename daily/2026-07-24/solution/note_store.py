"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class NoteNotFoundError(LookupError):
    """指定 id 的笔记不存在。"""


@dataclass(frozen=True)
class Note:
    id: int
    title: str
    body: str
    created_at: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class NoteStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _empty(self) -> dict[str, Any]:
        return {"next_id": 1, "notes": []}

    def _load_raw(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return self._empty()
        notes = data.get("notes")
        next_id = data.get("next_id")
        if not isinstance(notes, list) or not isinstance(next_id, int):
            return self._empty()
        return {"next_id": next_id, "notes": notes}

    def _save_raw(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        self.path.write_text(text, encoding="utf-8")

    def _notes_from_raw(self, data: dict[str, Any]) -> list[Note]:
        result: list[Note] = []
        for item in data["notes"]:
            result.append(
                Note(
                    id=int(item["id"]),
                    title=str(item["title"]),
                    body=str(item["body"]),
                    created_at=str(item["created_at"]),
                )
            )
        result.sort(key=lambda n: n.id)
        return result

    def add(self, title: str, body: str) -> Note:
        cleaned_title = title.strip()
        cleaned_body = body.strip()
        if not cleaned_title:
            raise ValueError("title must not be empty")

        data = self._load_raw()
        note = Note(
            id=int(data["next_id"]),
            title=cleaned_title,
            body=cleaned_body,
            created_at=_utc_now_iso(),
        )
        data["notes"].append(asdict(note))
        data["next_id"] = int(data["next_id"]) + 1
        self._save_raw(data)
        return note

    def list_notes(self) -> list[Note]:
        return self._notes_from_raw(self._load_raw())

    def get(self, note_id: int) -> Note:
        for note in self.list_notes():
            if note.id == note_id:
                return note
        raise NoteNotFoundError(note_id)

    def delete(self, note_id: int) -> None:
        data = self._load_raw()
        before = len(data["notes"])
        data["notes"] = [item for item in data["notes"] if int(item["id"]) != note_id]
        if len(data["notes"]) == before:
            raise NoteNotFoundError(note_id)
        self._save_raw(data)

    def search(self, query: str) -> list[Note]:
        needle = query.strip().lower()
        if not needle:
            return []
        hits: list[Note] = []
        for note in self.list_notes():
            hay = f"{note.title}\n{note.body}".lower()
            if needle in hay:
                hits.append(note)
        return hits
