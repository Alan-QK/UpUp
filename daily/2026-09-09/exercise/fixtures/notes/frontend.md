# 前端对接 Agent

前端可用 SSE 展示流式回答，并在侧栏列出引用的 chunk 来源。
工具调用时可显示 tool_start / tool_end，让用户知道 Agent 在干什么。
取消请求用 AbortController；会话用 session_id 续聊。
