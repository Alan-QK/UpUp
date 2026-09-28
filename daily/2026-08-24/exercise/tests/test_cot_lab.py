"""Day 23：CoT 与直接回答对比。"""

from __future__ import annotations

import pytest

from cot_lab import (
    ANSWER_MARKER,
    COT_SYSTEM,
    DIRECT_SYSTEM,
    STRATEGY_COT,
    STRATEGY_DIRECT,
    CompareReport,
    ReasoningTask,
    build_messages,
    build_system_prompt,
    build_user_prompt,
    compare_outputs,
    count_reasoning_steps,
    evaluate_run,
    extract_final_answer,
    normalize_answer,
    normalize_strategy,
    normalize_text,
    render_report,
)


def test_normalize_text() -> None:
    assert normalize_text("  你好\n\n世界  ") == "你好 世界"
    assert normalize_text("a\tb  c") == "a b c"
    assert normalize_text("   ") == ""


def test_normalize_strategy() -> None:
    assert normalize_strategy(" Direct ") == STRATEGY_DIRECT
    assert normalize_strategy("COT") == STRATEGY_COT
    with pytest.raises(ValueError, match="strategy"):
        normalize_strategy("react")
    with pytest.raises(ValueError, match="strategy"):
        normalize_strategy("  ")


def test_normalize_answer() -> None:
    assert normalize_answer("  Six\n") == "six"
    assert normalize_answer("6") == "6"


def test_build_system_prompt() -> None:
    assert build_system_prompt("direct") == DIRECT_SYSTEM
    assert build_system_prompt("COT") == COT_SYSTEM
    assert ANSWER_MARKER in build_system_prompt("direct")
    assert ANSWER_MARKER in build_system_prompt("cot")


def test_build_user_prompt() -> None:
    assert build_user_prompt("  还剩几个？ ") == "【题目】\n还剩几个？"
    with pytest.raises(ValueError, match="question"):
        build_user_prompt("   \n")


def test_build_messages() -> None:
    messages = build_messages("direct", "1+1=?")
    assert len(messages) == 2
    assert messages[0] == {"role": "system", "content": DIRECT_SYSTEM}
    assert messages[1]["role"] == "user"
    assert "1+1=?" in messages[1]["content"]

    cot_messages = build_messages("cot", "1+1=?")
    assert cot_messages[0]["content"] == COT_SYSTEM


def test_extract_final_answer_last_marker_wins() -> None:
    text = (
        f"中间误写 {ANSWER_MARKER}99\n"
        "1. 重新计算\n"
        f"{ANSWER_MARKER}42\n"
        "谢谢"
    )
    assert extract_final_answer(text) == "42"


def test_extract_final_answer_errors() -> None:
    with pytest.raises(ValueError, match="empty"):
        extract_final_answer("   ")
    with pytest.raises(ValueError, match="最终答案"):
        extract_final_answer("没有锚点的一段话")
    with pytest.raises(ValueError, match="最终答案"):
        extract_final_answer(f"{ANSWER_MARKER}   ")


def test_count_reasoning_steps() -> None:
    text = (
        "1. 第一步\n"
        "2. 第二步\n"
        "随便一句\n"
        "3、第三步也算\n"
        f"{ANSWER_MARKER}6\n"
        "4. 答案后的步骤不算"
    )
    assert count_reasoning_steps(text) == 3
    assert count_reasoning_steps("最终答案：1") == 0
    assert count_reasoning_steps("1. only\n2. steps") == 2


def test_evaluate_run_correct_and_steps() -> None:
    raw = "1. a\n2. b\n最终答案：6"
    result = evaluate_run("cot", raw, "6")
    assert result.strategy == STRATEGY_COT
    assert result.extracted_answer == "6"
    assert result.step_count == 2
    assert result.correct is True

    wrong = evaluate_run("direct", "最终答案：7", "6")
    assert wrong.correct is False
    assert wrong.step_count == 0


def test_compare_outputs_cot_helped() -> None:
    task = ReasoningTask(
        question="难题",
        expected_answer="6",
        case_id="ages",
    )
    report = compare_outputs(
        task,
        direct_output="最终答案：12",
        cot_output="1. 设未知数\n2. 列方程\n最终答案：6",
    )
    assert isinstance(report, CompareReport)
    assert report.direct.correct is False
    assert report.cot.correct is True
    assert report.cot_helped is True
    assert report.cot_hurt is False
    assert report.cot.step_count == 2


def test_compare_outputs_cot_hurt_and_tie() -> None:
    task = ReasoningTask(question="简单题", expected_answer="2", case_id="easy")
    hurt = compare_outputs(
        task,
        direct_output="最终答案：2",
        cot_output="1. 过度推理\n最终答案：3",
    )
    assert hurt.cot_hurt is True
    assert hurt.cot_helped is False

    tie = compare_outputs(
        task,
        direct_output="最终答案：2",
        cot_output="1. ok\n最终答案：2",
    )
    assert tie.cot_helped is False
    assert tie.cot_hurt is False


def test_render_report_contains_verdict() -> None:
    task = ReasoningTask(question="q", expected_answer="1", case_id="c1")
    report = compare_outputs(
        task,
        direct_output="最终答案：0",
        cot_output="1. step\n最终答案：1",
    )
    text = render_report(report)
    assert "case: c1" in text
    assert "expected: 1" in text
    assert "direct:" in text
    assert "cot:" in text
    assert "verdict: helped" in text
