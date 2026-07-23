"""手工试跑：确认工具函数行为（测试请写在 tests/）。"""

from __future__ import annotations

from prompt_utils import extract_tagged_block, normalize_whitespace, truncate


def main() -> None:
    raw = "  hello   \n  agent  world  "
    print("normalize:", repr(normalize_whitespace(raw)))
    print("truncate:", repr(truncate("abcdefghijklmnopqrstuvwxyz", 10)))
    sample = "前缀 <answer>42</answer> 后缀"
    print("extract:", repr(extract_tagged_block(sample, "answer")))


if __name__ == "__main__":
    main()
