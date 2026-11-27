"""轨迹日志：每步 thought / action / observation 可回放。

本文件在练习中已给齐，今日勿改。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TraceStep:
    """Loop 中的一步（一次模型调用 + 可选工具观察）。"""

    index: int
    kind: str  # "action" | "final"
    thought: str
    tool_names: tuple[str, ...]
    observations: tuple[str, ...]


def format_trace_markdown(goal: str, steps: tuple[TraceStep, ...], *, final: str, reason: str) -> str:
    """渲染可回放的 Markdown 轨迹。"""
    lines = [
        "# Tool-Agent Trace",
        "",
        f"- **goal**: {goal}",
        f"- **stopped_reason**: {reason}",
        f"- **steps**: {len(steps)}",
        "",
    ]
    for step in steps:
        lines.append(f"## Step {step.index} · {step.kind}")
        lines.append("")
        if step.thought:
            lines.append(f"- thought: {step.thought}")
        if step.tool_names:
            lines.append(f"- tools: {', '.join(step.tool_names)}")
        for obs in step.observations:
            lines.append(f"- observation: {obs}")
        lines.append("")
    lines.append("## Final")
    lines.append("")
    lines.append(final)
    lines.append("")
    return "\n".join(lines)


def extract_tool_names(assistant: dict[str, Any]) -> tuple[str, ...]:
    raw = assistant.get("tool_calls")
    if not isinstance(raw, list):
        return ()
    names: list[str] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        fn = item.get("function")
        if isinstance(fn, dict) and isinstance(fn.get("name"), str):
            names.append(fn["name"])
    return tuple(names)
