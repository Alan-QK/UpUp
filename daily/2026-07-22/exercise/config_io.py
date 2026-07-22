"""Day 3 练习：JSON 配置读写。

请完成 TODO，使 tests/ 全部通过。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models import AgentConfig


class ConfigError(ValueError):
    """配置文件或配置内容不合法。"""


def load_json(path: Path) -> dict[str, Any]:
    """读取 JSON 对象文件。

    规则：
    - path 不存在 → ConfigError("config not found: {path}")
    - JSON 解析失败 → ConfigError("invalid json: {path}")
    - 根节点不是 object/dict → ConfigError("config root must be an object")
    - 成功返回 dict
    """
    # TODO: 实现这里
    raise NotImplementedError


def save_json(path: Path, data: dict[str, Any]) -> None:
    """将 dict 写成 UTF-8 JSON 文件。

    规则：
    - 若父目录不存在，先创建（parents=True）
    - 使用 json.dumps(..., ensure_ascii=False, indent=2)
    - 末尾加一个换行符 \\n
    """
    # TODO: 实现这里
    raise NotImplementedError


def _validate_agent_dict(data: dict[str, Any]) -> AgentConfig:
    """把 dict 校验并转为 AgentConfig。

    规则：
    - 必须包含键 model（允许额外键，忽略即可）
    - model 去首尾空格后不能为空 → ConfigError("model must not be empty")
    - temperature 缺省 0.2；必须是 int/float 且在 [0, 2]
      → ConfigError("temperature out of range") 或 ConfigError("temperature must be a number")
    - max_tokens 缺省 1024；必须是 int 且 >= 1
      → ConfigError("max_tokens must be >= 1") 或 ConfigError("max_tokens must be an int")
    """
    # TODO: 实现这里
    raise NotImplementedError


def load_agent_config(path: Path) -> AgentConfig:
    """从 JSON 文件加载 AgentConfig。"""
    # TODO: 调用 load_json + _validate_agent_dict
    raise NotImplementedError


def save_agent_config(path: Path, config: AgentConfig) -> None:
    """将 AgentConfig 保存为 JSON 文件。"""
    # TODO: 调用 config.to_dict() + save_json
    raise NotImplementedError
