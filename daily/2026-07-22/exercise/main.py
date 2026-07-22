"""Day 3 手工运行入口。"""

from __future__ import annotations

from pathlib import Path

from config_io import load_agent_config, save_agent_config
from models import AgentConfig


def main() -> None:
    root = Path(__file__).resolve().parent
    sample = root / "fixtures" / "agent.sample.json"
    out = root / "fixtures" / "agent.out.json"

    cfg = load_agent_config(sample)
    print("loaded:", cfg)

    tweaked = AgentConfig(
        model=cfg.model,
        temperature=0.1,
        max_tokens=512,
    )
    save_agent_config(out, tweaked)
    print("saved to:", out)
    print("reloaded:", load_agent_config(out))


if __name__ == "__main__":
    main()
