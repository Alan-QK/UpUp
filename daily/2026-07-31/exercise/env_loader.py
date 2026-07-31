"""Day 9 练习：.env 加载与密钥安全读取。

请完成 TODO，使 tests/ 全部通过。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, MutableMapping


class EnvError(ValueError):
    """环境变量或 .env 文件不合法。"""


def parse_dotenv(text: str) -> dict[str, str]:
    """把 .env 文本解析为 dict。

    规则：
    - 忽略空行、以及去掉首尾空白后以 # 开头的行
    - 每行必须包含至少一个 '='；否则 EnvError("invalid line: ...")
    - key = '=' 左侧 strip 后；不能为空 → EnvError("empty key")
    - value = '=' 右侧（只去掉行尾换行相关空白：用 rstrip('\\r\\n')，再按需处理引号）
      * 若 value 以成对的单引号或双引号包裹，去掉这对引号
      * 其余情况保留 value 内部空格；不要 strip 掉中间空格
      * 对「未加引号」的 value：去掉首尾空白（strip）
    - 同一 key 多次出现：后者覆盖前者
    - 不做行尾 # 注释剥离
    """
    # TODO: 实现这里
    raise NotImplementedError


def load_dotenv(
    path: Path,
    *,
    environ: MutableMapping[str, str] | None = None,
    override: bool = False,
) -> dict[str, str]:
    """从文件加载变量写入 environ，并返回「本次解析到的」全部键值。

    规则：
    - path 不存在 → EnvError("env file not found: {path}")
    - 用 UTF-8 读取全文，再交给 parse_dotenv
    - environ 默认 os.environ
    - 写入策略：
      * override=False（默认）：仅当 key 不在 environ 时才写入
      * override=True：始终写入（覆盖）
    - 返回值始终是 parse_dotenv 的完整结果（与是否写入无关）
    """
    # TODO: 实现这里
    raise NotImplementedError


def get_env(
    name: str,
    default: str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> str | None:
    """读取环境变量；不存在则返回 default。

    规则：
    - environ 默认 os.environ
    - 若 key 存在，返回原值（不做 strip）；不存在返回 default
    """
    # TODO: 实现这里
    raise NotImplementedError


def require_env(
    name: str,
    *,
    environ: Mapping[str, str] | None = None,
) -> str:
    """读取必填环境变量。

    规则：
    - 缺失，或 strip 后为空 → EnvError("missing required env: {name}")
    - 成功返回 strip 后的值
    """
    # TODO: 实现这里
    raise NotImplementedError


def mask_secret(value: str, *, head: int = 4, tail: int = 4) -> str:
    """脱敏密钥，便于日志打印。

    规则：
    - value 去掉首尾空白后再处理；若结果为空 → "***"
    - 若长度 <= head + tail → 返回 "***"（避免脱敏无效）
    - 否则返回 f"{前 head 个字符}…{后 tail 个字符}"（中间是英文省略号 …）
    """
    # TODO: 实现这里
    raise NotImplementedError


@dataclass(frozen=True)
class LlmSettings:
    """从环境组装的 LLM 配置。"""

    api_key: str
    base_url: str
    model: str


def load_llm_settings(*, environ: Mapping[str, str] | None = None) -> LlmSettings:
    """组装 LlmSettings。

    规则：
    - OPENAI_API_KEY：必填（require_env）
    - OPENAI_BASE_URL：可选，默认 "https://api.openai.com/v1"
    - OPENAI_MODEL：可选，默认 "gpt-4o-mini"
    - 可选值若存在但 strip 后为空，视为未设置，走默认值
    """
    # TODO: 实现这里
    raise NotImplementedError
