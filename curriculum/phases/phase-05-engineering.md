# Phase 5｜工程化：服务化、评测、观测与部署

> 周期：Week 17–20（约 20 个工作日）  
> 关键词：FastAPI、SSE、会话、Eval、Tracing、成本、部署

---

## 阶段目标

1. 把 Agent 封装成 HTTP API（含流式）
2. 建立最小评测集与回归意识
3. 具备基础可观测性（日志/追踪概念）
4. 交付里程碑：`projects/agent-api`

---

## 周计划

### Week 17 · API 服务化

| Day | 主题 | Coding |
|-----|------|--------|
| D81 | FastAPI 快速入门 | Hello API |
| D82 | Chat 接口设计 | POST /chat |
| D83 | SSE 流式响应 | /chat/stream |
| D84 | 会话 ID 与存储 | 内存/文件存储 |
| D85 | 周挑战：OpenAPI 文档完善 | 可调试 API |

### Week 18 · 可靠性

| Day | 主题 | Coding |
|-----|------|--------|
| D86 | 超时、取消、并发限制 | middleware |
| D87 | 重试与幂等 | request id |
| D88 | 限流与配额 | 简单令牌桶 |
| D89 | 配置分层（dev/prod） | settings |
| D90 | 周挑战：故障注入演练 | 混沌小测 |

### Week 19 · 评测与质量

| Day | 主题 | Coding |
|-----|------|--------|
| D91 | Golden set 设计 | 20 条用例 |
| D92 | 自动评分（规则+LLM-as-judge） | eval runner |
| D93 | 轨迹评测（是否乱调工具） | trace assert |
| D94 | 回归：改 Prompt 不踩坑 | CI 思路 |
| D95 | 周挑战：评测报告生成 | markdown report |

### Week 20 · 观测、成本与部署

| Day | 主题 | Coding |
|-----|------|--------|
| D96 | 结构化日志与请求关联 | correlation id |
| D97 | Tracing 概念（LangSmith/OTel） | 埋点练习 |
| D98 | Token/费用看板脚本 | cost summary |
| D99 | Docker 基础打包 | Dockerfile |
| D100 | 里程碑：`agent-api` 验收 | 项目打磨 |

---

## 里程碑验收清单

- [ ] 提供非流式 + 流式两个接口
- [ ] 会话可按 `session_id` 延续
- [ ] 有基础评测脚本与样例报告
- [ ] 日志能串联一次完整 Agent 轨迹
- [ ] Dockerfile 可本地构建运行
- [ ] README 含 API 示例（curl）

---

## 完成后进入

→ [Phase 6：综合项目与作品集](./phase-06-capstone.md)
