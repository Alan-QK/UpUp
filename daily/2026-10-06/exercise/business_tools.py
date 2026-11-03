"""Day 53 练习：自定义业务工具接入 ToolRegistry。

目标：新增 order_lookup，并挂到 Day52 迷你框架的 Registry 上。
只用标准库。不要改 mini_framework.py / tools_builtin.py 的内核逻辑。
"""

from __future__ import annotations

from typing import Any

from mini_framework import (
    FrameworkAgent,
    ToolRegistry,
    build_default_registry,
    default_system_prompt,
    tool_from_meta,
    validate_max_steps,
)
from tools_builtin import normalize_text

# 模拟订单库（只读）。key = order_id
ORDER_DB: dict[str, dict[str, Any]] = {
    "ORD-1001": {
        "status": "shipped",
        "total": "128.00",
        "currency": "CNY",
        "city": "上海",
        "item": "机械键盘",
    },
    "ORD-1002": {
        "status": "processing",
        "total": "59.90",
        "currency": "CNY",
        "city": "杭州",
        "item": "USB-C 数据线",
    },
    "ORD-1003": {
        "status": "delivered",
        "total": "899.00",
        "currency": "CNY",
        "city": "深圳",
        "item": "显示器支架",
    },
}


def order_lookup(order_id: str) -> str:
    """按订单号查询状态摘要。

    TODO:
    1. normalize_text 清理 order_id；空字符串 → ValueError
    2. 不在 ORDER_DB → KeyError（或 ValueError，信息需含 order_id）
    3. 命中则返回一行人类可读摘要，至少包含：
       order_id、status、total+currency、city、item
       示例：
       "订单 ORD-1001：status=shipped，合计 128.00 CNY，收货地 上海，商品 机械键盘"
    """
    raise NotImplementedError("TODO: implement order_lookup")


def order_lookup_tool_meta() -> dict[str, Any]:
    """返回可交给 tool_from_meta 的业务工具元数据。

    TODO: 返回 dict，字段：
    - name: "order_lookup"
    - description: 说明何时查询订单（只读、按订单号）
    - parameters: JSON Schema，required 含 order_id
    - handler: order_lookup
    """
    raise NotImplementedError("TODO: implement order_lookup_tool_meta")


def register_business_tools(registry: ToolRegistry) -> ToolRegistry:
    """把业务工具注册进已有 Registry（保留原有 lookup/calculate）。

    TODO:
    1. 校验 registry 是 ToolRegistry
    2. tool_from_meta(order_lookup_tool_meta()) 后 register
    3. 返回同一个 registry（便于链式调用）
    """
    raise NotImplementedError("TODO: implement register_business_tools")


def business_system_prompt(registry: ToolRegistry) -> str:
    """在默认提示基础上，补充 order_lookup 使用说明。

    TODO:
    1. 以 default_system_prompt(registry) 为基底
    2. 追加一句：查订单状态时用 order_lookup，不要编造物流
    """
    raise NotImplementedError("TODO: implement business_system_prompt")


def build_business_agent(
    *,
    name: str = "business-agent",
    max_steps: int = 6,
) -> FrameworkAgent:
    """构建：内置工具 + 业务工具 的 Agent。

    TODO:
    1. build_default_registry() → register_business_tools(...)
    2. FrameworkAgent(name, registry, business_system_prompt(registry), max_steps)
    3. max_steps 走 validate_max_steps
    """
    raise NotImplementedError("TODO: implement build_business_agent")


def render_extension_checklist() -> str:
    """输出「接入一个新工具」检查清单 Markdown（固定结构，便于复习）。

    TODO: 返回字符串，必须包含以下标题行（可有额外说明）：
    - # 自定义工具接入清单
    - ## 1. Handler
    - ## 2. Schema
    - ## 3. Register
    - ## 4. Prompt
    - ## 5. Verify
    正文可用短句；不要为空。
    """
    raise NotImplementedError("TODO: implement render_extension_checklist")
