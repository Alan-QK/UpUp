"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class AgentConfig:
    model: str
    temperature: float = 0.2
    max_tokens: int = 1024

    def to_dict(self) -> dict[str, str | float | int]:
        return asdict(self)
