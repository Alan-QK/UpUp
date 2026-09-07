"""Day 27：校验失败重试 · repair loop。"""

from __future__ import annotations

import json

import pytest

from repair_loop import (
    ALLOWED_FAILURE_KINDS,
    FAILURE_EXTRACT,
    FAILURE_JSON,
    FAILURE_OTHER,
    FAILURE_VALIDATION,
    AttemptRecord,
    RepairResult,
    TaskBatch,
    append_repair_turn,
    build_repair_user_message,
    classify_failure,
    parse_task_batch,
    run_repair_loop,
)


SAMPLE_OK = {
    "tasks": [
        {
            "id": "T-1",
            "title": "修登录",
            "priority": "high",
            "tags": ["auth"],
            "estimate_hours": 1.5,
        }
    ]
}

SAMPLE_BAD_PRIORITY = {
    "tasks": [
        {
            "id": "T-1",
            "title": "修登录",
            "priority": "紧急",
            "tags": [],
            "estimate_hours": -1,
        }
    ]
}


def _ok_raw() -> str:
    return "如下：\n```json\n" + json.dumps(SAMPLE_OK, ensure_ascii=False) + "\n```\n"


def _bad_validation_raw() -> str:
    return json.dumps(SAMPLE_BAD_PRIORITY, ensure_ascii=False)


class QueueLLM:
    """按顺序返回预设回复；并记录每次收到的 messages 长度。"""

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.calls: list[list[dict[str, str]]] = []

    def __call__(self, messages: list[dict[str, str]]) -> str:
        self.calls.append([dict(m) for m in messages])
        if not self.replies:
            raise AssertionError("LLM queue exhausted")
        return self.replies.pop(0)


def test_parse_task_batch_still_works() -> None:
    batch = parse_task_batch(_ok_raw())
    assert isinstance(batch, TaskBatch)
    assert batch.tasks[0].id == "T-1"


def test_classify_failure() -> None:
    assert classify_failure(ValueError("validation failed: a: b")) == FAILURE_VALIDATION
    assert classify_failure(ValueError("invalid json: boom")) == FAILURE_JSON
    assert classify_failure(ValueError("empty model output")) == FAILURE_EXTRACT
    assert classify_failure(ValueError("no json object found")) == FAILURE_EXTRACT
    assert classify_failure(ValueError("something else")) == FAILURE_OTHER
    assert FAILURE_VALIDATION in ALLOWED_FAILURE_KINDS


def test_build_repair_user_message_ok() -> None:
    text = build_repair_user_message(
        "tasks/0/priority: invalid",
        failure_kind=FAILURE_VALIDATION,
        repair_index=1,
        max_repairs=3,
    )
    assert "tasks/0/priority: invalid" in text
    assert "只输出" in text
    assert "JSON" in text
    assert "修复第" in text
    assert "1/3" in text
    assert "字段" in text

    extract_msg = build_repair_user_message(
        "no json object found",
        failure_kind=FAILURE_EXTRACT,
        repair_index=2,
        max_repairs=3,
    )
    assert "完整" in extract_msg
    assert "2/3" in extract_msg

    json_msg = build_repair_user_message(
        "invalid json: x",
        failure_kind=FAILURE_JSON,
        repair_index=1,
        max_repairs=2,
    )
    assert "语法" in json_msg


def test_build_repair_user_message_errors() -> None:
    with pytest.raises(ValueError, match="error"):
        build_repair_user_message(
            "  ",
            failure_kind=FAILURE_OTHER,
            repair_index=1,
            max_repairs=3,
        )
    with pytest.raises(ValueError, match="kind"):
        build_repair_user_message(
            "x",
            failure_kind="nope",
            repair_index=1,
            max_repairs=3,
        )
    with pytest.raises(ValueError, match="repair"):
        build_repair_user_message(
            "x",
            failure_kind=FAILURE_OTHER,
            repair_index=0,
            max_repairs=3,
        )
    with pytest.raises(ValueError, match="repair"):
        build_repair_user_message(
            "x",
            failure_kind=FAILURE_OTHER,
            repair_index=4,
            max_repairs=3,
        )
    with pytest.raises(ValueError, match="max_repairs"):
        build_repair_user_message(
            "x",
            failure_kind=FAILURE_OTHER,
            repair_index=1,
            max_repairs=0,
        )


def test_append_repair_turn() -> None:
    base = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
    out = append_repair_turn(
        base,
        assistant_raw='{"bad": true}',
        repair_user="请修复",
    )
    assert len(base) == 2  # 原列表不变
    assert len(out) == 4
    assert out[2] == {"role": "assistant", "content": '{"bad": true}'}
    assert out[3] == {"role": "user", "content": "请修复"}
    with pytest.raises(ValueError, match="assistant"):
        append_repair_turn(base, assistant_raw="  ", repair_user="ok")
    with pytest.raises(ValueError, match="user"):
        append_repair_turn(base, assistant_raw="ok", repair_user="")


def test_run_repair_loop_first_success() -> None:
    llm = QueueLLM([_ok_raw()])
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "做任务清单"},
    ]
    result = run_repair_loop(llm=llm, initial_messages=messages, max_repairs=3)
    assert isinstance(result, RepairResult)
    assert result.batch is not None
    assert result.batch.tasks[0].title == "修登录"
    assert result.repaired is False
    assert result.exhausted is False
    assert len(result.attempts) == 1
    assert result.attempts[0] == AttemptRecord(
        attempt=1, raw=_ok_raw(), ok=True, error=None, failure_kind=None
    )
    assert len(llm.calls) == 1
    assert len(llm.calls[0]) == 2


def test_run_repair_loop_fail_then_success() -> None:
    llm = QueueLLM([_bad_validation_raw(), _ok_raw()])
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "做任务清单"},
    ]
    result = run_repair_loop(llm=llm, initial_messages=messages, max_repairs=3)
    assert result.batch is not None
    assert result.repaired is True
    assert result.exhausted is False
    assert len(result.attempts) == 2
    assert result.attempts[0].ok is False
    assert result.attempts[0].failure_kind == FAILURE_VALIDATION
    assert result.attempts[1].ok is True
    assert len(llm.calls) == 2
    # 第二次调用应带上 assistant 坏输出 + repair user
    assert len(llm.calls[1]) == 4
    assert llm.calls[1][2]["role"] == "assistant"
    assert llm.calls[1][3]["role"] == "user"
    assert "只输出" in llm.calls[1][3]["content"]
    assert "1/3" in llm.calls[1][3]["content"]


def test_run_repair_loop_fail_twice_then_success() -> None:
    llm = QueueLLM(
        [
            "完全没有大括号",
            _bad_validation_raw(),
            _ok_raw(),
        ]
    )
    messages = [{"role": "user", "content": "x"}]
    result = run_repair_loop(llm=llm, initial_messages=messages, max_repairs=3)
    assert result.batch is not None
    assert result.repaired is True
    assert len(result.attempts) == 3
    assert result.attempts[0].failure_kind == FAILURE_EXTRACT
    assert result.attempts[1].failure_kind == FAILURE_VALIDATION
    assert len(llm.calls[2]) == 5  # 1 user + 2*(assistant+user)


def test_run_repair_loop_exhausted() -> None:
    bad = _bad_validation_raw()
    llm = QueueLLM([bad, bad, bad, bad])
    messages = [{"role": "user", "content": "x"}]
    result = run_repair_loop(llm=llm, initial_messages=messages, max_repairs=3)
    assert result.batch is None
    assert result.exhausted is True
    assert result.repaired is False
    assert len(result.attempts) == 4  # 1 + 3 repairs
    assert all(not a.ok for a in result.attempts)
    assert len(llm.calls) == 4
    # 不应再有第 5 次
    assert not llm.replies or True


def test_run_repair_loop_max_repairs_zero() -> None:
    llm = QueueLLM([_bad_validation_raw()])
    messages = [{"role": "user", "content": "x"}]
    result = run_repair_loop(llm=llm, initial_messages=messages, max_repairs=0)
    assert result.exhausted is True
    assert result.batch is None
    assert len(result.attempts) == 1
    assert len(llm.calls) == 1


def test_run_repair_loop_input_errors() -> None:
    llm = QueueLLM([_ok_raw()])
    with pytest.raises(ValueError, match="max_repairs"):
        run_repair_loop(llm=llm, initial_messages=[{"role": "user", "content": "x"}], max_repairs=-1)
    with pytest.raises(ValueError, match="messages"):
        run_repair_loop(llm=llm, initial_messages=[], max_repairs=3)
