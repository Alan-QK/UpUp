"""Agent 常用的纯文本工具函数（今日实现已给齐，请专注写测试）。"""

from __future__ import annotations

import re


def normalize_whitespace(text: str) -> str:
    """把连续空白（空格/制表/换行）折叠为单个空格，并去掉首尾空白。"""
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, max_chars: int, ellipsis: str = "...") -> str:
    """按字符数截断文本；超出时追加 ellipsis（计入总长度）。

    - max_chars < 1 时抛 ValueError
    - 若 ellipsis 长度 >= max_chars，则只返回 ellipsis 的前 max_chars 个字符
    """
    if max_chars < 1:
        raise ValueError("max_chars must be >= 1")
    if len(text) <= max_chars:
        return text
    if len(ellipsis) >= max_chars:
        return ellipsis[:max_chars]
    keep = max_chars - len(ellipsis)
    return text[:keep] + ellipsis


def extract_tagged_block(text: str, tag: str) -> str | None:
    """从文本中提取第一个 <tag>...</tag> 内的内容（不含标签本身）。

    - tag 不能为空或含空白
    - 找不到则返回 None
    - 匹配非贪婪，且忽略大小写标签名
    """
    cleaned = tag.strip()
    if not cleaned or re.search(r"\s", cleaned):
        raise ValueError("tag must be a non-empty token without whitespace")
    pattern = rf"<{re.escape(cleaned)}>(.*?)</{re.escape(cleaned)}>"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if match is None:
        return None
    return match.group(1)
