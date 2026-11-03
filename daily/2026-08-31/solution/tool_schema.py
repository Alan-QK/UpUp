"""参考实现：请先自己完成 exercise/ 再对照。

纯标准库：inspect + typing → OpenAI 风格 tool JSON Schema。
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


def is_optional_annotation(annotation: Any) -> bool:
    """是否为 Optional / X | None / Union[..., None]。"""
    if annotation is inspect.Parameter.empty:
        return False
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        return type(None) in get_args(annotation)
    return False


def unwrap_optional(annotation: Any) -> Any:
    """剥掉 Optional / Union 中的 None，返回非 None 分支。

    - 恰好两个成员且其一为 None → 返回另一个
    - 多个非 None 成员 → ValueError（含 \"union\"）
    - 非 Optional → 原样返回
    """
    if not is_optional_annotation(annotation):
        return annotation
    non_none = [a for a in get_args(annotation) if a is not type(None)]
    if len(non_none) != 1:
        raise ValueError("unsupported union annotation")
    return non_none[0]


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
    if annotation is inspect.Parameter.empty:
        raise ValueError("missing type annotation")

    annotation = unwrap_optional(annotation)
    origin = get_origin(annotation)

    if origin is Literal:
        values = list(get_args(annotation))
        if not values:
            raise ValueError("unsupported empty Literal")
        kinds = {type(v) for v in values}
        if len(kinds) != 1 or next(iter(kinds)) not in (str, int, float, bool):
            raise ValueError("unsupported Literal members")
        py_t = next(iter(kinds))
        return {"type": _PRIMITIVE_MAP[py_t], "enum": list(values)}

    if origin is list:
        args = get_args(annotation)
        if len(args) != 1:
            raise ValueError("unsupported list annotation")
        return {"type": "array", "items": annotation_to_json_schema(args[0])}

    if origin is dict or annotation is dict:
        return {"type": "object"}

    if annotation in _PRIMITIVE_MAP:
        return {"type": _PRIMITIVE_MAP[annotation]}

    raise ValueError(f"unsupported annotation: {annotation!r}")


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


def parse_args_descriptions(doc: str | None) -> dict[str, str]:
    """从 Google/简式 Args 段解析参数说明。

    识别以 ``Args:`` / ``Arguments:`` / ``参数:`` 开头的段落，
    直到空行或下一个段标题为止。
    每行 ``name: desc``；同名后者覆盖前者。无 Args 段 → {}。
    不支持多行续写（保持简单）。
    """
    if not doc:
        return {}
    lines = inspect.cleandoc(doc).splitlines()
    start = -1
    for i, line in enumerate(lines):
        if line.strip().lower() in {"args:", "arguments:", "参数:"}:
            start = i + 1
            break
    if start < 0:
        return {}

    result: dict[str, str] = {}
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped:
            break
        if stripped.lower() in _SECTION_HEADERS:
            break
        m = _ARGS_LINE.match(stripped)
        if not m:
            continue
        name, desc = m.group(1), m.group(2).strip()
        if desc:
            result[name] = desc
    return result


def function_description(fn: Callable[..., Any]) -> str:
    """取 docstring 第一段（到空行为止）压成单行；无 docstring → \"\"。"""
    doc = inspect.getdoc(fn)
    if not doc:
        return ""
    parts: list[str] = []
    for line in doc.splitlines():
        if not line.strip():
            if parts:
                break
            continue
        # 遇到 Args/Returns 等段标题则停
        low = line.strip().lower()
        if low in {"args:", "arguments:", "参数:", "returns:", "return:", "raises:", "返回:", "异常:"}:
            break
        parts.append(line.strip())
    return " ".join(parts).strip()


def iter_tool_parameters(fn: Callable[..., Any]) -> list[inspect.Parameter]:
    """列出可作为 tool 参数的签名参数。

    - 跳过 self / cls
    - 出现 *args / **kwargs → ValueError（含 \"variadic\"）
    - 其余按定义顺序返回
    """
    sig = inspect.signature(fn)
    params: list[inspect.Parameter] = []
    for name, param in sig.parameters.items():
        if name in {"self", "cls"}:
            continue
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            raise ValueError("variadic parameters are not supported")
        if param.kind is inspect.Parameter.POSITIONAL_ONLY:
            raise ValueError("positional-only parameters are not supported")
        params.append(param)
    return params


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
    arg_docs = parse_args_descriptions(inspect.getdoc(fn))
    hints = get_type_hints(fn)
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param in iter_tool_parameters(fn):
        if param.name not in hints:
            raise ValueError("missing type annotation")
        annotation = hints[param.name]
        schema = annotation_to_json_schema(annotation)
        desc = arg_docs.get(param.name, "").strip()
        if desc:
            schema = {**schema, "description": desc}
        properties[param.name] = schema

        optional = is_optional_annotation(annotation)
        has_default = param.default is not inspect.Parameter.empty
        if not optional and not has_default:
            required.append(param.name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


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

    - name 默认 fn.__name__；若传入须为非空标识符，否则 ValueError 含 \"name\"
    - description 默认 function_description(fn)；显式传入空串也允许
    - fn 必须是可调用对象，否则 TypeError
    """
    if not callable(fn):
        raise TypeError("fn must be callable")
    tool_name = name if name is not None else fn.__name__
    if not tool_name or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", tool_name):
        raise ValueError("invalid tool name")
    tool_desc = function_description(fn) if description is None else description
    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool_desc,
            "parameters": function_to_parameters_schema(fn),
        },
    }


def tools_from_functions(*fns: Callable[..., Any]) -> list[dict[str, Any]]:
    """批量转换；空输入 → []；同名工具 → ValueError 含 \"duplicate\"。"""
    tools: list[dict[str, Any]] = []
    seen: set[str] = set()
    for fn in fns:
        tool = function_to_tool_schema(fn)
        n = tool["function"]["name"]
        if n in seen:
            raise ValueError(f"duplicate tool name: {n}")
        seen.add(n)
        tools.append(tool)
    return tools
