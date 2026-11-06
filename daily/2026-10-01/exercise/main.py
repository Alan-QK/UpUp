"""Day 50 手工运行入口：只读文件助手 Demo。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from file_assistant import (
    SandboxPolicy,
    ScriptedChat,
    file_toolkit,
    run_readonly_assistant,
)


def _tool(call_id: str, name: str, arguments: dict, thought: str = "") -> dict:
    return {
        "role": "assistant",
        "content": thought or f"调用 {name}",
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(arguments, ensure_ascii=False),
                },
            }
        ],
    }


def _final(text: str) -> dict:
    return {"role": "assistant", "content": text}


def sample_root() -> Path:
    return (Path(__file__).resolve().parent / "sample_workspace").resolve()


def build_demo_chat() -> ScriptedChat:
    """list → read → final。"""
    return ScriptedChat(
        [
            _tool("c1", "list_directory", {"path": "."}, "先看工作区根目录"),
            _tool("c2", "read_file", {"path": "docs/notes.md"}, "再读 docs/notes.md"),
            _final("工作区含 docs/ 与 src/；notes.md 强调权限边界：只能 list/read。"),
        ]
    )


def build_escape_chat() -> ScriptedChat:
    """越界失败 → 纠正读取。"""
    return ScriptedChat(
        [
            _tool(
                "c1",
                "read_file",
                {"path": "../outside.txt"},
                "错误尝试读沙箱外",
            ),
            _tool("c2", "read_file", {"path": "README.md"}, "改为读 README"),
            _final("越界被拒绝；README 显示这是 UpUp Day50 sandbox。"),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 50 只读文件助手 Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="list + read 正常路径",
    )
    parser.add_argument(
        "--escape",
        action="store_true",
        help="演示越界拒绝后纠正",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="沙箱根目录（默认 sample_workspace）",
    )
    args = parser.parse_args()

    root = (args.root or sample_root()).resolve()
    policy = SandboxPolicy(root=root, max_steps=6)
    mode = "escape" if args.escape else "demo"
    chat = build_escape_chat() if mode == "escape" else build_demo_chat()
    goal = (
        "尝试读取沙箱外文件，失败后改读 README"
        if mode == "escape"
        else "摸清工作区并总结 notes.md 要点"
    )

    print("tools:", [t["function"]["name"] for t in file_toolkit()])
    print("sandbox:", policy.root)
    print("goal:", goal)
    print("---")

    result = run_readonly_assistant(goal, chat, policy)
    print("stopped:", result.stopped_reason)
    print("steps:", result.steps)
    print("tools_used:", result.tool_names_used)
    print("final:", result.final_content)
    print("--- messages ---")
    for msg in result.messages:
        role = msg.get("role")
        if role == "tool":
            content = str(msg.get("content") or "")
            preview = content if len(content) < 160 else content[:157] + "..."
            print(f"[tool {msg.get('tool_call_id')}] {preview}")
        elif role == "assistant":
            if msg.get("tool_calls"):
                names = [
                    c.get("function", {}).get("name") for c in msg["tool_calls"]
                ]
                print(f"[assistant/tool_calls] {names} | {msg.get('content')}")
            else:
                print(f"[assistant/final] {msg.get('content')}")
        else:
            print(f"[{role}] {str(msg.get('content') or '')[:120]}")


if __name__ == "__main__":
    main()
