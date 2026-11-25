# Exercise · Day 25 用户故事生成器

## 目标

把「模糊需求」变成可校验的 **用户故事 JSON**，并渲染成 Markdown 方便评审。

本练习 **不调用真实 LLM**：你实现 Prompt 组装 + JSON 抽取/校验；`main.py` 用 mock 回复跑通流水线。

## 文件

| 文件 | 说明 |
|------|------|
| `user_story.py` | 完成全部 TODO |
| `main.py` | 已给齐，阅读即可 |
| `tests/test_user_story.py` | 验收测试 |

## 运行

```bash
cd daily/2026-08-26/exercise
python3 -m pytest -q
python3 main.py --demo
python3 main.py --demo --show-prompt
python3 main.py --demo --json
```

## 约束

- 只用 Python 标准库
- 不要引入 langchain / openai / pydantic（Week 6 再用）
