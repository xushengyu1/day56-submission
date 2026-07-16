# T06 AI 适配器与模型契约设计

## 目标

隔离 OpenAI 兼容供应商细节，提供固定的提取、问题生成、回答核验和 embedding 接口。所有外部 JSON 先经过 schema 校验和敏感字段清理；模型失败、低置信或结构非法只返回可追踪的失败/未确定结果，不自动放行。

## 方案

- `multimodal/ports.py`：供应商无关的 Protocol 与稳定 `ModelAdapterError`。
- `multimodal/schemas.py`：`ExtractionDraft`、`VerificationResult`、模型元数据和安全字段 DTO；问题集复用 T02 的 `QuestionSetDraft`。
- `multimodal/openai_compatible.py`：同步 `httpx.Client`，固定 timeout、最多一次重试，只接受 JSON object；供应商原始响应不向业务层泄漏。
- `multimodal/mock.py`：按 scenario ID 返回仓库内固定合成 fixture，显式标记 `provider=mock`、`version=fixture-v1`。
- `matching/embedding.py`：对确认后的公开文本做 SHA-256 分桶并 L2 归一化；维度由配置锁定，明确仅用于离线 mock，不伪装为真实模型。

## 安全与失败策略

- 图片提取只接收 `image_ref`，不把 PRIVATE 文件路径写入日志或输出；身份证号码候选只存在于本次人工确认草稿，adapter 不持久化完整号码。
- 问题生成结果必须满足 T02 的 2～3 个开放题规则；答案键不会出现在返回 DTO 的 public 字段。
- 回答核验单题置信度低于 `0.8` 或出现冲突时返回 `UNDETERMINED/CONFLICT`，由后续服务转人工。
- HTTP 4xx/5xx、超时、非法 JSON 和 schema 错误统一为 `ModelAdapterError`，包含稳定 code 和 provider/model/version，不含请求 token 或原始响应。

## 配置

增加 `AI_MODE`（`mock`/`real`）、兼容 API base URL/key/model、embedding dimension 和模型 timeout；测试默认 mock，生产禁止缺失 key 或 dimension 不一致。

## 验证

- contract：提取、问题、核验、embedding 四组契约；固定 fixture 可重复。
- failure：非法 JSON、低置信、超时/错误码和维度错误均不自动通过。
- 全量：T00–T05 回归、compileall、diff check。
