"""Day 17 参考实现：采样参数对比实验。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from chat_client import ChatClient, ChatMessage


_TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


@dataclass(frozen=True)
class SamplingRun:
    """一次固定采样参数下的调用结果。"""

    temperature: float
    top_p: float | None
    content: str
    finish_reason: str | None = None


def validate_temperature(value: float) -> float:
    if not 0.0 <= value <= 2.0:
        raise ValueError("temperature must be in [0, 2]")
    return value


def validate_top_p(value: float) -> float:
    if not 0.0 < value <= 1.0:
        raise ValueError("top_p must be in (0, 1]")
    return value


def tokenize(text: str) -> list[str]:
    return [m.lower() for m in _TOKEN_RE.findall(text)]


def unique_token_ratio(text: str) -> float:
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def jaccard_distance(a: str, b: str) -> float:
    sa = set(tokenize(a))
    sb = set(tokenize(b))
    if not sa and not sb:
        return 0.0
    union = sa | sb
    if not union:
        return 0.0
    return 1.0 - len(sa & sb) / len(union)


def run_temperature_sweep(
    client: ChatClient,
    messages: Sequence[ChatMessage],
    temperatures: Sequence[float],
    *,
    top_p: float | None = None,
) -> list[SamplingRun]:
    validated_temps = [validate_temperature(t) for t in temperatures]
    validated_top_p = validate_top_p(top_p) if top_p is not None else None

    runs: list[SamplingRun] = []
    for t in validated_temps:
        result = client.complete(
            messages,
            temperature=t,
            top_p=validated_top_p,
        )
        runs.append(
            SamplingRun(
                temperature=t,
                top_p=validated_top_p,
                content=result.content,
                finish_reason=result.finish_reason,
            )
        )
    return runs


def format_comparison_report(runs: Sequence[SamplingRun]) -> str:
    lines: list[str] = ["# Temperature Sweep Report"]

    if not runs:
        lines.append("（无采样结果）")
        return "\n".join(lines) + "\n"

    blocks: list[str] = []
    for run in runs:
        preview = run.content.strip()
        if len(preview) > 80:
            preview = preview[:80] + "..."
        top_p_text = "default" if run.top_p is None else str(run.top_p)
        block = "\n".join(
            [
                f"## temperature={run.temperature}",
                f"top_p={top_p_text}",
                f"chars={len(run.content)}",
                f"unique_token_ratio={unique_token_ratio(run.content):.3f}",
                f"preview={preview}",
            ]
        )
        blocks.append(block)

    lines.append("")
    lines.append("\n\n".join(blocks))

    if len(runs) >= 2:
        lines.append("")
        lines.append("## Pairwise Jaccard Distance")
        for i in range(len(runs)):
            for j in range(i + 1, len(runs)):
                dist = jaccard_distance(runs[i].content, runs[j].content)
                lines.append(f"t{i}-t{j}: {dist:.3f}")

    return "\n".join(lines) + "\n"
