# Day 9 笔记｜环境变量与密钥管理

## 1. 今天学什么？

下周就要真正调 LLM API 了。在那之前，必须先把**密钥习惯**钉死：

| 错误做法 | 正确做法 |
|----------|----------|
| `api_key = "sk-xxxx"` 写在 `.py` 里 | 从环境变量读取 |
| 把 `.env` 提交到 Git | `.env` 进 `.gitignore`；仓库只留 `.env.example` |
| 日志打印完整 Key | 脱敏：`sk-ab…wxyz` |
| 缺 Key 时默默用空字符串 | 启动时 `require_env` 直接失败 |

前端类比：你不会把 OSS / 第三方 SDK 的 Secret 写进前端打包产物；同样，Python 脚本也不能把 Key 硬编码。

## 2. `.env` 是什么？

本地开发时的小文件，一行一个配置：

```bash
# 这是注释
OPENAI_API_KEY=sk-demo-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

规则（今天练习采用的最小子集）：

1. 空行、以 `#` 开头的行 → 忽略
2. 必须有 `=`；左边是 key（去首尾空白），右边是 value
3. value 两端可有成对单/双引号，加载时去掉
4. 行内 `#`：简单起见，**今天不做**「行尾注释剥离」（避免把 URL 里的 `#` 弄坏）

生产环境（Docker / K8s / CI）通常**直接注入环境变量**，不一定有 `.env` 文件。所以加载器应支持：

- 文件可选地加载进 `os.environ`
- **默认不覆盖**已经存在的变量（容器注入优先）

## 3. 手写加载 vs `python-dotenv`

真实项目可以用 `python-dotenv`。今天刻意手写，是为了：

1. 看清「解析 → 写入 environ → 读取」三步
2. 少一个依赖（练习环境更简单）
3. 理解库帮你做了什么，而不是魔法

以后接 LLM SDK 时，你会看到它们也是 `os.environ["OPENAI_API_KEY"]`。

## 4. 启动时校验

```python
def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise EnvError(f"missing required env: {name}")
    return value
```

Agent 服务启动失败，好过跑了半小时才发现 Key 是空的。

## 5. 脱敏打印

演示/日志里永远不要完整输出密钥：

```text
sk-demo-very-long-secret-key
→ sk-d…-key   （保留头尾少量字符，中间用 …）
```

短字符串（长度 ≤ 8）直接显示为 `***`，避免「脱敏后仍等于原文」。

## 6. 和 Agent 工程的关系

```text
进程启动
  → load_dotenv(".env")          # 本地开发便利
  → settings = load_llm_settings()  # require API Key
  → ChatClient(api_key=settings.api_key, ...)
  → 日志只打 mask_secret(api_key)
```

安全默认位：工具权限最小、密钥最小暴露面、配置与代码分离。

## 7. 今日一句话

> 密钥进环境，示例进 `.env.example`，真实 `.env` 永不提交；缺了就早死，打印就脱敏。

## 8. 明日预告

Day 10（下周一开始）：周挑战——多 API 聚合 CLI，会用到今天的加载与校验习惯。

---

## 我的记录（请自己填写）

1.  
2.  
3.  
