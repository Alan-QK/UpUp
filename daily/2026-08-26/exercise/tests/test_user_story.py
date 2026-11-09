"""Day 25：周挑战 · 用户故事生成器。"""

from __future__ import annotations

import json

import pytest

from user_story import (
    ALLOWED_PRIORITIES,
    DEFAULT_CONSTRAINTS,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_ROLE,
    DEFAULT_TASK,
    PRIORITY_COULD,
    PRIORITY_MUST,
    PRIORITY_SHOULD,
    REQ_BEGIN,
    REQ_END,
    SECTION_CONSTRAINTS,
    SECTION_FEW_SHOT,
    SECTION_OUTPUT_FORMAT,
    SECTION_ROLE,
    SECTION_TASK,
    StoryExample,
    UserStory,
    build_story_messages,
    build_story_system_prompt,
    extract_json_object,
    format_constraints,
    format_few_shot,
    generate_stories_from_response,
    join_sections,
    normalize_priority,
    normalize_text,
    parse_stories_json,
    parse_stories_payload,
    render_stories_markdown,
    stories_to_dict,
    user_story_from_dict,
    wrap_requirement,
)


SAMPLE_STORY = {
    "id": "US-1",
    "title": "查看学习进度",
    "as_a": "学员",
    "i_want": "在首页看到本周完成课时",
    "so_that": "我能合理安排剩余学习时间",
    "acceptance_criteria": ["首页展示本周已完成课时数字", "数字与学习记录一致"],
    "priority": "must",
}


def test_normalize_text() -> None:
    assert normalize_text("  你好\n\n世界  ") == "你好 世界"
    assert normalize_text("a\tb  c") == "a b c"
    assert normalize_text("   ") == ""


def test_normalize_priority() -> None:
    assert normalize_priority(" Must ") == PRIORITY_MUST
    assert normalize_priority("SHOULD") == PRIORITY_SHOULD
    assert normalize_priority("could") == PRIORITY_COULD
    assert ALLOWED_PRIORITIES == {PRIORITY_MUST, PRIORITY_SHOULD, PRIORITY_COULD}
    with pytest.raises(ValueError, match="priority"):
        normalize_priority("high")
    with pytest.raises(ValueError, match="priority"):
        normalize_priority("  ")


def test_wrap_requirement() -> None:
    wrapped = wrap_requirement("  做个打卡功能  ")
    assert wrapped == f"{REQ_BEGIN}\n做个打卡功能\n{REQ_END}"
    with pytest.raises(ValueError, match="requirement"):
        wrap_requirement("  \n ")
    with pytest.raises(ValueError, match="delimiter"):
        wrap_requirement(f"开头 {REQ_BEGIN} 结尾")


def test_format_constraints_and_join_sections() -> None:
    assert format_constraints(["  A  ", "", " B\nB "]) == "- A\n- B B"
    assert format_constraints([]) == ""
    text = join_sections(
        [
            ("角色", "产品经理"),
            ("空", "  "),
            ("任务", "拆故事"),
        ]
    )
    assert text == "【角色】\n产品经理\n\n【任务】\n拆故事"


def test_format_few_shot() -> None:
    assert format_few_shot([]) == ""
    example = StoryExample(
        requirement="  登录  ",
        stories=[
            {
                "id": "US-1",
                "title": "账号登录",
                "as_a": "用户",
                "i_want": "用邮箱登录",
                "so_that": "进入系统",
                "acceptance_criteria": ["输入正确密码可进入"],
                "priority": "must",
            }
        ],
    )
    body = format_few_shot([example])
    assert "例1 需求：登录" in body
    assert "例1 输出：" in body
    assert '"stories"' in body
    with pytest.raises(ValueError, match="requirement"):
        format_few_shot([StoryExample(requirement="  ", stories=[{"id": "x"}])])
    with pytest.raises(ValueError, match="stories"):
        format_few_shot([StoryExample(requirement="需求", stories=[])])


def test_build_story_system_prompt_order() -> None:
    prompt = build_story_system_prompt()
    assert prompt.startswith(f"【{SECTION_ROLE}】\n{normalize_text(DEFAULT_ROLE)}")
    assert f"【{SECTION_TASK}】\n{normalize_text(DEFAULT_TASK)}" in prompt
    assert f"【{SECTION_CONSTRAINTS}】" in prompt
    for item in DEFAULT_CONSTRAINTS:
        assert normalize_text(item) in normalize_text(prompt)
    assert f"【{SECTION_OUTPUT_FORMAT}】" in prompt
    assert normalize_text(DEFAULT_OUTPUT_FORMAT) in normalize_text(
        prompt.split(f"【{SECTION_OUTPUT_FORMAT}】\n", 1)[1]
    )
    assert f"【{SECTION_FEW_SHOT}】" not in prompt

    with_examples = build_story_system_prompt(
        examples=[
            StoryExample(requirement="重置密码", stories=[SAMPLE_STORY]),
        ]
    )
    assert f"【{SECTION_FEW_SHOT}】" in with_examples
    assert "例1 需求：重置密码" in with_examples

    with pytest.raises(ValueError, match="role"):
        build_story_system_prompt(role="  ")
    with pytest.raises(ValueError, match="task"):
        build_story_system_prompt(task="\n")
    with pytest.raises(ValueError, match="output_format"):
        build_story_system_prompt(output_format=" ")
    with pytest.raises(ValueError, match="constraints"):
        build_story_system_prompt(constraints=["  ", ""])


def test_build_story_messages() -> None:
    messages = build_story_messages("支持课程收藏")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "【角色】" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"].startswith(REQ_BEGIN)
    assert "支持课程收藏" in messages[1]["content"]


def test_extract_json_object_plain_and_fenced() -> None:
    plain = '前言 {"stories":[{"id":"US-1"}]} 后记'
    assert extract_json_object(plain) == '{"stories":[{"id":"US-1"}]}'

    fenced = '好的：\n```json\n{"stories":[{"id":"US-2"}]}\n```\n完'
    assert json.loads(extract_json_object(fenced)) == {
        "stories": [{"id": "US-2"}]
    }

    nested = '{"stories":[{"title":"含 { 花括号 }","id":"US-3"}]}'
    assert extract_json_object(f"x{nested}y") == nested

    with pytest.raises(ValueError):
        extract_json_object("没有对象")
    with pytest.raises(ValueError):
        extract_json_object("{未闭合")
    with pytest.raises(ValueError):
        extract_json_object("   ")


def test_user_story_from_dict_and_payload() -> None:
    story = user_story_from_dict(SAMPLE_STORY)
    assert story.id == "US-1"
    assert story.priority == PRIORITY_MUST
    assert len(story.acceptance_criteria) == 2

    stories = parse_stories_payload({"stories": [SAMPLE_STORY, {
        **SAMPLE_STORY,
        "id": "US-2",
        "priority": "Should",
        "acceptance_criteria": ["  条件A  ", ""],
    }]})
    assert [s.id for s in stories] == ["US-1", "US-2"]
    assert stories[1].priority == PRIORITY_SHOULD
    assert stories[1].acceptance_criteria == ("条件A",)

    with pytest.raises(ValueError, match="acceptance_criteria"):
        user_story_from_dict({**SAMPLE_STORY, "acceptance_criteria": ["  ", ""]})
    with pytest.raises(ValueError, match="unique"):
        parse_stories_payload({"stories": [SAMPLE_STORY, SAMPLE_STORY]})
    with pytest.raises(ValueError, match="stories"):
        parse_stories_payload({"stories": []})
    with pytest.raises(TypeError, match="stories"):
        parse_stories_payload({"stories": "nope"})


def test_parse_stories_json_roundtrip_markdown() -> None:
    raw = (
        "如下：\n```json\n"
        + json.dumps({"stories": [SAMPLE_STORY]}, ensure_ascii=False)
        + "\n```"
    )
    stories = parse_stories_json(raw)
    assert len(stories) == 1
    payload = stories_to_dict(stories)
    assert payload["stories"][0]["id"] == "US-1"
    assert payload["stories"][0]["acceptance_criteria"] == list(
        SAMPLE_STORY["acceptance_criteria"]
    )

    md = render_stories_markdown(stories)
    assert "### US-1 · 查看学习进度" in md
    assert "**As a** 学员" in md
    assert "**Priority** `must`" in md
    assert "首页展示本周已完成课时数字" in md
    with pytest.raises(ValueError, match="stories"):
        render_stories_markdown([])


def test_generate_stories_from_response_pipeline() -> None:
    response = json.dumps({"stories": [SAMPLE_STORY]}, ensure_ascii=False)
    messages, stories = generate_stories_from_response(
        "学员要看进度",
        response,
        examples=[StoryExample(requirement="示例", stories=[SAMPLE_STORY])],
    )
    assert messages[0]["role"] == "system"
    assert "【示例】" in messages[0]["content"]
    assert isinstance(stories[0], UserStory)
    assert stories[0].title == "查看学习进度"
