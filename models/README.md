# 模型与运行模式

当前提交默认使用 `char-tfidf-2-4-v1`，它不是生成式大模型，而是完全本地的字符 n-gram TF-IDF
向量器。回答采用“证据抽取模式”，会明确显示原文和来源，不把抽取结果冒充模型生成。

课程推荐的可选模型（本仓库不分发模型权重）：

| 用途 | 模型 | Revision | License |
|---|---|---|---|
| 中文 Embedding | BAAI/bge-small-zh-v1.5 | `7999e1d3359715c523056ef9478215996d62a620` | MIT |
| 本地生成 | Qwen/Qwen2.5-1.5B-Instruct | `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` | Apache-2.0 |
| 低内存生成 | Qwen/Qwen2.5-0.5B-Instruct | `7ae557604adf67be50417f59c2c2f167def9a775` | Apache-2.0 |

若后续接入模型，必须固定 Revision，预下载后使用 `local_files_only=True`，并设置
`HF_HUB_OFFLINE=1` 与 `TRANSFORMERS_OFFLINE=1` 验证断网启动。

