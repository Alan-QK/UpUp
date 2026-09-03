"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_SUFFIXES: tuple[str, ...] = (".txt", ".md", ".markdown")


class DocLoadError(ValueError):
    """文档加载或清洗失败。"""


@dataclass(frozen=True)
class Document:
    source: str
    text: str
    suffix: str
    raw_char_count: int
    char_count: int


def strip_bom(text: str) -> str:
    if text.startswith("\ufeff"):
        return text[1:]
    return text


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def collapse_blank_lines(text: str, *, max_consecutive: int = 2) -> str:
    if max_consecutive < 1:
        raise DocLoadError("max_consecutive")

    lines = [line.rstrip() for line in text.split("\n")]
    out: list[str] = []
    blank_run = 0
    for line in lines:
        if line == "":
            blank_run += 1
            if blank_run <= max_consecutive:
                out.append("")
        else:
            blank_run = 0
            out.append(line)

    joined = "\n".join(out).strip()
    if not joined:
        return ""
    return joined + "\n"


def strip_yaml_frontmatter(text: str) -> str:
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return text

    # Must start with a full-line --- after leading whitespace removal for detection,
    # but we need to remove from the beginning of `stripped`.
    lines = stripped.split("\n")
    if not lines or lines[0].strip() != "---":
        return text

    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            rest = "\n".join(lines[i + 1 :])
            # Preserve whether original had trailing content; join already drops leading fence.
            return rest
    return text


def strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def clean_text(
    text: str,
    *,
    strip_frontmatter: bool = True,
    strip_comments: bool = True,
    max_blank_lines: int = 2,
) -> str:
    out = normalize_newlines(strip_bom(text))
    if strip_frontmatter:
        out = strip_yaml_frontmatter(out)
    if strip_comments:
        out = strip_html_comments(out)
    return collapse_blank_lines(out, max_consecutive=max_blank_lines)


def read_text_file(path: Path) -> str:
    if not path.is_file():
        raise DocLoadError(f"not a file: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise DocLoadError(f"utf-8 decode failed: {path}") from e


def is_supported_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES


def _is_hidden_relative(rel: Path) -> bool:
    return any(part.startswith(".") for part in rel.parts)


def discover_documents(root: Path) -> list[Path]:
    if not root.is_dir():
        raise DocLoadError(f"not a directory: {root}")

    found: list[Path] = []
    for path in root.rglob("*"):
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if _is_hidden_relative(rel):
            continue
        if is_supported_file(path):
            found.append(path.resolve())

    found.sort(key=lambda p: p.relative_to(root.resolve()).as_posix())
    return found


def load_document(path: Path, *, root: Path | None = None) -> Document:
    raw = read_text_file(path)
    text = clean_text(raw)
    suffix = path.suffix.lower()
    if root is not None:
        source = path.relative_to(root).as_posix()
    else:
        source = path.name
    return Document(
        source=source,
        text=text,
        suffix=suffix,
        raw_char_count=len(raw),
        char_count=len(text),
    )


def load_corpus(root: Path) -> list[Document]:
    return [load_document(p, root=root) for p in discover_documents(root)]


def corpus_stats(docs: Sequence[Document]) -> dict[str, object]:
    by_suffix: dict[str, int] = {}
    for doc in docs:
        by_suffix[doc.suffix] = by_suffix.get(doc.suffix, 0) + 1
    ordered_suffix = {k: by_suffix[k] for k in sorted(by_suffix)}
    return {
        "total_docs": len(docs),
        "total_chars": sum(d.char_count for d in docs),
        "total_raw_chars": sum(d.raw_char_count for d in docs),
        "by_suffix": ordered_suffix,
        "sources": [d.source for d in docs],
    }
