"""Day 38 练习：拒答与低相关处理（无依据时不硬答）。

复用 Day 36 的 `rag_pipeline.RetrievedChunk`（已给出，勿改）。
请完成 TODO，使 tests/ 全部通过。
只用标准库 + pytest；不要引入 openai / langchain / chromadb。

前端类比：搜索空状态 + 请求前 Guard——分数不够就展示「暂无可靠资料」，别渲染假答案。
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from rag_pipeline import RetrievedChunk

GenerateLike = Callable[[str, Sequence[RetrievedChunk]], str]

DEFAULT_REFUSAL_HINT = "请换个问法，或补充相关文档后再试。"


class RefusalError(ValueError):
    """拒答策略参数不合法。"""


@dataclass(frozen=True)
class RefusalPolicy:
    """检索门控策略。

    - min_top_score：top-1 分数必须 ≥ 该值，否则 low_score
    - min_margin：若命中 ≥ 2 条，则 (top1 - top2) 必须 ≥ 该值，否则 low_margin；
      命中不足 2 条时不做 margin 检查
    """

    min_top_score: float = 0.55
    min_margin: float = 0.0


@dataclass(frozen=True)
class GateDecision:
    """一次检索门控结果。"""

    allow: bool
    reason: str  # "ok" | "empty" | "low_score" | "low_margin"
    top_score: float | None
    margin: float | None
    detail: str


@dataclass(frozen=True)
class GatedAnswer:
    """门控后的问答结果（拒答或放行生成）。"""

    question: str
    refused: bool
    reason: str
    answer: str
    display: str
    contexts: tuple[RetrievedChunk, ...]
    decision: GateDecision


def validate_policy(policy: RefusalPolicy) -> None:
    """校验策略参数。

    规则：
    - min_top_score 为 bool，或不在 [0, 1] → RefusalError，消息含 \"min_top_score\"
    - min_margin 为 bool，或 < 0，或 > 1 → RefusalError，消息含 \"min_margin\"
    """
    # TODO
    raise NotImplementedError


def top_score(chunks: Sequence[RetrievedChunk]) -> float | None:
    """返回 rank==1 的分数；若无命中则 None。

    若存在命中但找不到 rank==1 → RefusalError，消息含 \"rank\"。
    """
    # TODO
    raise NotImplementedError


def score_margin(chunks: Sequence[RetrievedChunk]) -> float | None:
    """返回 top1.score - top2.score；命中不足 2 条则 None。

    需要同时存在 rank==1 与 rank==2；缺一 → RefusalError，消息含 \"rank\"。
    """
    # TODO
    raise NotImplementedError


def evaluate_retrieval(
    chunks: Sequence[RetrievedChunk],
    policy: RefusalPolicy | None = None,
) -> GateDecision:
    """根据检索命中与策略给出放行/拒答决定。

    流程：
    1. policy 默认 RefusalPolicy()；先 validate_policy
    2. 空命中 → allow=False, reason=\"empty\", top_score=None, margin=None
    3. 取 ts=top_score(chunks)；若 ts < min_top_score → reason=\"low_score\"
    4. 否则若 len(chunks)>=2：m=score_margin(chunks)；
       若 m < min_margin → reason=\"low_margin\"
    5. 否则 allow=True, reason=\"ok\"
    6. detail 用简短中文/英文均可（测试不校验 detail 文案）
    """
    # TODO
    raise NotImplementedError


def format_refusal(
    question: str,
    decision: GateDecision,
    *,
    hint: str = DEFAULT_REFUSAL_HINT,
    min_top_score: float = 0.55,
) -> str:
    """生成用户可读的拒答文案。

    规则：
    - question 先 strip；空 → RefusalError，消息含 \"question\"
    - decision.allow 为 True → RefusalError，消息含 \"allow\"
    - hint 先 strip；空 → RefusalError，消息含 \"hint\"
    - min_top_score 为 bool 或不在 [0, 1] → RefusalError，消息含 \"min_top_score\"
    - 输出固定三行（末尾无多余空行）：
        抱歉，我无法依据当前资料回答「{question}」。
        原因：{reason_text}
        建议：{hint}
      reason_text 映射：
        empty      → 没有检索到任何相关片段
        low_score  → 最高相关度不足（top_score={ts}，阈值={thr}）
                     ts：decision.top_score 四位小数；若为 None 则写 n/a
                     thr：参数 min_top_score 的四位小数
        low_margin → 候选资料区分度不足（margin={m}）
                     m：decision.margin 四位小数；若为 None 则写 n/a
        其他       → 资料不足（{reason}）
    """
    # TODO
    raise NotImplementedError


def gated_answer(
    question: str,
    chunks: Sequence[RetrievedChunk],
    generate_fn: GenerateLike,
    *,
    policy: RefusalPolicy | None = None,
    hint: str = DEFAULT_REFUSAL_HINT,
) -> GatedAnswer:
    """先门控，再决定是否调用 generate_fn。

    流程：
    1. q = question.strip()；空 → RefusalError，消息含 \"question\"
    2. pol = policy or RefusalPolicy()
    3. decision = evaluate_retrieval(chunks, pol)
    4. 若 not decision.allow：
         text = format_refusal(
             q, decision, hint=hint, min_top_score=pol.min_top_score
         )
         返回 GatedAnswer(
           question=q, refused=True, reason=decision.reason,
           answer=text, display=text,
           contexts=tuple(chunks), decision=decision,
         )
         （注意：此时不得调用 generate_fn）
    5. 否则：
         raw = generate_fn(q, chunks)
         若 raw 不是 str → RefusalError，消息含 \"generate\"
         answer = raw.strip()；空 → RefusalError，消息含 \"empty\"
         返回 refused=False, reason=\"ok\", answer=answer, display=answer, ...
    """
    # TODO
    raise NotImplementedError
