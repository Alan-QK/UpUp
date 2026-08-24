"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

from dataclasses import dataclass
import re


STRATEGY_DIRECT = "direct"
STRATEGY_COT = "cot"
ALLOWED_STRATEGIES = frozenset({STRATEGY_DIRECT, STRATEGY_COT})

ANSWER_MARKER = "最终答案："

DIRECT_SYSTEM = (
    "你是严谨的解题助手。只给出最终结论，不要解释过程。"
    f"最后一行必须是：{ANSWER_MARKER}<答案>"
)

COT_SYSTEM = (
    "你是严谨的解题助手。先分步骤推理（每步单独一行，"
    "形如「1. ...」「2. ...」），再给出结论。"
    f"最后一行必须是：{ANSWER_MARKER}<答案>"
)

# 允许「1. 步骤」或「3、步骤」（顿号后可无空格）
_STEP_LINE_RE = re.compile(
    r"^\s*(?:\(?\d+\)?[.、)]|\d+[\.、)])\s*\S+"
)


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。"""
    return " ".join(text.split())


def normalize_strategy(strategy: str) -> str:
    """规范化策略名。"""
    normalized = strategy.strip().lower()
    if normalized not in ALLOWED_STRATEGIES:
        raise ValueError("strategy must be 'direct' or 'cot'")
    return normalized


def normalize_answer(answer: str) -> str:
    """规范化答案以便比较。"""
    return normalize_text(answer).lower()


@dataclass(frozen=True)
class ReasoningTask:
    """一道可离线评测的推理题。"""

    question: str
    expected_answer: str
    case_id: str = "default"


@dataclass(frozen=True)
class RunResult:
    """某一种策略的一次运行结果。"""

    strategy: str
    raw_output: str
    extracted_answer: str
    step_count: int
    correct: bool


@dataclass(frozen=True)
class CompareReport:
    """Direct vs CoT 的对比报告。"""

    task: ReasoningTask
    direct: RunResult
    cot: RunResult

    @property
    def cot_helped(self) -> bool:
        """Direct 错且 CoT 对。"""
        return (not self.direct.correct) and self.cot.correct

    @property
    def cot_hurt(self) -> bool:
        """Direct 对且 CoT 错。"""
        return self.direct.correct and (not self.cot.correct)


def build_system_prompt(strategy: str) -> str:
    """按策略返回 system 文本。"""
    key = normalize_strategy(strategy)
    if key == STRATEGY_DIRECT:
        return DIRECT_SYSTEM
    return COT_SYSTEM


def build_user_prompt(question: str) -> str:
    """渲染 user 正文。"""
    normalized = normalize_text(question)
    if not normalized:
        raise ValueError("question must not be empty")
    return f"【题目】\n{normalized}"


def build_messages(strategy: str, question: str) -> list[dict[str, str]]:
    """组装 OpenAI 风格 messages。"""
    return [
        {"role": "system", "content": build_system_prompt(strategy)},
        {"role": "user", "content": build_user_prompt(question)},
    ]


def extract_final_answer(text: str) -> str:
    """从模型输出中抽取最终答案。"""
    if not text.strip():
        raise ValueError("output is empty")

    idx = text.rfind(ANSWER_MARKER)
    if idx < 0:
        raise ValueError("missing 最终答案 marker")

    after = text[idx + len(ANSWER_MARKER) :]
    # 只取标记所在行剩余部分
    line_rest = after.splitlines()[0] if after else ""
    answer = line_rest.strip()
    if not answer:
        raise ValueError("最终答案 is empty")
    return answer


def count_reasoning_steps(text: str) -> int:
    """统计最终答案标记之前的步骤行数。"""
    cut = text.find(ANSWER_MARKER)
    head = text if cut < 0 else text[:cut]
    count = 0
    for line in head.splitlines():
        if _STEP_LINE_RE.match(line):
            count += 1
    return count


def evaluate_run(
    strategy: str,
    raw_output: str,
    expected_answer: str,
) -> RunResult:
    """评测单次输出。"""
    key = normalize_strategy(strategy)
    extracted = extract_final_answer(raw_output)
    steps = count_reasoning_steps(raw_output)
    correct = normalize_answer(extracted) == normalize_answer(expected_answer)
    return RunResult(
        strategy=key,
        raw_output=raw_output,
        extracted_answer=extracted,
        step_count=steps,
        correct=correct,
    )


def compare_outputs(
    task: ReasoningTask,
    direct_output: str,
    cot_output: str,
) -> CompareReport:
    """对比同一题目下 Direct / CoT 两次输出。"""
    direct = evaluate_run(STRATEGY_DIRECT, direct_output, task.expected_answer)
    cot = evaluate_run(STRATEGY_COT, cot_output, task.expected_answer)
    return CompareReport(task=task, direct=direct, cot=cot)


def render_report(report: CompareReport) -> str:
    """把对比报告渲染成可读多行文本。"""
    if report.cot_helped:
        verdict = "helped"
    elif report.cot_hurt:
        verdict = "hurt"
    else:
        verdict = "tie"

    lines = [
        f"case: {report.task.case_id}",
        f"question: {normalize_text(report.task.question)}",
        f"expected: {report.task.expected_answer.strip()}",
        (
            f"direct: correct={report.direct.correct} "
            f"steps={report.direct.step_count} "
            f"answer={report.direct.extracted_answer}"
        ),
        (
            f"cot: correct={report.cot.correct} "
            f"steps={report.cot.step_count} "
            f"answer={report.cot.extracted_answer}"
        ),
        f"verdict: {verdict}",
    ]
    return "\n".join(lines)
