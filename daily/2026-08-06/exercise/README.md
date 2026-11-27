# Exercise · Day 13 流式终端聊天打印

## 依赖

```bash
python3 -m pip install --user httpx pytest
```

## 你要做的事

1. 完成 [`streaming_client.py`](./streaming_client.py) 里的 TODO：
   - `parse_sse_data_line`：从一行文本抽出 SSE payload
   - `extract_delta_text`：从 chunk JSON 取 `delta.content`
   - `StreamingChatClient.iter_content`：`stream: true` + 逐行解析
   - `print_stream`：边打印边 flush，返回全文
2. 构造器 / `close` / 上下文管理 **已给齐**，不必改
3. [`main.py`](./main.py) 已给齐：`--demo` 离线流式试跑

## 验证

```bash
cd daily/2026-08-06/exercise
python3 -m pytest -q
python3 main.py --demo
python3 main.py --demo -m "解释一下 delta.content"
```
