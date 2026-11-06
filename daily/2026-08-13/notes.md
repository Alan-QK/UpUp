# Day 18 笔记｜模型 Provider 抽象

## 1. 今天学什么？

前几天你已经会调 OpenAI 兼容接口了。下一步常见坑是：

```text
persona_assistant.py 直接 new ChatClient(...)
sampling_lab.py 也直接绑死 httpx + /chat/completions
→ 换厂商 / 写单测 / 本地 demo = 到处改
```

今天要练的是前端同学最熟的招数：**面向接口编程**。

| 概念 | 前端类比 | 今天对应 |
|------|----------|----------|
| 接口 / 协议 | `interface ChatService` | `ChatProvider`（Protocol） |
| 真实实现 | 调后端 API 的 adapter | `OpenAICompatProvider` |
| Mock | MSW / jest mock | `FakeChatProvider` |
| 工厂 / DI | `createClient(env)` | `create_chat_provider(kind, ...)` |

## 2. 为什么是 Protocol，不是硬继承？

Python 的 `typing.Protocol` 是**结构化类型**（duck typing + 类型检查友好）：

- 只要对象有约定的方法/属性，就算实现了协议
- 不必 `class X(Base)` 强行绑继承树
- 方便给「别人写的客户端」套一层适配，而不改源码

今天约定的最小能力：

```text
ChatProvider
  · name: str
  · complete(messages, *, temperature=None, top_p=None) -> ChatCompletionResult
  · close() -> None
```

先别急着把流式、tool call 塞进接口——**接口越小，替换成本越低**。流式可以以后再拆 `StreamingChatProvider`。

## 3. Fake 不是玩具，是工程部件

`FakeChatProvider` 要解决三件事：

1. **确定性回复**：按「最后一条 user 内容」查表，未命中用默认句  
2. **可观察**：把每次 `complete` 的入参记进 `.calls`，测试好断言  
3. **零网络**：不引入 httpx，CI 稳定、不花 token

以后写 Agent Loop / Prompt 修复重试时，你会天天用它。

## 4. 工厂：唯一知道厂商细节的地方

```text
create_chat_provider("fake", model=..., default_reply=..., replies=...)
create_chat_provider("openai", model=..., api_key=..., base_url=..., transport=...)
```

上层（CLI、Assistant、评测脚本）只拿 `ChatProvider`：

```python
provider = create_chat_provider(kind, ...)
try:
    result = provider.complete(messages)
finally:
    provider.close()
```

换国产兼容接口时，多数情况只是换 `base_url` + `api_key` + `model`；  
真遇到协议差异，再加一个新 Provider 类，而不是改业务。

## 5. 和 Agent 工程的关系

```text
Agent / Assistant
    ↓ 只依赖
ChatProvider  (协议)
    ↓ 可替换
Fake | OpenAICompat | (未来) AnthropicAdapter | LocalModelAdapter
```

收益：

- 单测不打网
- Demo 日可以 `--provider fake`
- 里程碑 `cli-chatbot` 换模型时改配置即可
- 评测脚本可对同一套轨迹换 Provider 复跑

## 6. 今日一句话

> 把「怎么调模型」关进 Provider；业务只认 `complete`，测试只认 Fake。

## 7. 明日预告

Day 19：结构化日志与调试——给聊天链路打上可检索的事件日志。

---

## 我的记录（请自己填写）

1.  
2.  
3.  
