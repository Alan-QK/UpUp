"""Day 22：文本分类 few-shot Prompt。"""

from __future__ import annotations

import pytest

from few_shot import (
    KIND_COUNTER,
    KIND_POSITIVE,
    SECTION_COUNTER,
    SECTION_LABELS,
    SECTION_OUTPUT_FORMAT,
    SECTION_POSITIVE,
    SECTION_TASK,
    ClassificationPrompt,
    ShotExample,
    build_classification_messages,
    format_label_list,
    format_shot,
    join_sections,
    normalize_kind,
    normalize_text,
    render_examples_block,
    render_system_prompt,
    render_user_prompt,
    validate_classification_prompt,
)


def test_normalize_text() -> None:
    assert normalize_text("  你好\n\n世界  ") == "你好 世界"
    assert normalize_text("a\tb  c") == "a b c"
    assert normalize_text("   ") == ""


def test_normalize_kind() -> None:
    assert normalize_kind(" Positive ") == KIND_POSITIVE
    assert normalize_kind("COUNTER") == KIND_COUNTER
    with pytest.raises(ValueError, match="kind"):
        normalize_kind("negative")
    with pytest.raises(ValueError, match="kind"):
        normalize_kind("  ")


def test_format_label_list() -> None:
    assert format_label_list([]) == ""
    assert format_label_list(["  ", "\n"]) == ""
    assert format_label_list(["bug", " feature ", "bug", "question"]) == (
        "bug / feature / question"
    )


def test_format_shot_with_and_without_note() -> None:
    basic = ShotExample(text="  支付失败  ", label=" bug ")
    assert format_shot(basic, index=1) == (
        "1. 输入：支付失败\n"
        "   标签：bug"
    )

    with_note = ShotExample(
        text="希望支持暗黑模式",
        label="feature",
        kind=KIND_COUNTER,
        note="  这是需求，不是缺陷  ",
    )
    assert format_shot(with_note, index=2) == (
        "2. 输入：希望支持暗黑模式\n"
        "   标签：feature\n"
        "   说明：这是需求，不是缺陷"
    )

    blank_note = ShotExample(text="x", label="bug", note="   ")
    assert format_shot(blank_note, index=3) == (
        "3. 输入：x\n"
        "   标签：bug"
    )


def test_render_examples_block_filters_and_numbers() -> None:
    examples = [
        ShotExample("A", "bug", kind="positive"),
        ShotExample("B", "feature", kind="COUNTER"),
        ShotExample("C", "question", kind="positive"),
        ShotExample("D", "feature", kind="counter"),
    ]
    positive = render_examples_block(examples, kind="positive")
    assert positive == (
        "1. 输入：A\n"
        "   标签：bug\n"
        "2. 输入：C\n"
        "   标签：question"
    )
    counter = render_examples_block(examples, kind="counter")
    assert counter == (
        "1. 输入：B\n"
        "   标签：feature\n"
        "2. 输入：D\n"
        "   标签：feature"
    )
    assert render_examples_block(examples[:1], kind="counter") == ""


def test_join_sections_skips_empty() -> None:
    text = join_sections(
        [
            (SECTION_TASK, "分类"),
            (SECTION_POSITIVE, ""),
            (SECTION_COUNTER, "1. 输入：x\n   标签：feature"),
            ("  ", "幽灵标题应跳过"),
            (SECTION_OUTPUT_FORMAT, "只输出标签"),
        ]
    )
    assert text == (
        "【任务】\n分类\n\n"
        "【反例】\n1. 输入：x\n   标签：feature\n\n"
        "【输出格式】\n只输出标签"
    )


def test_validate_rejects_empty_task_and_format() -> None:
    base = ClassificationPrompt(
        task="工单分类",
        labels=["bug", "feature"],
        examples=[ShotExample("崩溃了", "bug")],
        output_format="只输出标签",
    )
    validate_classification_prompt(base)

    with pytest.raises(ValueError, match="task"):
        validate_classification_prompt(
            ClassificationPrompt(
                task="  ",
                labels=["bug"],
                examples=[ShotExample("x", "bug")],
                output_format="只输出标签",
            )
        )
    with pytest.raises(ValueError, match="output_format"):
        validate_classification_prompt(
            ClassificationPrompt(
                task="分类",
                labels=["bug"],
                examples=[ShotExample("x", "bug")],
                output_format="\n",
            )
        )


def test_validate_labels_and_examples() -> None:
    with pytest.raises(ValueError, match="labels"):
        validate_classification_prompt(
            ClassificationPrompt(
                task="分类",
                labels=[],
                examples=[ShotExample("x", "bug")],
            )
        )
    with pytest.raises(ValueError, match="labels"):
        validate_classification_prompt(
            ClassificationPrompt(
                task="分类",
                labels=["  ", ""],
                examples=[ShotExample("x", "bug")],
            )
        )
    with pytest.raises(ValueError, match="positive"):
        validate_classification_prompt(
            ClassificationPrompt(
                task="分类",
                labels=["bug", "feature"],
                examples=[
                    ShotExample("暗黑模式", "feature", kind="counter"),
                ],
            )
        )
    with pytest.raises(ValueError, match="label"):
        validate_classification_prompt(
            ClassificationPrompt(
                task="分类",
                labels=["bug", "feature"],
                examples=[ShotExample("x", "question")],
            )
        )
    with pytest.raises(ValueError, match="text"):
        validate_classification_prompt(
            ClassificationPrompt(
                task="分类",
                labels=["bug"],
                examples=[ShotExample("  ", "bug")],
            )
        )
    with pytest.raises(ValueError, match="kind"):
        validate_classification_prompt(
            ClassificationPrompt(
                task="分类",
                labels=["bug"],
                examples=[ShotExample("x", "bug", kind="neg")],
            )
        )


def test_render_system_prompt_full() -> None:
    spec = ClassificationPrompt(
        task="  将用户工单分类到指定标签  ",
        labels=["bug", "feature", "question", "bug"],
        examples=[
            ShotExample("支付失败一直转圈", "bug", kind="positive"),
            ShotExample("希望支持导出 CSV", "feature"),
            ShotExample(
                "暗黑模式什么时候有？",
                "feature",
                kind="counter",
                note="需求提问，不是缺陷",
            ),
            ShotExample("怎么重置密码？", "question", kind="positive"),
        ],
        output_format="只输出一个标签：bug / feature / question",
    )
    text = render_system_prompt(spec)
    assert text.startswith("【任务】\n将用户工单分类到指定标签")
    assert "【标签集合】\nbug / feature / question" in text
    assert "【正例】" in text
    assert "1. 输入：支付失败一直转圈\n   标签：bug" in text
    assert "2. 输入：希望支持导出 CSV\n   标签：feature" in text
    assert "3. 输入：怎么重置密码？\n   标签：question" in text
    assert "【反例】" in text
    assert "说明：需求提问，不是缺陷" in text
    assert "【输出格式】\n只输出一个标签：bug / feature / question" in text

    positions = [
        text.index("【任务】"),
        text.index("【标签集合】"),
        text.index("【正例】"),
        text.index("【反例】"),
        text.index("【输出格式】"),
    ]
    assert positions == sorted(positions)


def test_render_system_prompt_omits_empty_counter_section() -> None:
    spec = ClassificationPrompt(
        task="情感分类",
        labels=["pos", "neg"],
        examples=[
            ShotExample("太棒了", "pos"),
            ShotExample("很难用", "neg"),
        ],
        output_format="只输出 pos 或 neg",
    )
    text = render_system_prompt(spec)
    assert "【正例】" in text
    assert "【反例】" not in text


def test_render_user_prompt() -> None:
    assert render_user_prompt("  hello\nworld ") == "【待分类文本】\nhello world"
    assert (
        render_user_prompt("内容", label=" 工单正文 ")
        == "【工单正文】\n内容"
    )
    assert render_user_prompt("内容", label="  ") == "【待分类文本】\n内容"
    with pytest.raises(ValueError, match="user_text"):
        render_user_prompt("   ")


def test_build_classification_messages() -> None:
    spec = ClassificationPrompt(
        task="工单分类",
        labels=["bug", "feature", "question"],
        examples=[
            ShotExample("页面白屏", "bug"),
            ShotExample("想要暗黑模式", "feature", kind="counter", note="是需求"),
        ],
        output_format="只输出标签",
    )
    messages = build_classification_messages(spec, "登录按钮点了没反应")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "【任务】\n工单分类" in messages[0]["content"]
    assert "【反例】" in messages[0]["content"]
    assert messages[1]["content"] == "【待分类文本】\n登录按钮点了没反应"


def test_build_classification_messages_custom_label() -> None:
    spec = ClassificationPrompt(
        task="分类",
        labels=["bug"],
        examples=[ShotExample("崩溃", "bug")],
        output_format="标签",
    )
    messages = build_classification_messages(
        spec, "闪退", user_label="用户反馈"
    )
    assert messages[1]["content"] == "【用户反馈】\n闪退"
