"""Day 68 练习：Reflection 反思纠错（critic 轮）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——不调用 LLM。

提示：
- StepSnapshot / RunSnapshot / Critique 已给齐，今日主要写决策与循环
- 先实现 score_step / critique_* / pick_overall_decision
- 再实现 improve / apply_retry / run_reflection
- 最后做 sample / demo / render / report
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

# --- 决策 ---

DECISION_ACCEPT = "accept"
DECISION_RETRY = "retry"
DECISION_REVISE = "revise"
DECISION_ABORT = "abort"
VALID_DECISIONS = frozenset(
    {
        DECISION_ACCEPT,
        DECISION_RETRY,
        DECISION_REVISE,
        DECISION_ABORT,
    }
)

# 合并优先级：数字越大越优先
DECISION_PRIORITY: dict[str, int] = {
    DECISION_ACCEPT: 0,
    DECISION_RETRY: 1,
    DECISION_REVISE: 2,
    DECISION_ABORT: 3,
}

# --- 执行状态字面量（与 Day67 对齐，今日只读） ---

STATUS_DONE = "done"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"
STATUS_PENDING = "pending"
VALID_STATUSES = frozenset(
    {STATUS_DONE, STATUS_FAILED, STATUS_SKIPPED, STATUS_PENDING}
)

STOP_COMPLETED = "completed"
STOP_FAILED = "failed"
STOP_BLOCKED = "blocked"
STOP_MAX_STEPS = "max_steps"
VALID_STOP_REASONS = frozenset(
    {STOP_COMPLETED, STOP_FAILED, STOP_BLOCKED, STOP_MAX_STEPS}
)

# --- issue 标签 ---

ISSUE_EMPTY_OBS = "empty_observation"
ISSUE_TOO_SHORT = "too_short"
ISSUE_HAS_ERROR = "has_error"
ISSUE_FAILED_STATUS = "failed_status"
ISSUE_SKIPPED_STATUS = "skipped_status"
ISSUE_PENDING_STATUS = "pending_status"
ISSUE_NO_DELIVERABLE = "no_deliverable"
ISSUE_STOP_FAILED = "stop_failed"
ISSUE_STOP_BLOCKED = "stop_blocked"
ISSUE_CASCADE_SKIP = "cascade_skip"

PASS_SCORE = 0.7
MIN_OBS_LEN = 12
DEFAULT_MAX_ROUNDS = 3

REQUIRED_REPORT_SECTIONS = (
    "何为 Reflection",
    "四态决策与优先级",
    "今日演示统计",
    "与状态机衔接",
    "明日预告",
)


@dataclass(frozen=True)
class StepSnapshot:
    """单步执行快照（只读输入）。"""

    step_id: str
    title: str
    kind: str
    status: str
    observation: str = ""
    error: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.step_id, str) or not self.step_id.strip():
            raise ValueError("step_id must be non-empty str")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be non-empty str")
        if not isinstance(self.kind, str) or not self.kind.strip():
            raise ValueError("kind must be non-empty str")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"invalid status: {self.status}")
        if not isinstance(self.observation, str):
            raise TypeError("observation must be str")
        if not isinstance(self.error, str):
            raise TypeError("error must be str")


@dataclass(frozen=True)
class RunSnapshot:
    """一次完整执行的轨迹快照。"""

    goal: str
    stop_reason: str
    steps: tuple[StepSnapshot, ...]
    has_deliverable: bool

    def __post_init__(self) -> None:
        if not isinstance(self.goal, str) or not self.goal.strip():
            raise ValueError("goal must be non-empty str")
        if self.stop_reason not in VALID_STOP_REASONS:
            raise ValueError(f"invalid stop_reason: {self.stop_reason}")
        if not isinstance(self.steps, tuple) or not self.steps:
            raise ValueError("steps must be non-empty tuple")
        if not isinstance(self.has_deliverable, bool):
            raise TypeError("has_deliverable must be bool")
        ids = [s.step_id for s in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("step ids must be unique")


@dataclass(frozen=True)
class Critique:
    """一条评审意见。"""

    target: str  # step_id 或 "run"
    score: float
    issues: tuple[str, ...]
    decision: str
    rationale: str
    retry_hint: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.target, str) or not self.target.strip():
            raise ValueError("target must be non-empty str")
        if not isinstance(self.score, (int, float)) or isinstance(self.score, bool):
            raise TypeError("score must be number")
        if not 0.0 <= float(self.score) <= 1.0:
            raise ValueError("score out of range")
        if not isinstance(self.issues, tuple):
            raise TypeError("issues must be tuple")
        if self.decision not in VALID_DECISIONS:
            raise ValueError(f"invalid decision: {self.decision}")
        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise ValueError("rationale must be non-empty str")
        if not isinstance(self.retry_hint, str):
            raise TypeError("retry_hint must be str")


@dataclass(frozen=True)
class ReflectionRound:
    """反思循环中的一轮。"""

    round_index: int
    critiques: tuple[Critique, ...]
    decision: str
    run: RunSnapshot

    def __post_init__(self) -> None:
        if not isinstance(self.round_index, int) or isinstance(self.round_index, bool):
            raise TypeError("round_index must be int")
        if self.round_index < 1:
            raise ValueError("round_index must be >= 1")
        if not isinstance(self.critiques, tuple) or not self.critiques:
            raise ValueError("critiques must be non-empty tuple")
        if self.decision not in VALID_DECISIONS:
            raise ValueError(f"invalid decision: {self.decision}")
        if not isinstance(self.run, RunSnapshot):
            raise TypeError("run must be RunSnapshot")


@dataclass
class ReflectionResult:
    """整次反思的结果。"""

    initial: RunSnapshot
    rounds: list[ReflectionRound] = field(default_factory=list)
    final_run: RunSnapshot | None = None
    final_decision: str = DECISION_ABORT
    retries_used: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.initial, RunSnapshot):
            raise TypeError("initial must be RunSnapshot")
        if self.final_decision not in VALID_DECISIONS:
            raise ValueError(f"invalid final_decision: {self.final_decision}")
        if not isinstance(self.retries_used, int) or isinstance(self.retries_used, bool):
            raise TypeError("retries_used must be int")
        if self.retries_used < 0:
            raise ValueError("retries_used must be >= 0")


def score_step(step: StepSnapshot) -> tuple[float, tuple[str, ...]]:
    """对单步打分，返回 (score, issues)。"""
    # TODO: 按 status / observation / error 打分并收集 issues
    raise NotImplementedError

def critique_step(step: StepSnapshot) -> Critique:
    """评审单步，给出决策。"""
    # TODO: 调 score_step；skipped→revise；低分→retry；过线→accept
    raise NotImplementedError

def critique_run(run: RunSnapshot) -> Critique:
    """评审整次运行。"""
    # TODO: 看 stop_reason、级联 skipped、交付物、平均分
    raise NotImplementedError

def pick_overall_decision(critiques: Sequence[Critique]) -> str:
    """按优先级合并多条评审：abort > revise > retry > accept。"""
    # TODO
    raise NotImplementedError

def _improved_observation(step: StepSnapshot) -> str:
    """生成模拟重试后的合格观察。"""
    base = (
        f"【重试成功】步骤「{step.title}」（{step.kind}）已补全："
        f"针对目标产出了可核对要点与下一步建议。"
    )
    if step.kind == "research":
        return base + "检索命中 3 条笔记并完成去重。"
    if step.kind == "analyze":
        return base + "交叉比对完成，列出异同与风险。"
    if step.kind == "deliver":
        return base + "交付物已写入共享黑板。"
    if step.kind == "clarify":
        return base + "范围、受众与成功标准已对齐。"
    return base + "主路径观察已满足长度与信息量门槛。"


def improve_step(step: StepSnapshot, *, hint: str = "") -> StepSnapshot:
    """模拟对单步的成功重试：清错误、置 done、写合格观察。"""
    # TODO: 可用 _improved_observation
    raise NotImplementedError

def find_retry_targets(critiques: Sequence[Critique], run: RunSnapshot) -> list[str]:
    """收集 decision=retry 且状态允许重试的 step_id（按分数升序）。"""
    # TODO: 跳过 target=run 与 status=skipped
    raise NotImplementedError

def find_retry_target(critiques: Sequence[Critique], run: RunSnapshot) -> str | None:
    """兼容接口：返回分数最低的可重试 step_id。"""
    # TODO: 复用 find_retry_targets
    raise NotImplementedError

def apply_retry(run: RunSnapshot, critiques: Sequence[Critique]) -> RunSnapshot:
    """对本轮所有可重试步骤执行 improve_step，并刷新 stop_reason / deliverable。"""
    # TODO
    raise NotImplementedError

def run_reflection(
    run: RunSnapshot,
    *,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
) -> ReflectionResult:
    """执行反思循环。

    规则：
    1. 每轮对所有 step + run 做 critique，再 pick_overall_decision
    2. accept / revise → 记录本轮后结束
    3. retry 且还有剩余轮次 → apply_retry，retries_used+=1
    4. retry 但找不到目标 → 升级为 revise
    5. 仍需 retry 但已是最后一轮 → abort（不 apply）
    """
    # TODO
    raise NotImplementedError

def summarize_reflection(result: ReflectionResult) -> dict[str, object]:
    """汇总反思结果。"""
    # TODO: goal / final_decision / rounds / retries_used / initial_stop / final_stop / final_has_deliverable
    raise NotImplementedError

def render_reflection(result: ReflectionResult) -> str:
    """把反思轨迹渲染成 Markdown。"""
    # TODO
    raise NotImplementedError

def build_sample_good_run() -> RunSnapshot:
    """优质完整轨迹。"""
    # TODO
    raise NotImplementedError

def build_sample_weak_run() -> RunSnapshot:
    """观察过短 / 空洞，但状态为 done。"""
    # TODO
    raise NotImplementedError

def build_sample_failed_run() -> RunSnapshot:
    """中途失败并级联跳过。"""
    # TODO
    raise NotImplementedError

def build_demo_runs() -> list[RunSnapshot]:
    """至少 3 份不同情景的演示轨迹。"""
    # TODO
    raise NotImplementedError

def run_demo_reflection(
    runs: Sequence[RunSnapshot] | None = None,
    *,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
) -> list[ReflectionResult]:
    """批量反思演示。"""
    # TODO
    raise NotImplementedError

def render_reflection_report(
    results: Sequence[ReflectionResult] | None = None,
) -> str:
    """生成含固定二级标题的学习报告。"""
    # TODO: 必须包含 REQUIRED_REPORT_SECTIONS 中每个标题（作 ## 二级标题）
    raise NotImplementedError

