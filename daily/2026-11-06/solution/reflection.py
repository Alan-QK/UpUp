"""Day 68 参考实现：Reflection 反思纠错（critic 轮）。

吃进执行轨迹快照，启发式打分后决定 accept / retry / revise / abort。
RETRY 时模拟改善最差一步；不调用 LLM，结构与生产 critic 一致。
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
    if not isinstance(step, StepSnapshot):
        raise TypeError("step must be StepSnapshot")

    issues: list[str] = []

    if step.status == STATUS_FAILED:
        issues.append(ISSUE_FAILED_STATUS)
        if step.error.strip():
            issues.append(ISSUE_HAS_ERROR)
        return 0.0, tuple(issues)

    if step.status == STATUS_SKIPPED:
        issues.append(ISSUE_SKIPPED_STATUS)
        return 0.25, tuple(issues)

    if step.status == STATUS_PENDING:
        issues.append(ISSUE_PENDING_STATUS)
        return 0.2, tuple(issues)

    # done
    obs = step.observation.strip()
    if step.error.strip():
        issues.append(ISSUE_HAS_ERROR)
    if not obs:
        issues.append(ISSUE_EMPTY_OBS)
        return 0.15, tuple(issues)
    if len(obs) < MIN_OBS_LEN:
        issues.append(ISSUE_TOO_SHORT)
        score = 0.45 if not step.error.strip() else 0.35
        return score, tuple(issues)

    score = 0.95 if not step.error.strip() else 0.75
    return score, tuple(issues)


def critique_step(step: StepSnapshot) -> Critique:
    """评审单步，给出决策。"""
    score, issues = score_step(step)

    if score >= PASS_SCORE and not issues:
        return Critique(
            target=step.step_id,
            score=score,
            issues=issues,
            decision=DECISION_ACCEPT,
            rationale=f"{step.step_id} 观察合格，接受。",
        )

    if score >= PASS_SCORE:
        # 有轻微问题但仍过线
        return Critique(
            target=step.step_id,
            score=score,
            issues=issues,
            decision=DECISION_ACCEPT,
            rationale=f"{step.step_id} 分数过线（{score:.2f}），带告警接受。",
        )

    if ISSUE_SKIPPED_STATUS in issues:
        return Critique(
            target=step.step_id,
            score=score,
            issues=issues,
            decision=DECISION_REVISE,
            rationale=f"{step.step_id} 被跳过，应回到计划层调整依赖/步骤。",
            retry_hint="",
        )

    # failed / pending / empty / too_short → retry
    hint = "补充更具体的观察，清除临时错误后重试。"
    if ISSUE_PENDING_STATUS in issues:
        hint = "上游已修复，补跑本步骤并写出完整观察。"
    elif ISSUE_FAILED_STATUS in issues:
        hint = f"排查工具错误后重试：{step.error or 'unknown error'}"
    elif ISSUE_EMPTY_OBS in issues:
        hint = "观察为空，换检索词或扩大上下文后重试。"
    elif ISSUE_TOO_SHORT in issues:
        hint = f"观察过短（<{MIN_OBS_LEN}），要求输出关键要点后重试。"

    return Critique(
        target=step.step_id,
        score=score,
        issues=issues,
        decision=DECISION_RETRY,
        rationale=f"{step.step_id} 质量不足（{score:.2f}），建议重试。",
        retry_hint=hint,
    )


def critique_run(run: RunSnapshot) -> Critique:
    """评审整次运行。"""
    if not isinstance(run, RunSnapshot):
        raise TypeError("run must be RunSnapshot")

    issues: list[str] = []
    skipped = sum(1 for s in run.steps if s.status == STATUS_SKIPPED)
    failed = sum(1 for s in run.steps if s.status == STATUS_FAILED)
    done = sum(1 for s in run.steps if s.status == STATUS_DONE)

    if run.stop_reason == STOP_FAILED:
        issues.append(ISSUE_STOP_FAILED)
    if run.stop_reason == STOP_BLOCKED:
        issues.append(ISSUE_STOP_BLOCKED)
    if skipped >= 2 and failed >= 1:
        issues.append(ISSUE_CASCADE_SKIP)
    if not run.has_deliverable:
        # 仅当计划里看起来需要交付（最后一步 kind/title 含 deliver 或存在 skipped/failed）
        last = run.steps[-1]
        if last.kind == "deliver" or "交付" in last.title or last.status != STATUS_DONE:
            issues.append(ISSUE_NO_DELIVERABLE)

    # 聚合步骤分
    step_scores = [score_step(s)[0] for s in run.steps]
    avg = sum(step_scores) / len(step_scores)

    if (
        run.stop_reason == STOP_COMPLETED
        and run.has_deliverable
        and failed == 0
        and skipped == 0
        and avg >= PASS_SCORE
    ):
        return Critique(
            target="run",
            score=min(1.0, avg),
            issues=tuple(issues),
            decision=DECISION_ACCEPT,
            rationale="运行完整完成且交付物就绪，接受。",
        )

    if ISSUE_CASCADE_SKIP in issues or (
        run.stop_reason in {STOP_FAILED, STOP_BLOCKED} and skipped >= 2
    ):
        return Critique(
            target="run",
            score=min(avg, 0.3),
            issues=tuple(issues),
            decision=DECISION_REVISE,
            rationale="出现级联跳过，计划或依赖需调整，而非单步重试。",
        )

    if failed or avg < PASS_SCORE or ISSUE_NO_DELIVERABLE in issues:
        return Critique(
            target="run",
            score=avg,
            issues=tuple(issues),
            decision=DECISION_RETRY,
            rationale="运行未达质量门禁，优先重试薄弱步骤。",
            retry_hint="从分数最低的可重试步骤开始。",
        )

    return Critique(
        target="run",
        score=avg,
        issues=tuple(issues),
        decision=DECISION_ACCEPT,
        rationale=f"整体可接受（done={done}, avg={avg:.2f}）。",
    )


def pick_overall_decision(critiques: Sequence[Critique]) -> str:
    """按优先级合并多条评审：abort > revise > retry > accept。"""
    if not critiques:
        raise ValueError("critiques must be non-empty")
    best = DECISION_ACCEPT
    best_p = DECISION_PRIORITY[best]
    for c in critiques:
        if not isinstance(c, Critique):
            raise TypeError("critiques must contain Critique")
        p = DECISION_PRIORITY[c.decision]
        if p > best_p:
            best = c.decision
            best_p = p
    return best


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
    if not isinstance(step, StepSnapshot):
        raise TypeError("step must be StepSnapshot")
    obs = _improved_observation(step)
    if hint.strip():
        obs = f"{obs}（提示：{hint.strip()}）"
    return StepSnapshot(
        step_id=step.step_id,
        title=step.title,
        kind=step.kind,
        status=STATUS_DONE,
        observation=obs,
        error="",
    )


def find_retry_targets(critiques: Sequence[Critique], run: RunSnapshot) -> list[str]:
    """收集 decision=retry 且状态允许重试的 step_id（按分数升序）。"""
    by_id = {s.step_id: s for s in run.steps}
    candidates: list[tuple[float, str]] = []
    for c in critiques:
        if c.decision != DECISION_RETRY:
            continue
        if c.target == "run":
            continue
        if c.target not in by_id:
            continue
        step = by_id[c.target]
        # skipped 应由 revise 处理，不进 retry 列表
        if step.status == STATUS_SKIPPED:
            continue
        candidates.append((c.score, c.target))
    candidates.sort(key=lambda x: (x[0], x[1]))
    # 去重且保序
    seen: set[str] = set()
    ordered: list[str] = []
    for _, sid in candidates:
        if sid not in seen:
            seen.add(sid)
            ordered.append(sid)
    return ordered


def find_retry_target(critiques: Sequence[Critique], run: RunSnapshot) -> str | None:
    """兼容接口：返回分数最低的可重试 step_id。"""
    targets = find_retry_targets(critiques, run)
    return targets[0] if targets else None


def apply_retry(run: RunSnapshot, critiques: Sequence[Critique]) -> RunSnapshot:
    """对本轮所有可重试步骤执行 improve_step，并刷新 stop_reason / deliverable。"""
    if not isinstance(run, RunSnapshot):
        raise TypeError("run must be RunSnapshot")

    targets = find_retry_targets(critiques, run)
    if not targets:
        return run

    hints = {c.target: c.retry_hint for c in critiques if c.target in targets}
    target_set = set(targets)

    new_steps: list[StepSnapshot] = []
    for step in run.steps:
        if step.step_id in target_set:
            new_steps.append(improve_step(step, hint=hints.get(step.step_id, "")))
        else:
            new_steps.append(step)

    has_deliverable = run.has_deliverable
    for s in new_steps:
        if s.kind == "deliver" and s.status == STATUS_DONE:
            has_deliverable = True
        if "交付物" in s.observation:
            has_deliverable = True

    failed = any(s.status == STATUS_FAILED for s in new_steps)
    skipped = any(s.status == STATUS_SKIPPED for s in new_steps)
    pending = any(s.status == STATUS_PENDING for s in new_steps)
    if failed:
        stop = STOP_FAILED
    elif pending or skipped:
        stop = STOP_BLOCKED
    else:
        stop = STOP_COMPLETED

    return RunSnapshot(
        goal=run.goal,
        stop_reason=stop,
        steps=tuple(new_steps),
        has_deliverable=has_deliverable,
    )


def run_reflection(
    run: RunSnapshot,
    *,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
) -> ReflectionResult:
    """执行反思循环。

    规则：
    1. 每轮对所有 step + run 做 critique，再 pick_overall_decision
    2. accept / revise → 记录本轮后结束
    3. retry → apply_retry，retries_used+=1，进入下一轮
    4. 若决策为 retry 但找不到目标 → 升级为 revise
    5. 超过 max_rounds 仍未 accept/revise → final_decision=abort
    """
    if not isinstance(run, RunSnapshot):
        raise TypeError("run must be RunSnapshot")
    if not isinstance(max_rounds, int) or isinstance(max_rounds, bool):
        raise TypeError("max_rounds must be int")
    if max_rounds < 1:
        raise ValueError("max_rounds must be >= 1")

    result = ReflectionResult(initial=run, final_run=run)
    current = run

    for i in range(1, max_rounds + 1):
        step_critiques = tuple(critique_step(s) for s in current.steps)
        run_critique = critique_run(current)
        critiques = step_critiques + (run_critique,)
        decision = pick_overall_decision(critiques)

        if decision == DECISION_RETRY:
            target = find_retry_target(critiques, current)
            if target is None:
                decision = DECISION_REVISE
                critiques = step_critiques + (
                    Critique(
                        target="run",
                        score=run_critique.score,
                        issues=run_critique.issues + (ISSUE_CASCADE_SKIP,),
                        decision=DECISION_REVISE,
                        rationale="需要重试但无可修步骤（多为 skipped），改为 revise。",
                    ),
                )

        if decision == DECISION_RETRY:
            # 已无剩余轮次可验证重试结果 → 升级 abort（本轮不 apply）
            if i >= max_rounds:
                abort_critique = Critique(
                    target="run",
                    score=0.0,
                    issues=(ISSUE_STOP_FAILED,),
                    decision=DECISION_ABORT,
                    rationale=f"仍需重试但已达 max_rounds={max_rounds}，中止。",
                )
                result.rounds.append(
                    ReflectionRound(
                        round_index=i,
                        critiques=critiques + (abort_critique,),
                        decision=DECISION_ABORT,
                        run=current,
                    )
                )
                result.final_run = current
                result.final_decision = DECISION_ABORT
                return result

            current = apply_retry(current, critiques)
            result.retries_used += 1
            result.rounds.append(
                ReflectionRound(
                    round_index=i,
                    critiques=critiques,
                    decision=DECISION_RETRY,
                    run=current,
                )
            )
            continue

        # accept / revise / abort
        result.rounds.append(
            ReflectionRound(
                round_index=i,
                critiques=critiques,
                decision=decision,
                run=current,
            )
        )
        result.final_run = current
        result.final_decision = decision
        return result

    result.final_run = current
    result.final_decision = DECISION_ABORT
    return result


def summarize_reflection(result: ReflectionResult) -> dict[str, object]:
    """汇总反思结果。"""
    if not isinstance(result, ReflectionResult):
        raise TypeError("result must be ReflectionResult")
    return {
        "goal": result.initial.goal,
        "final_decision": result.final_decision,
        "rounds": len(result.rounds),
        "retries_used": result.retries_used,
        "initial_stop": result.initial.stop_reason,
        "final_stop": result.final_run.stop_reason if result.final_run else None,
        "final_has_deliverable": (
            result.final_run.has_deliverable if result.final_run else False
        ),
    }


def render_reflection(result: ReflectionResult) -> str:
    """把反思轨迹渲染成 Markdown。"""
    if not isinstance(result, ReflectionResult):
        raise TypeError("result must be ReflectionResult")
    lines = [
        f"# 反思轨迹：{result.initial.goal}",
        "",
        f"- 最终决策：`{result.final_decision}`",
        f"- 轮次：{len(result.rounds)}",
        f"- 重试次数：{result.retries_used}",
        "",
    ]
    for rnd in result.rounds:
        lines.append(f"## Round {rnd.round_index} → `{rnd.decision}`")
        lines.append("")
        for c in rnd.critiques:
            issues = ",".join(c.issues) if c.issues else "—"
            lines.append(
                f"- **{c.target}** score={c.score:.2f} decision=`{c.decision}` "
                f"issues={issues}"
            )
            lines.append(f"  - {c.rationale}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_sample_good_run() -> RunSnapshot:
    """优质完整轨迹。"""
    return RunSnapshot(
        goal="调研向量数据库选型",
        stop_reason=STOP_COMPLETED,
        has_deliverable=True,
        steps=(
            StepSnapshot(
                "S1",
                "澄清调研范围",
                "clarify",
                STATUS_DONE,
                "已澄清目标：「调研向量数据库选型」。范围：对比适用场景。",
            ),
            StepSnapshot(
                "S2",
                "收集资料",
                "research",
                STATUS_DONE,
                "笔记#1：背景摘要；笔记#2：与收集资料相关的要点。",
            ),
            StepSnapshot(
                "S3",
                "交叉比对",
                "analyze",
                STATUS_DONE,
                "分析完成：基于 2 条笔记，聚焦「交叉比对」。",
            ),
            StepSnapshot(
                "S4",
                "形成结论",
                "deliver",
                STATUS_DONE,
                "已写入交付物（128 字符）",
            ),
        ),
    )


def build_sample_weak_run() -> RunSnapshot:
    """观察过短 / 空洞，但状态为 done。"""
    return RunSnapshot(
        goal="写一份记忆系统设计文档",
        stop_reason=STOP_COMPLETED,
        has_deliverable=False,
        steps=(
            StepSnapshot("S1", "澄清", "clarify", STATUS_DONE, "ok"),
            StepSnapshot("S2", "检索", "research", STATUS_DONE, "短"),
            StepSnapshot(
                "S3",
                "交付",
                "deliver",
                STATUS_DONE,
                "草稿",
            ),
        ),
    )


def build_sample_failed_run() -> RunSnapshot:
    """中途失败并级联跳过。"""
    return RunSnapshot(
        goal="实现带重试的 HTTP 客户端",
        stop_reason=STOP_FAILED,
        has_deliverable=False,
        steps=(
            StepSnapshot(
                "S1",
                "澄清范围",
                "clarify",
                STATUS_DONE,
                "已澄清目标：「实现带重试的 HTTP 客户端」。范围：超时与退避。",
            ),
            StepSnapshot(
                "S2",
                "检索资料",
                "research",
                STATUS_FAILED,
                "",
                "RuntimeError: simulated tool failure",
            ),
            StepSnapshot(
                "S3",
                "分析方案",
                "analyze",
                STATUS_SKIPPED,
                "",
                "dependencies not satisfied",
            ),
            StepSnapshot(
                "S4",
                "写出交付",
                "deliver",
                STATUS_SKIPPED,
                "",
                "stopped before reach",
            ),
        ),
    )


def build_demo_runs() -> list[RunSnapshot]:
    """至少 3 份不同情景的演示轨迹。"""
    return [
        build_sample_good_run(),
        build_sample_weak_run(),
        build_sample_failed_run(),
    ]


def run_demo_reflection(
    runs: Sequence[RunSnapshot] | None = None,
    *,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
) -> list[ReflectionResult]:
    """批量反思演示。"""
    items = list(runs) if runs is not None else build_demo_runs()
    return [run_reflection(r, max_rounds=max_rounds) for r in items]


def render_reflection_report(
    results: Sequence[ReflectionResult] | None = None,
) -> str:
    """生成含固定二级标题的学习报告。"""
    if results is None:
        results = run_demo_reflection()
    accepts = sum(1 for r in results if r.final_decision == DECISION_ACCEPT)
    revises = sum(1 for r in results if r.final_decision == DECISION_REVISE)
    aborts = sum(1 for r in results if r.final_decision == DECISION_ABORT)
    retries = sum(r.retries_used for r in results)
    sample = results[0] if results else None
    sample_md = render_reflection(sample) if sample else "_（无结果）_"

    lines = [
        "# Day 68 报告｜Reflection 反思纠错",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[0]}",
        "",
        "Reflection = 在执行轨迹之上增加 **critic 轮**：打分、列问题、做决策。",
        "它不替代 Planner / Executor，只负责「要不要认、要不要再试、要不要改计划」。",
        "今日用启发式 mock；生产可换成第二个模型输出同样的结构化 Critique。",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[1]}",
        "",
        "四态：`accept` / `retry` / `revise` / `abort`。",
        "合并优先级：**abort > revise > retry > accept**。",
        "`skipped` 倾向 revise；空/短观察倾向 retry；轮次耗尽 → abort。",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[2]}",
        "",
        f"- 轨迹数：{len(results)}",
        f"- accept：{accepts} · revise：{revises} · abort：{aborts}",
        f"- 累计 retries_used：{retries}",
        "",
        "### 样例轨迹",
        "",
        sample_md,
        f"## {REQUIRED_REPORT_SECTIONS[3]}",
        "",
        "明日会把 Plan / Execute / Reflect / HITL 收成状态机：",
        "每个决策对应一条转移，避免「if-else 糊成一团」。",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[4]}",
        "",
        "Day 69｜状态机视角：画出 Agent 状态图。",
        "",
    ]
    return "\n".join(lines)
