"""Day 50：只读文件助手（权限边界）。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from file_assistant import (
    ERROR_PREFIX,
    FILE_TOOL_NAMES,
    STOP_FINAL,
    STOP_MAX_STEPS,
    AssistantResult,
    SandboxPolicy,
    ScriptedChat,
    assistant_thought,
    default_system_prompt,
    execute_file_tools,
    file_toolkit,
    has_tool_calls,
    list_directory,
    normalize_text,
    parse_arguments,
    read_text_file,
    resolve_sandbox_path,
    run_readonly_assistant,
    validate_sandbox_policy,
)


def _tool(call_id: str, name: str, arguments: dict | str, content: str | None = "") -> dict:
    if isinstance(arguments, dict):
        args_text = json.dumps(arguments, ensure_ascii=False)
    else:
        args_text = arguments
    return {
        "role": "assistant",
        "content": content,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": args_text},
            }
        ],
    }


def _final(content: str) -> dict:
    return {"role": "assistant", "content": content}


@pytest.fixture()
def sandbox(tmp_path: Path) -> Path:
    root = tmp_path / "ws"
    (root / "docs").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "README.md").write_text("hello sandbox\nline2\n", encoding="utf-8")
    (root / "docs" / "notes.md").write_text("# notes\npermission boundary\n", encoding="utf-8")
    (root / "docs" / "secret.env").write_text("SECRET=demo\n", encoding="utf-8")
    (root / "src" / "hello.py").write_text('print("hi")\n', encoding="utf-8")
    # 沙箱外的诱饵文件（越界读取应失败）
    (tmp_path / "outside.txt").write_text("outside-secret\n", encoding="utf-8")
    return root


def test_toolkit_and_prompt() -> None:
    names = [item["function"]["name"] for item in file_toolkit()]
    assert names == list(FILE_TOOL_NAMES)
    prompt = default_system_prompt()
    assert "list_directory" in prompt
    assert "read_file" in prompt
    assert "只读" in prompt or "不能写入" in prompt


def test_validate_sandbox_policy(sandbox: Path) -> None:
    ok = validate_sandbox_policy(SandboxPolicy(root=sandbox))
    assert ok.root == sandbox.resolve()
    assert ok.max_read_bytes == 4096

    with pytest.raises(TypeError):
        validate_sandbox_policy("bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="directory"):
        validate_sandbox_policy(SandboxPolicy(root=sandbox / "missing"))
    with pytest.raises(TypeError):
        validate_sandbox_policy(SandboxPolicy(root=sandbox, max_steps=True))  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        validate_sandbox_policy(SandboxPolicy(root=sandbox, max_read_bytes=0))


def test_normalize_and_helpers() -> None:
    assert normalize_text("  a\n b\t c  ") == "a b c"
    assert has_tool_calls(_tool("1", "list_directory", {})) is True
    assert has_tool_calls(_final("done")) is False
    assert has_tool_calls("x") is False  # type: ignore[arg-type]
    assert assistant_thought(_final("  hi\nthere ")) == "hi there"
    assert assistant_thought({"role": "assistant", "content": None}) == ""


def test_parse_arguments() -> None:
    assert parse_arguments(None) == {}
    assert parse_arguments("   ") == {}
    assert parse_arguments({"path": "docs"}) == {"path": "docs"}
    assert parse_arguments('{"path":"README.md"}') == {"path": "README.md"}
    with pytest.raises(ValueError, match="valid JSON"):
        parse_arguments("{bad")
    with pytest.raises(ValueError, match="object"):
        parse_arguments("[1]")
    with pytest.raises(ValueError, match="str or dict"):
        parse_arguments(3)  # type: ignore[arg-type]


def test_resolve_sandbox_path_allows_inside(sandbox: Path) -> None:
    assert resolve_sandbox_path(sandbox, ".") == sandbox.resolve()
    assert resolve_sandbox_path(sandbox, "README.md") == (sandbox / "README.md").resolve()
    assert resolve_sandbox_path(sandbox, "docs/notes.md") == (
        sandbox / "docs" / "notes.md"
    ).resolve()
    # 绝对路径但仍在 root 内
    abs_inside = str((sandbox / "src").resolve())
    assert resolve_sandbox_path(sandbox, abs_inside) == (sandbox / "src").resolve()


def test_resolve_sandbox_path_blocks_escape(sandbox: Path, tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="escapes sandbox"):
        resolve_sandbox_path(sandbox, "../outside.txt")
    with pytest.raises(PermissionError, match="escapes sandbox"):
        resolve_sandbox_path(sandbox, str(tmp_path / "outside.txt"))
    with pytest.raises(PermissionError, match="escapes sandbox"):
        resolve_sandbox_path(sandbox, "docs/../../outside.txt")
    with pytest.raises(ValueError):
        resolve_sandbox_path(sandbox, "  ")
    with pytest.raises(ValueError):
        resolve_sandbox_path(sandbox, "a\x00b")
    with pytest.raises(TypeError):
        resolve_sandbox_path(sandbox, None)  # type: ignore[arg-type]


def test_list_directory(sandbox: Path) -> None:
    policy = SandboxPolicy(root=sandbox)
    root_listing = list_directory(policy, ".")
    assert root_listing["path"] == "."
    names = [e["name"] for e in root_listing["entries"]]
    assert names == sorted(names)
    assert set(names) >= {"README.md", "docs", "src"}
    types = {e["name"]: e["type"] for e in root_listing["entries"]}
    assert types["docs"] == "dir"
    assert types["README.md"] == "file"

    docs = list_directory(policy, "docs")
    assert docs["path"] == "docs"
    doc_names = {e["name"] for e in docs["entries"]}
    assert "notes.md" in doc_names
    assert "secret.env" in doc_names

    tiny = SandboxPolicy(root=sandbox, max_list_entries=1)
    truncated = list_directory(tiny, ".")
    assert len(truncated["entries"]) == 1
    assert truncated.get("truncated") is True

    with pytest.raises(ValueError, match="not a directory"):
        list_directory(policy, "README.md")
    with pytest.raises(PermissionError):
        list_directory(policy, "..")


def test_read_text_file(sandbox: Path) -> None:
    policy = SandboxPolicy(root=sandbox, max_read_bytes=11)
    result = read_text_file(policy, "README.md")
    assert result["path"] == "README.md"
    assert result["content"] == "hello sandb"
    assert result["truncated"] is True
    assert result["bytes_read"] == 11

    full = read_text_file(SandboxPolicy(root=sandbox), "docs/notes.md")
    assert "permission boundary" in full["content"]
    assert full["truncated"] is False

    with pytest.raises(ValueError, match="not a file"):
        read_text_file(SandboxPolicy(root=sandbox), "docs")
    with pytest.raises(PermissionError):
        read_text_file(SandboxPolicy(root=sandbox), "../outside.txt")


def test_execute_file_tools_success_and_errors(sandbox: Path) -> None:
    policy = SandboxPolicy(root=sandbox)
    ok_msgs = execute_file_tools(
        _tool("c1", "list_directory", {"path": "docs"}, "列一下"),
        policy,
    )
    assert len(ok_msgs) == 1
    assert ok_msgs[0]["role"] == "tool"
    assert ok_msgs[0]["tool_call_id"] == "c1"
    payload = json.loads(ok_msgs[0]["content"])
    assert payload["path"] == "docs"

    escape = execute_file_tools(
        _tool("c2", "read_file", {"path": "../outside.txt"}),
        policy,
    )
    assert escape[0]["content"].startswith(ERROR_PREFIX)
    assert "PermissionError" in escape[0]["content"]

    unknown = execute_file_tools(
        _tool("c3", "write_file", {"path": "x"}),
        policy,
    )
    assert "Unknown tool" in unknown[0]["content"]

    missing = execute_file_tools(
        _tool("c4", "read_file", {}),
        policy,
    )
    assert "missing required argument" in missing[0]["content"]


def test_run_readonly_assistant_happy_path(sandbox: Path) -> None:
    policy = SandboxPolicy(root=sandbox, max_steps=4)
    chat = ScriptedChat(
        [
            _tool("1", "list_directory", {"path": "."}, "先看根目录"),
            _tool("2", "read_file", {"path": "docs/notes.md"}, "读笔记"),
            _final("笔记里提到了 permission boundary。"),
        ]
    )
    result = run_readonly_assistant("notes 里写了什么？", chat, policy)
    assert isinstance(result, AssistantResult)
    assert result.stopped_reason == STOP_FINAL
    assert "permission boundary" in result.final_content
    assert result.tool_names_used == ("list_directory", "read_file")
    assert result.steps == 3
    # 工具结果已回填
    tool_contents = [
        m["content"] for m in result.messages if m.get("role") == "tool"
    ]
    assert any("notes.md" in c or "permission" in c for c in tool_contents)


def test_run_readonly_assistant_blocks_escape_then_recovers(sandbox: Path) -> None:
    policy = SandboxPolicy(root=sandbox, max_steps=4)
    chat = ScriptedChat(
        [
            _tool("1", "read_file", {"path": "../outside.txt"}, "尝试越界"),
            _tool("2", "read_file", {"path": "README.md"}, "改读沙箱内"),
            _final("README 开头是 hello sandbox。"),
        ]
    )
    result = run_readonly_assistant("读一下说明", chat, policy)
    assert result.stopped_reason == STOP_FINAL
    assert result.tool_names_used == ("read_file", "read_file")
    first_tool = next(m for m in result.messages if m.get("role") == "tool")
    assert first_tool["content"].startswith(ERROR_PREFIX)
    assert "hello sandbox" in result.final_content


def test_run_readonly_assistant_max_steps(sandbox: Path) -> None:
    policy = SandboxPolicy(root=sandbox, max_steps=2)
    chat = ScriptedChat(
        [
            _tool("1", "list_directory", {"path": "."}),
            _tool("2", "list_directory", {"path": "docs"}),
            _final("不应走到这里"),
        ]
    )
    result = run_readonly_assistant("摸清结构", chat, policy)
    assert result.stopped_reason == STOP_MAX_STEPS
    assert result.steps == 2
    assert len(chat._responses) == 1  # 第三条未消费


def test_run_readonly_assistant_rejects_empty_goal(sandbox: Path) -> None:
    with pytest.raises(ValueError, match="goal"):
        run_readonly_assistant("  ", ScriptedChat([]), SandboxPolicy(root=sandbox))
