"""Day 71 练习：何时用多智能体（适用 / 不适用决策清单）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——不调用 LLM。

提示：
- 常量、权重、标签、数据类已给齐
- 先写 normalize_title / collect_signals / compute_score
- 再实现 decide（注意否决规则优先级）
- 最后补 render_checklist / summarize / demo / report
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

# --- 推荐结论 ---

REC_USE_MULTI = "use_multi"
REC_KEEP_SINGLE = "keep_single"
REC_DEFER = "defer"
VALID_RECOMMENDATIONS = frozenset({REC_USE_MULTI, REC_KEEP_SINGLE, REC_DEFER})

# --- 信号权重（教学启发式，非生产公式） ---

POSITIVE_WEIGHTS: dict[str, int] = {
    "distinct_roles": 2,
    "handoff_chain": 2,
    "parallel_workstreams": 1,
    "adversarial_review": 2,
    "specialty_toolsets": 1,
}

NEGATIVE_WEIGHTS: dict[str, int] = {
    "single_skill_loop": 2,
    "tight_latency": 2,
    "cost_sensitive": 1,
    "blurry_roles": 2,
    "heavy_shared_mutable_state": 1,
}

POSITIVE_LABELS: dict[str, str] = {
    "distinct_roles": "需要清晰分工的专职角色（如研究 / 写作 / 审校）",
    "handoff_chain": "产物需流水线交接（A 的输出是 B 的输入）",
    "parallel_workstreams": "存在可并行的独立工作流",
    "adversarial_review": "需要对立视角或独立审校",
    "specialty_toolsets": "不同角色需要完全不同的工具集",
}

NEGATIVE_LABELS: dict[str, str] = {
    "single_skill_loop": "单技能工具循环即可（查 → 答）",
    "tight_latency": "延迟预算紧，多轮协调会拖垮体验",
    "cost_sensitive": "成本敏感，多 Agent 会成倍烧 token",
    "blurry_roles": "角色边界说不清，容易互相推诿",
    "heavy_shared_mutable_state": "强依赖复杂共享可变状态，协调成本高",
}

USE_MULTI_MIN_POSITIVES = 2
USE_MULTI_MIN_SCORE = 3

REQUIRED_REPORT_SECTIONS = (
    "何为多智能体决策",
    "适用信号与不适用信号",
    "决策规则",
    "今日演示统计",
    "明日预告",
)


@dataclass(frozen=True)
class TaskProfile:
    """任务画像：用布尔信号描述「该不该拆多智能体」。"""

    title: str
    distinct_roles: bool = False
    handoff_chain: bool = False
    parallel_workstreams: bool = False
    adversarial_review: bool = False
    specialty_toolsets: bool = False
    single_skill_loop: bool = False
    tight_latency: bool = False
    cost_sensitive: bool = False
    blurry_roles: bool = False
    heavy_shared_mutable_state: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be non-empty str")
        for name in (
            "distinct_roles",
            "handoff_chain",
            "parallel_workstreams",
            "adversarial_review",
            "specialty_toolsets",
            "single_skill_loop",
            "tight_latency",
            "cost_sensitive",
            "blurry_roles",
            "heavy_shared_mutable_state",
        ):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be bool")


@dataclass(frozen=True)
class SignalHit:
    """命中的一条信号。"""

    key: str
    polarity: str  # "pro" | "con"
    weight: int
    label: str

    def __post_init__(self) -> None:
        if self.polarity not in {"pro", "con"}:
            raise ValueError("polarity must be pro or con")
        if not isinstance(self.key, str) or not self.key.strip():
            raise ValueError("key must be non-empty str")
        if not isinstance(self.weight, int) or self.weight < 1:
            raise ValueError("weight must be int >= 1")
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("label must be non-empty str")


@dataclass(frozen=True)
class Decision:
    """一次多智能体适用性决策。"""

    title: str
    recommendation: str
    score: int
    rationale: str
    pros: tuple[SignalHit, ...]
    cons: tuple[SignalHit, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be non-empty str")
        if self.recommendation not in VALID_RECOMMENDATIONS:
            raise ValueError(f"invalid recommendation: {self.recommendation}")
        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise ValueError("rationale must be non-empty str")
        if not isinstance(self.pros, tuple) or not isinstance(self.cons, tuple):
            raise TypeError("pros/cons must be tuple")


def normalize_title(text: str) -> str:
    """去掉首尾空白、压缩中间空白。"""
    # TODO
    raise NotImplementedError


def collect_signals(profile: TaskProfile) -> tuple[tuple[SignalHit, ...], tuple[SignalHit, ...]]:
    """按画像收集正/负信号（按 key 排序，保证稳定）。"""
    # TODO
    raise NotImplementedError


def compute_score(pros: Sequence[SignalHit], cons: Sequence[SignalHit]) -> int:
    """score = Σ pro.weight − Σ con.weight。"""
    # TODO
    raise NotImplementedError


def decide(profile: TaskProfile) -> Decision:
    """根据任务画像给出 use_multi / keep_single / defer。

    规则优先级：
    1. 否决：blurry_roles 且没有 distinct_roles → keep_single
    2. 否决：single_skill_loop 且没有任何「强拆分信号」
       （distinct_roles / handoff_chain / adversarial_review）→ keep_single
    3. 采用：命中 ≥ USE_MULTI_MIN_POSITIVES 条正信号且 score ≥ USE_MULTI_MIN_SCORE
       → use_multi
    4. 拒绝：score ≤ 0，或（负信号 ≥ 2 且正信号 ≤ 1）→ keep_single
    5. 其余 → defer（信号打架，先别拆）
    """
    # TODO
    raise NotImplementedError


def render_checklist(decision: Decision) -> str:
    """把决策渲染成可读清单（适用 / 不适用 / 结论）。

    必须包含：
    - 一级标题含决策 title
    - `## 适用信号（Pro）` / `## 不适用信号（Con）` / `## 结论`
    - 结论行含 recommendation 字面量（反引号包起来亦可）
    """
    # TODO
    raise NotImplementedError


def summarize_decision(decision: Decision) -> dict[str, object]:
    """结构化摘要，便于 CLI / 测试断言。

    键：title / recommendation / score / pro_count / con_count /
        pro_keys / con_keys / rationale
    """
    # TODO
    raise NotImplementedError


def build_demo_profiles() -> tuple[TaskProfile, ...]:
    """六条典型场景（覆盖三种推荐结论）。

    顺序与内容需与下方约定一致（测试会按 index 断言）：
    0. 查天气并一句话回复 → keep_single（单技能 + 延迟/成本）
    1. 调研向量库 → 写对比报告 → 独立审校 → use_multi
    2. 客服 FAQ 单轮问答 → keep_single
    3. 代码生成后由安全审计员挑刺 → use_multi
    4. 想拆很多 Agent 但说不清各自职责 → keep_single（blurry 否决）
    5. 可并行搜集资料但成本敏感、尚无专职角色 → defer
       （parallel+specialty vs cost；score 正但未达采用阈值）
    """
    # TODO
    raise NotImplementedError


def build_demo_decisions() -> tuple[Decision, ...]:
    """对演示画像逐条 decide。"""
    # TODO
    raise NotImplementedError


def render_decision_report(decisions: Sequence[Decision] | None = None) -> str:
    """学习报告（必须包含 REQUIRED_REPORT_SECTIONS 五个二级标题）。"""
    # TODO
    raise NotImplementedError
