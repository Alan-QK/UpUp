"""Day 23 练习：CoT 与直接回答对比实验。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库。
"""

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

# 匹配步骤行：1. / 1、 / 1) 等；顿号后可无空格（如「3、第三步」）
_STEP_LINE_RE = re.compile(
    r"^\s*(?:\(?\d+\)?[.、)]|\d+[\.、)])\s*\S+"
)


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。

    例：\"  你好\\n\\n世界  \" → \"你好 世界\"
    """
    # TODO: 实现空白规范化
    raise NotImplementedError


def normalize_strategy(strategy: str) -> str:
    """规范化策略名。

    - strip + lower
    - 结果必须属于 ALLOWED_STRATEGIES，否则 ValueError（消息含 \"strategy\"）
    """
    # TODO: 实现策略规范化
    raise NotImplementedError


def normalize_answer(answer: str) -> str:
    """规范化答案以便比较：normalize_text 后再 lower。"""
    # TODO: 实现答案规范化
    raise NotImplementedError


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
    """按策略返回 system 文本（使用上方 DIRECT_SYSTEM / COT_SYSTEM 常量）。"""
    # TODO: normalize_strategy 后返回对应常量
    raise NotImplementedError


def build_user_prompt(question: str) -> str:
    """渲染 user 正文：【题目】\\n<规范化后的题目>。

    题目 normalize_text 后为空则 ValueError（消息含 \"question\"）。
    """
    # TODO: 实现 user 渲染
    raise NotImplementedError


def build_messages(strategy: str, question: str) -> list[dict[str, str]]:
    """组装 OpenAI 风格 messages：system + user。"""
    # TODO: 调用 build_system_prompt / build_user_prompt
    raise NotImplementedError


def extract_final_answer(text: str) -> str:
    """从模型输出中抽取最终答案。

    规则：
    - 在全文找最后一次出现的 ANSWER_MARKER
    - 取该标记所在行、标记之后的文本，strip 后作为答案
    - 若标记不存在，或标记后答案为空 → ValueError（消息含 \"最终答案\"）
    - 输入整体 normalize 前若为空字符串（strip 后空）→ ValueError（含 \"empty\"）
    """
    # TODO: 实现答案抽取
    raise NotImplementedError


def count_reasoning_steps(text: str) -> int:
    """统计「最终答案」标记之前，有多少像步骤的行。

    - 若存在 ANSWER_MARKER，只统计标记首次出现位置之前的行
      （注意：步骤计数用「首次」截断，避免把答案行后的噪声算进去；
       答案抽取仍用「最后一次」标记，两者目的不同）
    - 若无标记，统计全部非空行中的步骤行
    - 步骤行定义：匹配模块顶部的 _STEP_LINE_RE
    """
    # TODO: 实现步骤计数
    raise NotImplementedError


def evaluate_run(
    strategy: str,
    raw_output: str,
    expected_answer: str,
) -> RunResult:
    """评测单次输出。

    - strategy 需可被 normalize_strategy 接受
    - extracted_answer = extract_final_answer(raw_output)
    - step_count = count_reasoning_steps(raw_output)
    - correct = normalize_answer(extracted) == normalize_answer(expected)
    - 若抽取失败，不要吞掉异常（让调用方 / 测试看到 ValueError）
    """
    # TODO: 实现单次评测
    raise NotImplementedError


def compare_outputs(
    task: ReasoningTask,
    direct_output: str,
    cot_output: str,
) -> CompareReport:
    """对比同一题目下 Direct / CoT 两次输出。"""
    # TODO: 分别 evaluate_run 后组装 CompareReport
    raise NotImplementedError


def render_report(report: CompareReport) -> str:
    """把对比报告渲染成可读多行文本。

    至少包含：
    - case_id / question / expected
    - direct：correct / steps / answer
    - cot：correct / steps / answer
    - 一行结论：helped / hurt / tie（两边都对或都错算 tie）
    """
    # TODO: 实现报告渲染
    raise NotImplementedError
