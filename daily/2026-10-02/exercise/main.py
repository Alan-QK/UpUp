"""Day 51 手工运行入口：按目标打印框架推荐与一页选型笔记。"""

from __future__ import annotations

import argparse

from framework_selection import (
    GOAL_LEARN_LOOP,
    GOAL_MULTI_AGENT,
    GOAL_RAG_APP,
    GOAL_SHIP_PRODUCT,
    LEVEL_ADVANCED,
    LEVEL_BEGINNER,
    LEVEL_INTERMEDIATE,
    ProjectContext,
    default_decision_cases,
    recommend_framework,
    render_selection_note,
)


def context_for_goal(goal: str) -> ProjectContext:
    """给 demo 用的快捷上下文（与 default_decision_cases 同思路）。"""
    presets: dict[str, ProjectContext] = {
        GOAL_LEARN_LOOP: ProjectContext(
            name="个人转型练习",
            goal=GOAL_LEARN_LOOP,
            python_level=LEVEL_INTERMEDIATE,
            need_multi_agent=False,
            need_rag_first=False,
            prefer_official_sdk=False,
            max_frameworks=2,
        ),
        GOAL_SHIP_PRODUCT: ProjectContext(
            name="内部工具助手",
            goal=GOAL_SHIP_PRODUCT,
            python_level=LEVEL_ADVANCED,
            need_multi_agent=False,
            need_rag_first=False,
            prefer_official_sdk=False,
            max_frameworks=1,
        ),
        GOAL_RAG_APP: ProjectContext(
            name="文档问答 Bot",
            goal=GOAL_RAG_APP,
            python_level=LEVEL_INTERMEDIATE,
            need_multi_agent=False,
            need_rag_first=True,
            prefer_official_sdk=False,
            max_frameworks=2,
        ),
        GOAL_MULTI_AGENT: ProjectContext(
            name="调研写作流水线",
            goal=GOAL_MULTI_AGENT,
            python_level=LEVEL_ADVANCED,
            need_multi_agent=True,
            need_rag_first=False,
            prefer_official_sdk=False,
            max_frameworks=2,
        ),
    }
    if goal == "beginner_product":
        return ProjectContext(
            name="新手想直接上线",
            goal=GOAL_SHIP_PRODUCT,
            python_level=LEVEL_BEGINNER,
            need_multi_agent=False,
            need_rag_first=False,
            prefer_official_sdk=True,
            max_frameworks=1,
        )
    return presets[goal]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 51 · 框架选型 Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="打印全部默认案例摘要（默认行为）",
    )
    parser.add_argument(
        "--goal",
        choices=sorted(
            {
                GOAL_LEARN_LOOP,
                GOAL_SHIP_PRODUCT,
                GOAL_RAG_APP,
                GOAL_MULTI_AGENT,
                "beginner_product",
            }
        ),
        help="按预设目标输出一次推荐",
    )
    parser.add_argument(
        "--note",
        action="store_true",
        help="同时打印一页选型笔记（需配合 --goal）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    show_demo = args.demo or args.goal is None

    if args.goal is not None:
        ctx = context_for_goal(args.goal)
        rec = recommend_framework(ctx)
        print(f"# 推荐 · {ctx.name}")
        print(f"goal={ctx.goal}  python_level={ctx.python_level}")
        print(f"primary={rec.primary}")
        print(f"secondary={rec.secondary}")
        print("reasons:")
        for reason in rec.reasons:
            print(f"  - {reason}")
        if args.note:
            print()
            print(render_selection_note(ctx, rec))
        if not show_demo:
            return 0
        print()

    if show_demo:
        print("# 默认决策案例\n")
        for case in default_decision_cases():
            rec = recommend_framework(case.context)
            print(f"## {case.title}")
            print(f"期望主选：{case.expected_primary} / 实际：{rec.primary}")
            print(f"教学点：{case.teaching_point}")
            print(f"备胎：{rec.secondary}")
            print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
