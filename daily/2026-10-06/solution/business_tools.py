"""Day 53 参考实现：自定义业务工具 order_lookup 接入框架。"""

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
    cleaned = normalize_text(order_id)
    if not cleaned:
        raise ValueError("order_id must be non-empty")
    if cleaned not in ORDER_DB:
        raise KeyError(f"unknown order_id: {cleaned}")
    row = ORDER_DB[cleaned]
    return (
        f"订单 {cleaned}：status={row['status']}，"
        f"合计 {row['total']} {row['currency']}，"
        f"收货地 {row['city']}，商品 {row['item']}"
    )


def order_lookup_tool_meta() -> dict[str, Any]:
    return {
        "name": "order_lookup",
        "description": (
            "按订单号查询只读订单状态与摘要（状态、金额、收货城市、商品）。"
            "当用户询问某笔订单进度/详情时使用；不要编造不存在的订单。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "订单号，例如 ORD-1001",
                },
            },
            "required": ["order_id"],
        },
        "handler": order_lookup,
    }


def register_business_tools(registry: ToolRegistry) -> ToolRegistry:
    if not isinstance(registry, ToolRegistry):
        raise TypeError("registry must be ToolRegistry")
    registry.register(tool_from_meta(order_lookup_tool_meta()))
    return registry


def business_system_prompt(registry: ToolRegistry) -> str:
    base = default_system_prompt(registry)
    return (
        f"{base}"
        "查订单状态或详情时使用 order_lookup，根据工具观察回答，不要编造物流。"
    )


def build_business_agent(
    *,
    name: str = "business-agent",
    max_steps: int = 6,
) -> FrameworkAgent:
    registry = register_business_tools(build_default_registry())
    return FrameworkAgent(
        name=name,
        registry=registry,
        system_prompt=business_system_prompt(registry),
        max_steps=validate_max_steps(max_steps),
    )


def render_extension_checklist() -> str:
    return "\n".join(
        [
            "# 自定义工具接入清单",
            "",
            "## 1. Handler",
            "实现纯函数业务逻辑；空参与未知资源要抛明确错误。",
            "",
            "## 2. Schema",
            "补齐 name / description / parameters（含 required），与 handler 参数名对齐。",
            "",
            "## 3. Register",
            "通过 ToolRegistry.register 挂载；不要改 Runner 内核写 if-else。",
            "",
            "## 4. Prompt",
            "system prompt 点名新工具及使用时机，避免模型当它不存在。",
            "",
            "## 5. Verify",
            "检查 names()、openai_tools()、ScriptedChat 多步 Observation 回填。",
            "",
        ]
    )
