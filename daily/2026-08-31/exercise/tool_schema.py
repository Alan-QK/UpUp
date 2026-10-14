"""Day 28 练习：从函数到 JSON Schema（tool schema）。

纯标准库实现（inspect + typing）。请完成 TODO。
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Callable
from types import UnionType
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints

# Python 类型 → JSON Schema type 字段
_PRIMITIVE_MAP: dict[Any, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}

_SECTION_HEADERS = frozenset(
    {
        "args:",
        "arguments:",
        "参数:",
        "returns:",
        "return:",
        "raises:",
        "yields:",
        "example:",
        "examples:",
        "返回:",
        "异常:",
    }
)
_ARGS_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$")


def is_optional_annotation(annotation: Any) -> bool:
    """是否为 Optional / X | None / Union[..., None]。"""
    # TODO: 用 get_origin / get_args 判断
    raise NotImplementedError


def unwrap_optional(annotation: Any) -> Any:
    """剥掉 Optional / Union 中的 None，返回非 None 分支。

    - 恰好两个成员且其一为 None → 返回另一个
    - 多个非 None 成员 → ValueError（含 \"union\"）
    - 非 Optional → 原样返回
    """
    # TODO
    raise NotImplementedError


def annotation_to_json_schema(annotation: Any) -> dict[str, Any]:
    """把单个类型注解转成 JSON Schema 片段（不含 required）。

    支持：
    - str / int / float / bool
    - list[T]（T 须可再转换）
    - dict / dict[str, Any] → {\"type\": \"object\"}
    - Literal[\"a\", \"b\"] → string + enum（成员须同为 str/int/float/bool）
    - Optional[T] / T | None → 按 T 转换（是否 required 由上层决定）

    不支持 / 报错：
    - 缺注解（Parameter.empty）→ ValueError 含 \"annotation\"
    - Any / 未知类型 → ValueError 含 \"unsupported\"
    """
    # TODO: 先 unwrap_optional，再按 origin / 原始类型分支
    raise NotImplementedError


def parse_args_descriptions(doc: str | None) -> dict[str, str]:
    """从 Google/简式 Args 段解析参数说明。

    识别以 ``Args:`` / ``Arguments:`` / ``参数:`` 开头的段落，
    直到空行或下一个段标题为止。
    每行 ``name: desc``；同名后者覆盖前者。无 Args 段 → {}。
    不支持多行续写（保持简单）。
    """
    # TODO: 可用 _SECTION_HEADERS / _ARGS_LINE
    raise NotImplementedError


def function_description(fn: Callable[..., Any]) -> str:
    """取 docstring 第一段（到空行为止）压成单行；无 docstring → \"\"。

    若第一段遇到 Args/Returns 等段标题则停。
    """
    # TODO: inspect.getdoc
    raise NotImplementedError


def iter_tool_parameters(fn: Callable[..., Any]) -> list[inspect.Parameter]:
    """列出可作为 tool 参数的签名参数。

    - 跳过 self / cls
    - 出现 *args / **kwargs → ValueError（含 \"variadic\"）
    - positional-only → ValueError（含 \"positional-only\"）
    - 其余按定义顺序返回
    """
    # TODO: inspect.signature
    raise NotImplementedError


def function_to_parameters_schema(fn: Callable[..., Any]) -> dict[str, Any]:
    """生成 OpenAI tools.parameters 对象。

    {
      \"type\": \"object\",
      \"properties\": { name: schema(+可选 description) },
      \"required\": [无默认且非 Optional 的参数，保序]
    }

    - 每个参数必须有类型注解，否则 ValueError 含 \"annotation\"
    - 必须用 typing.get_type_hints(fn) 解析注解（兼容 from __future__ import annotations）
    - properties 键顺序与签名一致
    - 有默认值 → 不进 required
    - Optional / | None（即使无默认）→ 不进 required
    - 参数 description 来自 docstring Args 段；有则写入，无则不写 description 键
    """
    # TODO
    raise NotImplementedError


def function_to_tool_schema(
    fn: Callable[..., Any],
    *,
    name: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """生成 OpenAI Chat Completions tools[] 单条结构：

    {
      \"type\": \"function\",
      \"function\": {
        \"name\": ...,
        \"description\": ...,
        \"parameters\": {...}
      }
    }

    - name 默认 fn.__name__；若传入须匹配 ``[A-Za-z_][A-Za-z0-9_]*``，否则 ValueError 含 \"name\"
    - description 默认 function_description(fn)；显式传入空串也允许
    - fn 必须是可调用对象，否则 TypeError
    """
    # TODO
    raise NotImplementedError


def tools_from_functions(*fns: Callable[..., Any]) -> list[dict[str, Any]]:
    """批量转换；空输入 → []；同名工具 → ValueError 含 \"duplicate\"。"""
    # TODO
    raise NotImplementedError


# 给实现时用的提示符号（避免未使用导入告警）
_ = (
    Union,
    UnionType,
    Literal,
    get_type_hints,
    _PRIMITIVE_MAP,
    _SECTION_HEADERS,
    _ARGS_LINE,
)
