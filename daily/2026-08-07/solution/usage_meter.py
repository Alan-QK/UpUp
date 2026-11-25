"""Day 14 参考实现：Token 估算、费用计算与用量账本。"""

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
    code = ord(ch)
    return (
        0x4E00 <= code <= 0x9FFF
        or 0x3400 <= code <= 0x4DBF
        or 0x3040 <= code <= 0x30FF
        or 0xAC00 <= code <= 0xD7AF
    )


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    cjk = 0
    other = 0
    for ch in text:
        if _is_cjk(ch):
            cjk += 1
        else:
            other += 1
    return cjk + (other + 3) // 4


def calculate_cost_usd(
    prompt_tokens: int,
    completion_tokens: int,
    pricing: ModelPricing,
) -> float:
    raw = (
        prompt_tokens / 1_000_000 * pricing.input_usd_per_1m
        + completion_tokens / 1_000_000 * pricing.output_usd_per_1m
    )
    return round(raw, 8)


def join_message_contents(messages: Sequence[object]) -> str:
    parts: list[str] = []
    for item in messages:
        if isinstance(item, str):
            parts.append(item)
            continue
        if isinstance(item, dict):
            parts.append(str(item.get("content", "")))
            continue
        content = getattr(item, "content", "")
        parts.append(str(content))
    return "\n".join(parts)


class UsageLedger:
    """内存中的用量账本。"""

    def __init__(self) -> None:
        self._records: list[UsageRecord] = []

    @property
    def records(self) -> list[UsageRecord]:
        return list(self._records)

    def record(
        self,
        *,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        pricing: ModelPricing,
        source: Source,
    ) -> UsageRecord:
        if prompt_tokens < 0 or completion_tokens < 0:
            raise ValueError("tokens must be non-negative")
        total = prompt_tokens + completion_tokens
        cost = calculate_cost_usd(prompt_tokens, completion_tokens, pricing)
        rec = UsageRecord(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            cost_usd=cost,
            source=source,
        )
        self._records.append(rec)
        return rec

    def record_from_texts(
        self,
        *,
        model: str,
        prompt_text: str,
        completion_text: str,
        pricing: ModelPricing,
    ) -> UsageRecord:
        return self.record(
            model=model,
            prompt_tokens=estimate_tokens(prompt_text),
            completion_tokens=estimate_tokens(completion_text),
            pricing=pricing,
            source="estimate",
        )

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
        if prompt_tokens is not None and completion_tokens is not None:
            return self.record(
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                pricing=pricing,
                source="api",
            )
        pt = (
            prompt_tokens
            if prompt_tokens is not None
            else estimate_tokens(prompt_text)
        )
        ct = (
            completion_tokens
            if completion_tokens is not None
            else estimate_tokens(completion_text)
        )
        return self.record(
            model=model,
            prompt_tokens=pt,
            completion_tokens=ct,
            pricing=pricing,
            source="estimate",
        )

    def total_tokens(self) -> int:
        return sum(r.total_tokens for r in self._records)

    def total_cost_usd(self) -> float:
        return round(sum(r.cost_usd for r in self._records), 8)

    def format_log_line(self, record: UsageRecord) -> str:
        return (
            f"usage model={record.model} "
            f"prompt={record.prompt_tokens} "
            f"completion={record.completion_tokens} "
            f"total={record.total_tokens} "
            f"cost_usd={record.cost_usd:.8f} "
            f"source={record.source}"
        )

    def format_summary(self) -> str:
        header = (
            f"usage_summary calls={len(self._records)} "
            f"total_tokens={self.total_tokens()} "
            f"total_cost_usd={self.total_cost_usd():.8f}"
        )
        if not self._records:
            return header
        lines = [header]
        lines.extend(self.format_log_line(r) for r in self._records)
        return "\n".join(lines)
