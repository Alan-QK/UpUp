"""Day 71 参考实现：何时用多智能体（适用 / 不适用决策清单）。

全程只用标准库——不调用 LLM。
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
    if not isinstance(text, str):
        raise TypeError("title must be str")
    return " ".join(text.split())


def collect_signals(profile: TaskProfile) -> tuple[tuple[SignalHit, ...], tuple[SignalHit, ...]]:
    """按画像收集正/负信号（按 key 排序，保证稳定）。"""
    if not isinstance(profile, TaskProfile):
        raise TypeError("profile must be TaskProfile")

    pros: list[SignalHit] = []
    for key, weight in POSITIVE_WEIGHTS.items():
        if getattr(profile, key):
            pros.append(
                SignalHit(
                    key=key,
                    polarity="pro",
                    weight=weight,
                    label=POSITIVE_LABELS[key],
                )
            )

    cons: list[SignalHit] = []
    for key, weight in NEGATIVE_WEIGHTS.items():
        if getattr(profile, key):
            cons.append(
                SignalHit(
                    key=key,
                    polarity="con",
                    weight=weight,
                    label=NEGATIVE_LABELS[key],
                )
            )

    pros.sort(key=lambda s: s.key)
    cons.sort(key=lambda s: s.key)
    return tuple(pros), tuple(cons)


def compute_score(pros: Sequence[SignalHit], cons: Sequence[SignalHit]) -> int:
    """score = Σ pro.weight − Σ con.weight。"""
    return sum(s.weight for s in pros) - sum(s.weight for s in cons)


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
    title = normalize_title(profile.title)
    if len(title) < 2:
        raise ValueError("title too short after normalize")

    pros, cons = collect_signals(profile)
    score = compute_score(pros, cons)
    pro_keys = {s.key for s in pros}

    # 1) 角色切不清
    if profile.blurry_roles and not profile.distinct_roles:
        return Decision(
            title=title,
            recommendation=REC_KEEP_SINGLE,
            score=score,
            rationale="角色边界说不清时先保持单 Agent；能叫出专职角色再考虑拆分",
            pros=pros,
            cons=cons,
        )

    # 2) 单技能循环且无强拆分信号
    strong_split = bool(
        pro_keys
        & {"distinct_roles", "handoff_chain", "adversarial_review"}
    )
    if profile.single_skill_loop and not strong_split:
        return Decision(
            title=title,
            recommendation=REC_KEEP_SINGLE,
            score=score,
            rationale="单技能工具循环足够；没有专职角色 / 流水线 / 对立审校时不必拆",
            pros=pros,
            cons=cons,
        )

    # 3) 明确适用
    if len(pros) >= USE_MULTI_MIN_POSITIVES and score >= USE_MULTI_MIN_SCORE:
        return Decision(
            title=title,
            recommendation=REC_USE_MULTI,
            score=score,
            rationale=(
                f"命中 {len(pros)} 条适用信号且 score={score}≥{USE_MULTI_MIN_SCORE}；"
                "值得按角色或流水线拆分"
            ),
            pros=pros,
            cons=cons,
        )

    # 4) 明确不适用
    if score <= 0 or (len(cons) >= 2 and len(pros) <= 1):
        return Decision(
            title=title,
            recommendation=REC_KEEP_SINGLE,
            score=score,
            rationale="不适用信号占优或得分非正；优先单 Agent + 多步骤（Plan/Execute）",
            pros=pros,
            cons=cons,
        )

    # 5) 观望
    return Decision(
        title=title,
        recommendation=REC_DEFER,
        score=score,
        rationale="信号互相拉扯；先用单 Agent 跑通闭环，再评估是否值得拆",
        pros=pros,
        cons=cons,
    )


def render_checklist(decision: Decision) -> str:
    """把决策渲染成可读清单（适用 / 不适用 / 结论）。"""
    if not isinstance(decision, Decision):
        raise TypeError("decision must be Decision")

    lines = [
        f"# 多智能体决策清单｜{decision.title}",
        "",
        "## 适用信号（Pro）",
    ]
    if decision.pros:
        for s in decision.pros:
            lines.append(f"- [x] (+{s.weight}) {s.label}")
    else:
        lines.append("- （无）")

    lines.extend(["", "## 不适用信号（Con）"])
    if decision.cons:
        for s in decision.cons:
            lines.append(f"- [x] (-{s.weight}) {s.label}")
    else:
        lines.append("- （无）")

    label = {
        REC_USE_MULTI: "建议使用多智能体",
        REC_KEEP_SINGLE: "建议保持单 Agent",
        REC_DEFER: "暂缓拆分（先跑通单 Agent）",
    }[decision.recommendation]

    lines.extend(
        [
            "",
            "## 结论",
            f"- 推荐：{label}（`{decision.recommendation}`）",
            f"- 得分：{decision.score}",
            f"- 理由：{decision.rationale}",
            "",
        ]
    )
    return "\n".join(lines)


def summarize_decision(decision: Decision) -> dict[str, object]:
    """结构化摘要，便于 CLI / 测试断言。"""
    if not isinstance(decision, Decision):
        raise TypeError("decision must be Decision")
    return {
        "title": decision.title,
        "recommendation": decision.recommendation,
        "score": decision.score,
        "pro_count": len(decision.pros),
        "con_count": len(decision.cons),
        "pro_keys": [s.key for s in decision.pros],
        "con_keys": [s.key for s in decision.cons],
        "rationale": decision.rationale,
    }


def build_demo_profiles() -> tuple[TaskProfile, ...]:
    """六条典型场景（覆盖三种推荐结论）。"""
    return (
        TaskProfile(
            title="查天气并一句话回复",
            single_skill_loop=True,
            tight_latency=True,
            cost_sensitive=True,
        ),
        TaskProfile(
            title="调研向量库 → 写对比报告 → 独立审校",
            distinct_roles=True,
            handoff_chain=True,
            adversarial_review=True,
            specialty_toolsets=True,
        ),
        TaskProfile(
            title="客服 FAQ 单轮问答",
            single_skill_loop=True,
            tight_latency=True,
        ),
        TaskProfile(
            title="代码生成后由安全审计员挑刺",
            distinct_roles=True,
            adversarial_review=True,
            specialty_toolsets=True,
        ),
        TaskProfile(
            title="想拆很多 Agent 但说不清各自职责",
            blurry_roles=True,
            parallel_workstreams=True,
            cost_sensitive=True,
        ),
        TaskProfile(
            title="可并行搜集资料但成本敏感、尚无专职角色",
            parallel_workstreams=True,
            specialty_toolsets=True,
            cost_sensitive=True,
        ),
    )


def build_demo_decisions() -> tuple[Decision, ...]:
    """对演示画像逐条 decide。"""
    return tuple(decide(p) for p in build_demo_profiles())


def render_decision_report(decisions: Sequence[Decision] | None = None) -> str:
    """学习报告（含规定二级标题）。"""
    items = list(decisions) if decisions is not None else list(build_demo_decisions())
    if not items:
        raise ValueError("decisions must be non-empty")

    counts = {
        REC_USE_MULTI: 0,
        REC_KEEP_SINGLE: 0,
        REC_DEFER: 0,
    }
    for d in items:
        counts[d.recommendation] += 1

    lines: list[str] = [
        "# Day 71 学习报告｜何时用多智能体",
        "",
        "## 何为多智能体决策",
        "多智能体不是「人多力量大」，而是：**角色边界清晰且交接有价值**时，才值得付协调税。",
        "今天用可运行清单，把「感觉该拆」变成「信号 → 得分 → 推荐」。",
        "",
        "## 适用信号与不适用信号",
        "适用（Pro）：专职角色、流水线交接、可并行、对立审校、异构工具集。",
        "不适用（Con）：单技能循环、延迟紧、成本紧、角色模糊、重共享可变状态。",
        "",
        "## 决策规则",
        "先走否决（角色模糊 / 纯单技能），再看正信号数量与 score，最后才 defer。",
        f"采用阈值：正信号 ≥ {USE_MULTI_MIN_POSITIVES} 且 score ≥ {USE_MULTI_MIN_SCORE}。",
        "",
        "## 今日演示统计",
        f"- 场景数：{len(items)}",
        f"- use_multi：{counts[REC_USE_MULTI]}",
        f"- keep_single：{counts[REC_KEEP_SINGLE]}",
        f"- defer：{counts[REC_DEFER]}",
        "",
    ]
    for d in items:
        sm = summarize_decision(d)
        lines.append(
            f"- {sm['title']}: `{sm['recommendation']}` (score={sm['score']})"
        )

    lines.extend(
        [
            "",
            "## 明日预告",
            "Day 72 将动手搭流水线双 Agent：Researcher → Writer，把「适用」落地成可跑协作。",
            "",
        ]
    )

    report = "\n".join(lines)
    for section in REQUIRED_REPORT_SECTIONS:
        heading = f"## {section}"
        if heading not in report:
            raise RuntimeError(f"missing report section: {section}")
    return report
