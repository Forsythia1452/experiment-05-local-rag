# 第三方资源与许可证

- Streamlit 1.50.0，Apache-2.0，用于界面。
- scikit-learn 1.7.2，BSD-3-Clause，用于字符 n-gram TF-IDF 本地向量化。
- FAISS 1.13.2，MIT，用于内积向量索引；不可用时退化为 NumPy 精确检索。
- pypdf 5.9.0，BSD-3-Clause，用于 PDF 文本解析。
- NumPy 2.3.3，BSD-3-Clause，用于数值计算。
- 示例知识库由侯宇晴为本实验原创，随项目按 MIT 许可证发布。

本实现参考实验指导书给出的 RAG 分层设计，不复制第三方项目源代码。推荐但未随仓库分发的模型
`BAAI/bge-small-zh-v1.5` 与 `Qwen/Qwen2.5-1.5B-Instruct` 记录于 `models/README.md`。

