"""Day 17 练习：采样参数（temperature / top_p）对比实验。

请完成 TODO，使 tests/ 全部通过。
依赖：同目录下已给齐的 chat_client.py。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from chat_client import ChatClient, ChatMessage


_TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


@dataclass(frozen=True)
class SamplingRun:
    """一次固定采样参数下的调用结果。"""

    temperature: float
    top_p: float | None
    content: str
    finish_reason: str | None = None


def validate_temperature(value: float) -> float:
    """校验 temperature ∈ [0, 2]，合法则原样返回。

    非法 → ValueError("temperature must be in [0, 2]")
    """
    # TODO
    raise NotImplementedError


def validate_top_p(value: float) -> float:
    """校验 top_p ∈ (0, 1]，合法则原样返回。

    非法 → ValueError("top_p must be in (0, 1]")
    """
    # TODO
    raise NotImplementedError


def tokenize(text: str) -> list[str]:
    """把文本拆成小写 token 列表（字母数字 / CJK 连续段）。

    空串或无匹配 → []
    """
    # TODO: 用模块顶部的 _TOKEN_RE.findall，再 .lower()
    raise NotImplementedError


def unique_token_ratio(text: str) -> float:
    """独特 token 占比：len(set(tokens)) / len(tokens)。

    - 无 token → 0.0
    - 返回 float，不做额外 round
    """
    # TODO
    raise NotImplementedError


def jaccard_distance(a: str, b: str) -> float:
    """基于 token 集合的 Jaccard 距离：1 - |A∩B| / |A∪B|。

    - 两边都无 token → 0.0
    - 否则按集合计算；距离越大表示两段文本越不像
    """
    # TODO
    raise NotImplementedError


def run_temperature_sweep(
    client: ChatClient,
    messages: Sequence[ChatMessage],
    temperatures: Sequence[float],
    *,
    top_p: float | None = None,
) -> list[SamplingRun]:
    """对同一组 messages，按 temperatures 依次调用 complete。

    规则：
    - 先 validate 每一个 temperature；若提供 top_p 也先 validate
    - 空 temperatures → []
    - 每次调用：client.complete(messages, temperature=t, top_p=top_p)
    - 按 temperatures 原序返回 SamplingRun 列表
    """
    # TODO
    raise NotImplementedError


def format_comparison_report(runs: Sequence[SamplingRun]) -> str:
    """把多次采样结果格式化成可读对比报告（纯文本）。

    要求（测试会检查关键片段）：
    1. 首行恰好：`# Temperature Sweep Report`
    2. 空 runs → 第二行 `（无采样结果）`，并以单个换行结束
    3. 非空时，每个 run 一块，块与块之间空一行；每块至少包含：
       - `## temperature=X`（X 用原浮点的默认 str，如 0.0 / 0.7）
       - `top_p=` 行：有值写数值，None 写 `default`
       - `chars=` 后接 len(content)
       - `unique_token_ratio=` 后接 f"{unique_token_ratio(content):.3f}"
       - `preview=` 后接 content 去首尾空白后最多 80 字符；超长加 `...`
    4. 若 len(runs) >= 2，报告末尾追加一节：
       - 标题行 `## Pairwise Jaccard Distance`
       - 对所有 i < j：一行
         `t{i}-t{j}: {jaccard_distance(...):.3f}`
         其中 i/j 是 0-based 下标
    5. 整个报告以单个换行符结尾
    """
    # TODO
    raise NotImplementedError
