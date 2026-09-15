"""Day 21：Prompt 模板函数库。"""

from __future__ import annotations

import pytest

from prompt_builder import (
    SECTION_CONSTRAINTS,
    SECTION_CONTEXT,
    SECTION_OUTPUT_FORMAT,
    SECTION_ROLE,
    SECTION_TASK,
    PromptSpec,
    build_chat_messages,
    format_constraints,
    join_sections,
    normalize_text,
    render_system_prompt,
    render_user_prompt,
    validate_spec,
)


def test_normalize_text() -> None:
    assert normalize_text("  你好\n\n世界  ") == "你好 世界"
    assert normalize_text("a\tb  c") == "a b c"
    assert normalize_text("   ") == ""


def test_format_constraints() -> None:
    assert format_constraints([]) == ""
    assert format_constraints(["  ", "\n"]) == ""
    assert format_constraints(["只用原文", " 简体中文 "]) == (
        "- 只用原文\n- 简体中文"
    )


def test_join_sections_skips_empty_and_orders() -> None:
    text = join_sections(
        [
            (SECTION_ROLE, "编辑"),
            (SECTION_TASK, ""),  # 跳过
            (SECTION_CONSTRAINTS, "- a"),
            ("  ", "幽灵标题应跳过"),
            (SECTION_OUTPUT_FORMAT, "纯文本"),
        ]
    )
    assert text == (
        "【角色】\n编辑\n\n"
        "【约束】\n- a\n\n"
        "【输出格式】\n纯文本"
    )


def test_validate_spec_rejects_empty_required() -> None:
    base = PromptSpec(
        role="编辑",
        task="总结",
        output_format="要点列表",
        constraints=[],
    )
    validate_spec(base)  # ok

    with pytest.raises(ValueError, match="role"):
        validate_spec(
            PromptSpec(role="  ", task="总结", output_format="要点列表")
        )
    with pytest.raises(ValueError, match="task"):
        validate_spec(
            PromptSpec(role="编辑", task="\n", output_format="要点列表")
        )
    with pytest.raises(ValueError, match="output_format"):
        validate_spec(PromptSpec(role="编辑", task="总结", output_format=""))


def test_render_system_prompt_full() -> None:
    spec = PromptSpec(
        role="  你是技术文档编辑  ",
        task="将用户段落压缩为 3 条要点",
        constraints=["只用原文信息", "简体中文"],
        output_format="每行一条：1. ...",
        context="面向初级前端读者",
    )
    text = render_system_prompt(spec)
    assert text.startswith("【角色】\n你是技术文档编辑")
    assert "【任务】\n将用户段落压缩为 3 条要点" in text
    assert "【约束】\n- 只用原文信息\n- 简体中文" in text
    assert "【输出格式】\n每行一条：1. ..." in text
    assert "【上下文】\n面向初级前端读者" in text
    # 顺序：角色 → 任务 → 约束 → 输出格式 → 上下文
    positions = [
        text.index("【角色】"),
        text.index("【任务】"),
        text.index("【约束】"),
        text.index("【输出格式】"),
        text.index("【上下文】"),
    ]
    assert positions == sorted(positions)


def test_render_system_prompt_omits_empty_constraints_and_context() -> None:
    spec = PromptSpec(
        role="助手",
        task="回答问题",
        output_format="一句话",
        constraints=["  ", ""],
        context="   ",
    )
    text = render_system_prompt(spec)
    assert "【约束】" not in text
    assert "【上下文】" not in text
    assert text == (
        "【角色】\n助手\n\n"
        "【任务】\n回答问题\n\n"
        "【输出格式】\n一句话"
    )


def test_render_user_prompt() -> None:
    assert render_user_prompt("  hello\nworld ") == "【用户输入】\nhello world"
    assert (
        render_user_prompt("内容", label=" 待处理文本 ")
        == "【待处理文本】\n内容"
    )
    assert render_user_prompt("内容", label="  ") == "【用户输入】\n内容"
    with pytest.raises(ValueError, match="user_input"):
        render_user_prompt("   ")


def test_build_chat_messages() -> None:
    spec = PromptSpec(
        role="校对员",
        task="找出错别字",
        output_format="JSON 数组",
        constraints=["不要改写原意"],
    )
    messages = build_chat_messages(spec, "他昨天去图收管了")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "【角色】\n校对员" in messages[0]["content"]
    assert messages[1]["content"] == "【用户输入】\n他昨天去图收管了"


def test_build_chat_messages_custom_label() -> None:
    spec = PromptSpec(
        role="助手",
        task="翻译",
        output_format="纯文本",
    )
    messages = build_chat_messages(
        spec, "Hello", user_label="英文原文"
    )
    assert messages[1]["content"] == "【英文原文】\nHello"
