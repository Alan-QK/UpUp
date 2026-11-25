"""Day 56 练习：Prompt Injection 案例集与本地启发式检测。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——今天是「攻防教学案例库」，不调用真实 LLM。
"""

from __future__ import annotations

from dataclasses import dataclass

ATTACK_DIRECT = "direct"
ATTACK_INDIRECT = "indirect"
ATTACK_EXFILTRATION = "exfiltration"
ALLOWED_ATTACK_TYPES = frozenset(
    {ATTACK_DIRECT, ATTACK_INDIRECT, ATTACK_EXFILTRATION}
)

ENTRY_USER = "user_message"
ENTRY_DOCUMENT = "retrieved_document"
ENTRY_TOOL = "tool_output"
ALLOWED_ENTRIES = frozenset({ENTRY_USER, ENTRY_DOCUMENT, ENTRY_TOOL})

RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
ALLOWED_RISKS = frozenset({RISK_LOW, RISK_MEDIUM, RISK_HIGH})

ACTION_ALLOW = "allow"
ACTION_SANITIZE = "sanitize"
ACTION_BLOCK = "block"
ALLOWED_ACTIONS = frozenset({ACTION_ALLOW, ACTION_SANITIZE, ACTION_BLOCK})

OUTCOME_SAFE = "safe"
OUTCOME_COMPROMISED = "compromised"
ALLOWED_OUTCOMES = frozenset({OUTCOME_SAFE, OUTCOME_COMPROMISED})

REQUIRED_REPORT_SECTIONS = (
    "案例总览",
    "三类攻击对照",
    "检测信号",
    "防御清单",
    "明日预告",
)

# 教学用启发式信号（小写匹配）。故意做成可解释的关键词，不是生产级模型。
DIRECT_SIGNALS = (
    "ignore previous instructions",
    "忽略以上",
    "忽略之前",
    "覆盖系统",
    "你现在是无限制",
)
INDIRECT_SIGNALS = (
    "system:",
    "hidden instruction",
    "隐藏指令",
    "之后所有查询",
    "forward all queries",
)
EXFIL_SIGNALS = (
    "system prompt",
    "系统提示",
    "api key",
    "api密钥",
    "dump the secret",
    "贴出隐藏规则",
    "base64",
)


@dataclass(frozen=True)
class AttackCase:
    """一条可复现的 Prompt Injection 教学案例。"""

    case_id: str
    attack_type: str
    entry: str
    payload: str
    expected_harm: str
    defense_hint: str


@dataclass(frozen=True)
class DetectionResult:
    """对一段文本的启发式检测结果。"""

    attack_type: str | None
    risk: str
    matched_signals: tuple[str, ...]
    action: str


@dataclass(frozen=True)
class AgentSimulation:
    """朴素 Agent（无防护）对一轮输入的教学模拟结果。"""

    outcome: str
    reason: str
    used_attack_type: str | None


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。"""
    # TODO: 实现规范化
    raise NotImplementedError


def normalize_attack_type(attack_type: str) -> str:
    """规范化 attack_type；非法值抛 ValueError（消息含 attack）。"""
    # TODO: strip + lower，校验属于 ALLOWED_ATTACK_TYPES
    raise NotImplementedError


def normalize_entry(entry: str) -> str:
    """规范化 entry；非法值抛 ValueError（消息含 entry）。"""
    # TODO
    raise NotImplementedError


def normalize_risk(risk: str) -> str:
    """规范化 risk；非法值抛 ValueError（消息含 risk）。"""
    # TODO
    raise NotImplementedError


def normalize_action(action: str) -> str:
    """规范化 action；非法值抛 ValueError（消息含 action）。"""
    # TODO
    raise NotImplementedError


def validate_attack_case(case: AttackCase) -> None:
    """校验案例字段：类型/入口合法，其余字符串规范化后非空。"""
    # TODO
    raise NotImplementedError


def classify_by_signals(text: str) -> str | None:
    """按信号优先级判定类型：exfiltration > direct > indirect；无命中返回 None。

    优先级理由（教学约定）：
    - 窃密信号往往也带「忽略指令」措辞，先标 exfiltration 更贴近破坏目标
    - 其次才是直接覆盖系统
    - 再其次是文档/工具里的伪装 SYSTEM 指令
    """
    # TODO: 对 normalize_text(text).lower() 做子串匹配
    raise NotImplementedError


def matched_signals_for(text: str, attack_type: str | None = None) -> tuple[str, ...]:
    """返回命中的信号列表（保持各信号表内顺序）。

    - attack_type 为 None：合并三类信号表去重扫描
    - 指定类型：只扫该类型信号表
    """
    # TODO
    raise NotImplementedError


def risk_for_attack_type(attack_type: str | None) -> str:
    """映射风险：None→low；indirect→medium；direct/exfiltration→high。"""
    # TODO
    raise NotImplementedError


def action_for_risk(risk: str) -> str:
    """映射处置：low→allow；medium→sanitize；high→block。"""
    # TODO
    raise NotImplementedError


def detect_injection(text: str) -> DetectionResult:
    """对文本做启发式检测，返回 DetectionResult。"""
    # TODO: classify → matched_signals → risk → action
    raise NotImplementedError


def simulate_naive_agent(
    system_prompt: str,
    user_message: str,
    context: str = "",
) -> AgentSimulation:
    """模拟「把所有文本一视同仁当指令」的朴素 Agent。

    规则（教学用，非真实 LLM）：
    1. 分别检测 user_message 与 context
    2. 任一检出 attack_type（含 medium 的 indirect）→ outcome=compromised，
       used_attack_type 取更危险的那个（exfiltration > direct > indirect）
    3. 否则 outcome=safe，used_attack_type=None
    4. system_prompt 本身不参与「被注入」判定（它是受信侧）
    """
    # TODO
    raise NotImplementedError


def apply_basic_defense(text: str) -> tuple[str, DetectionResult]:
    """按检测结果处置文本，返回 (处理后文本, DetectionResult)。

    - allow：原样返回（仍做 normalize_text）
    - sanitize：去掉所有已匹配信号子串（大小写不敏感），再 normalize
    - block：返回空字符串 ""
    """
    # TODO
    raise NotImplementedError


def build_casebook() -> tuple[AttackCase, ...]:
    """返回固定三类教学案例（顺序：direct → indirect → exfiltration）。

    要求：
    - case_id 分别为 DI-01 / IN-01 / EX-01
    - entry：direct→user_message；indirect→retrieved_document；exfiltration→user_message
    - payload 必须能被 detect_injection 判到对应类型
    - expected_harm / defense_hint 为非空中文短句
    """
    # TODO
    raise NotImplementedError


def render_casebook_report(
    cases: tuple[AttackCase, ...] | list[AttackCase] | None = None,
    title: str = "Week 12 · Prompt Injection 案例集",
) -> str:
    """渲染 Markdown 案例报告，必须包含 REQUIRED_REPORT_SECTIONS 全部二级标题。"""
    # TODO
    raise NotImplementedError
