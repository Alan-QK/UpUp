"""Day 2 手工运行入口。"""

from __future__ import annotations

from models import Role
from validate import build_agent_config, create_user, describe_user


def main() -> None:
    user = create_user(" u1 ", " Ada ", Role.ADMIN)
    print(describe_user(user))

    cfg = build_agent_config("gpt-4o-mini", temperature=0.1, max_tokens=512)
    print(cfg)


if __name__ == "__main__":
    main()
