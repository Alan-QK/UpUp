"""Day 72 入口：流水线双 Agent 演示。"""

from __future__ import annotations

import argparse

from pipeline_agents import (
    build_demo_topics,
    render_pipeline_report,
    render_trace,
    run_pipeline,
    summarize_pipeline,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 72 · Researcher → Writer 流水线")
    parser.add_argument("--demo", action="store_true", help="批量跑三条演示主题")
    parser.add_argument("--report", action="store_true", help="输出学习报告")
    parser.add_argument("--topic", type=str, default="", help="单主题跑通流水线")
    parser.add_argument("--trace", action="store_true", help="打印 trace（可与 --topic 联用）")
    args = parser.parse_args()

    if args.report:
        print(render_pipeline_report())
        return

    if args.topic.strip():
        result = run_pipeline(args.topic)
        sm = summarize_pipeline(result)
        print(f"topic={sm['topic']}")
        print(f"title={sm['title']}")
        print(f"findings={sm['finding_count']} sources={sm['source_ids']}")
        if args.trace or True:
            print("--- trace ---")
            print(render_trace(result.trace))
            print("--- article ---")
            print(result.article.body)
        return

    # 默认 / --demo
    topics = build_demo_topics()
    print(f"演示 {len(topics)} 条流水线")
    for topic in topics:
        result = run_pipeline(topic)
        sm = summarize_pipeline(result)
        print(
            f"- {sm['topic']}: findings={sm['finding_count']} "
            f"outline={sm['outline_len']} actions={sm['trace_actions']}"
        )
        if args.trace:
            print(render_trace(result.trace))
            print("-" * 40)


if __name__ == "__main__":
    main()
