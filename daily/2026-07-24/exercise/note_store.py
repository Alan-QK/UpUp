"""Day 5 练习：本地笔记存储（JSON 持久化）。

请完成 TODO，使 tests/ 全部通过。
"""

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
    """一条笔记。"""

    id: int
    title: str
    body: str
    created_at: str  # ISO-8601 字符串


def _utc_now_iso() -> str:
    """返回当前 UTC 时间的 ISO 字符串（带时区）。"""
    return datetime.now(timezone.utc).isoformat()


class NoteStore:
    """基于单个 JSON 文件的笔记仓库。

    文件结构：
    {
      "next_id": 1,
      "notes": [ { "id", "title", "body", "created_at" }, ... ]
    }
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def _load_raw(self) -> dict[str, Any]:
        """读取 JSON；文件不存在时返回空库。

        空库形态：{"next_id": 1, "notes": []}
        """
        # TODO: 实现这里（提示：json + Path.read_text）
        raise NotImplementedError

    def _save_raw(self, data: dict[str, Any]) -> None:
        """写入 JSON（UTF-8，ensure_ascii=False，indent=2，末尾换行）。父目录不存在则创建。"""
        # TODO: 实现这里
        raise NotImplementedError

    def add(self, title: str, body: str) -> Note:
        """新增笔记。

        规则：
        - title / body 先 strip
        - title 去空白后不能为空 → ValueError("title must not be empty")
        - id 使用 next_id，然后 next_id += 1
        - created_at 使用 _utc_now_iso()
        - 立刻持久化
        - 序列化可用 asdict(note)
        """
        # TODO: 实现这里
        raise NotImplementedError

    def list_notes(self) -> list[Note]:
        """按 id 升序返回全部笔记。"""
        # TODO: 实现这里
        raise NotImplementedError

    def get(self, note_id: int) -> Note:
        """按 id 获取；不存在 → NoteNotFoundError。"""
        # TODO: 实现这里
        raise NotImplementedError

    def delete(self, note_id: int) -> None:
        """按 id 删除；不存在 → NoteNotFoundError；成功则持久化。"""
        # TODO: 实现这里
        raise NotImplementedError

    def search(self, query: str) -> list[Note]:
        """在 title/body 中做大小写不敏感的子串匹配，按 id 升序返回。

        - query strip 后为空 → 返回 []
        """
        # TODO: 实现这里
        raise NotImplementedError
