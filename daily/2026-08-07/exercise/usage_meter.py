"""Day 14 练习：Token 估算、费用计算与用量账本。

请完成 TODO，使 tests/ 全部通过。
全程只需标准库。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence


Source = Literal["api", "estimate"]


@dataclass(frozen=True)
class ModelPricing:
    """某模型的示意单价（美元 / 百万 token）。"""

    model: str
    input_usd_per_1m: float
    output_usd_per_1m: float


# 示意价目表（非实时官网价；仅供练习）
DEFAULT_PRICING: dict[str, ModelPricing] = {
    "gpt-4o-mini": ModelPricing("gpt-4o-mini", 0.15, 0.60),
    "demo-model": ModelPricing("demo-model", 1.0, 2.0),
}


@dataclass(frozen=True)
class UsageRecord:
    """一次调用的用量与费用记录。"""

    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    source: Source


def _is_cjk(ch: str) -> bool:
    """判断是否按「1 字 ≈ 1 token」计数的 CJK 类字符。"""
    code = ord(ch)
    return (
        0x4E00 <= code <= 0x9FFF  # CJK Unified Ideographs
        or 0x3400 <= code <= 0x4DBF  # CJK Extension A
        or 0x3040 <= code <= 0x30FF  # Hiragana / Katakana
        or 0xAC00 <= code <= 0xD7AF  # Hangul Syllables
    )


def estimate_tokens(text: str) -> int:
    """按今日约定启发式估算 token 数。

    规则：
    - 空字符串 → 0
    - CJK 类字符：每个计 1
    - 其余字符共 n 个：计 (n + 3) // 4
    - 返回两者之和
    """
    # TODO: 实现这里
    raise NotImplementedError


def calculate_cost_usd(
    prompt_tokens: int,
    completion_tokens: int,
    pricing: ModelPricing,
) -> float:
    """按百万 token 单价计算美元费用，结果用 round(..., 8)。

    cost = prompt/1e6 * input_usd_per_1m + completion/1e6 * output_usd_per_1m
    """
    # TODO: 实现这里
    raise NotImplementedError


def join_message_contents(messages: Sequence[object]) -> str:
    """把消息列表拼成一段文本，供估算 prompt 使用。

    支持：
    - 带 `.content` 属性的对象（如 ChatMessage）
    - dict，取 `content` 键
    - 纯 str

    各段之间用单个换行拼接；非 str 的 content 转成 str。
    """
    # TODO: 实现这里
    raise NotImplementedError


class UsageLedger:
    """内存中的用量账本。"""

    def __init__(self) -> None:
        # TODO: 初始化内部列表
        raise NotImplementedError

    @property
    def records(self) -> list[UsageRecord]:
        """返回记录副本（防止外部篡改内部列表）。"""
        # TODO: 实现这里
        raise NotImplementedError

    def record(
        self,
        *,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        pricing: ModelPricing,
        source: Source,
    ) -> UsageRecord:
        """写入一条记录并返回。

        - prompt_tokens / completion_tokens 不得为负，否则 ValueError("tokens must be non-negative")
        - total_tokens = prompt_tokens + completion_tokens
        - cost_usd = calculate_cost_usd(...)
        """
        # TODO: 实现这里
        raise NotImplementedError

    def record_from_texts(
        self,
        *,
        model: str,
        prompt_text: str,
        completion_text: str,
        pricing: ModelPricing,
    ) -> UsageRecord:
        """用本地估算写入，source 固定为 estimate。"""
        # TODO: 实现这里
        raise NotImplementedError

    def record_from_api_usage(
        self,
        *,
        model: str,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        pricing: ModelPricing,
        prompt_text: str = "",
        completion_text: str = "",
    ) -> UsageRecord:
        """优先使用 API usage；任一为 None 则对该侧（或双侧）用文本估算。

        - 两者都是 int → source="api"（即便文本也传了，仍以 API 为准）
        - 否则缺失侧用 estimate_tokens(对应文本) 补齐 → source="estimate"
        """
        # TODO: 实现这里
        raise NotImplementedError

    def total_tokens(self) -> int:
        """所有记录的 total_tokens 之和。"""
        # TODO: 实现这里
        raise NotImplementedError

    def total_cost_usd(self) -> float:
        """所有记录的 cost_usd 之和，再 round(..., 8)。"""
        # TODO: 实现这里
        raise NotImplementedError

    def format_log_line(self, record: UsageRecord) -> str:
        """单行日志，格式必须为：

        usage model={model} prompt={n} completion={n} total={n} cost_usd={:.8f} source={api|estimate}
        """
        # TODO: 实现这里
        raise NotImplementedError

    def format_summary(self) -> str:
        """多行汇总：

        第一行：usage_summary calls={n} total_tokens={n} total_cost_usd={:.8f}
        随后每一行：一条 format_log_line（按记录顺序）
        若无记录：只返回 summary 行（calls=0 total_tokens=0 total_cost_usd=0.00000000）
        """
        # TODO: 实现这里
        raise NotImplementedError
