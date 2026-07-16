# T06 AI 适配器实施计划

**Goal:** 完成供应商无关的模型端口、固定 mock、OpenAI 兼容实现和确定性 embedding。

## Task 1：契约 DTO 与端口

- [x] 写 `tests/contract/test_extraction_contract.py`、`test_question_contract.py` Red 测试
- [x] 实现 ports/schemas 和固定错误码
- [x] 运行契约测试

## Task 2：mock 与 embedding

- [x] 写 verification/embedding 契约 Red 测试
- [x] 实现 mock、fixtures、确定性 embedding
- [x] 运行契约测试

## Task 3：OpenAI 兼容适配器

- [x] 写错误/非法 JSON 边界测试
- [x] 实现 timeout、有限重试和 schema 解析
- [x] 运行 adapter 单元测试

## Task 4：回归、证据、提交

- [x] 更新 `evidence/development-records/T06.md`
- [x] 运行 T06 contract、全量 pytest、compileall、diff check
- [x] 提交 `feat(ai): add validated openai compatible ports and deterministic mock` 并推送
