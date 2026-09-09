# RAG 笔记

RAG（Retrieval-Augmented Generation）先检索相关文档片段，
再让大模型基于片段生成答案，从而降低幻觉。

向量检索常用 cosine 相似度做 top-k；命中结果要带 source 元数据，
方便后面做引用溯源。

Chroma 的心智模型是 Client → Collection → add / query。
