# Day 18｜模型 Provider 抽象

> 日期：2026-08-13（周四）  
> Phase 1 / Week 4 · 学习日序号：**D18 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 用 Protocol 描述「聊天补全」能力边界，而不是绑死某一家 SDK
2. 实现可注入的 `FakeChatProvider`，让上层逻辑离线可测
3. 用工厂函数按 `kind` 切换 `fake` / `openai` 实现
4. 说清前端「接口 + Mock」与后端 Provider 抽象的对应关系

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 4）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选：对照 Day 11/17 的 `ChatClient.complete`——今天要把它「收成接口」

重点抓住三件事：

- **业务代码依赖协议，不依赖厂商**
- **假实现是一等公民**：CI / 本地 demo 不烧钱
- **工厂集中创建点**：换模型 = 换配置，不是改半个仓库

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 任务

1. 完成 `exercise/providers.py` 中的 TODO（`FakeChatProvider` + `create_chat_provider`）
2. `openai_compat.py` / `main.py` **已给齐**，无需改
3. 跑通测试：

```bash
cd daily/2026-08-13/exercise
python3 -m pytest -q
```

若尚未安装依赖：

```bash
python3 -m pip install --user httpx pytest
```

4. 手工试跑（离线 Demo）：

```bash
python3 main.py --demo
python3 main.py --demo -m "上下文窗口是什么？"
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `FakeChatProvider` 按「最后一条 user 消息」查表回复，未命中走默认句
- [ ] `.calls` 能回放每次 `complete` 的入参（便于断言）
- [ ] `create_chat_provider("fake"|"openai"|…)` 行为符合笔记约定
- [ ] 业务入口（`main.py`）只依赖 `ChatProvider`，不直接 `import httpx` 调厂商细节
- [ ] `--demo` 能打印假模型回复

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能画出：`Assistant → ChatProvider ← Fake / OpenAICompat` 的依赖方向
- [ ] 我知道为什么单测里要用 Fake，而不是打真实 API
- [ ] 我能说出换 DeepSeek / 通义时，理想情况下只需改工厂配置
- [ ] 我已知明天 Day 19：结构化日志与调试

---

## 通知摘要（便于推送）

**Day 18｜模型 Provider 抽象**  
用 Protocol 抽象聊天补全，实现 Fake + 工厂切换 openai；业务代码可离线测、可换厂商。  
路径：`daily/2026-08-13/`
