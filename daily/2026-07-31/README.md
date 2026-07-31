# Day 9｜环境变量与密钥管理

> 日期：2026-07-31（周五）  
> Phase 1 / Week 2 · 学习日序号：**D9 / 120**  
> 建议时长：**75 分钟**（概念 20 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清为什么 API Key **绝不能**写进源码或提交到 Git
2. 手写一个最小 `.env` 解析/加载器（不引入第三方依赖）
3. 用 `require_env` 在启动时快速失败，而不是带着空密钥去调模型
4. 打印配置时对密钥做脱敏（`mask_secret`）

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 2）
2. 仓库根目录 [`.env.example`](../../.env.example) 与 [`.gitignore`](../../.gitignore)（注意 `.env` 已被忽略）
3. 今日笔记：[`notes.md`](./notes.md)

重点抓住三件事：

- **密钥是配置，不是代码**：进程启动时从环境注入
- **`.env` 只是本地便利**：生产环境用真正的环境变量 / Secret Manager
- **缺密钥要早死**：启动时报错，别等到第一次 HTTP 401

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 任务

1. 完成 `exercise/env_loader.py` 中的 TODO
2. 阅读 `exercise/main.py`（加载示例 env 并打印脱敏配置）
3. 跑通测试：

```bash
cd daily/2026-07-31/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] 能解析注释、空行、`KEY=VALUE`、可选引号
- [ ] `load_dotenv` 默认**不覆盖**已存在的环境变量；`override=True` 时可覆盖
- [ ] `require_env` 在缺失/空值时抛出清晰的 `EnvError`
- [ ] `mask_secret` 打印时不泄露完整密钥
- [ ] 全程只用标准库（不要 `pip install python-dotenv`）

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能解释：`.env` 为什么必须进 `.gitignore`
- [ ] 我知道「已有环境变量优先」为什么是合理默认（CI / 容器注入）
- [ ] 我能说出下周 Day 10：多 API 聚合 CLI（会用到今天的密钥加载）
- [ ] 我不会把真实 Key 贴到聊天、截图或 commit message 里

---

## 通知摘要（便于推送）

**Day 9｜环境变量与密钥管理**  
手写 `.env` 加载器：解析、注入、必填校验与密钥脱敏；API Key 永不写进代码。  
路径：`daily/2026-07-31/`
