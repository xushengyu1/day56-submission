# Qwen3.7 文本向量接入设计

## 目标

将生产环境的文本向量模型切换为阿里云百炼 `qwen3.7-text-embedding`，统一使用 1024 维稠密向量，同时保持测试离线、确定、无额度消耗。API Key 仅由运行环境提供，不进入 Git、日志或错误响应。

## 范围

- 为 embedding 定义最小端口，并提供 DashScope 与确定性 mock 两个实现。
- LOST 创建和 FOUND 发布通过所选 adapter 生成向量，并持久化真实模型名与维度。
- 候选计算只比较模型名、维度均一致的向量。
- 提供一次性批量重算命令，将已有已发布 LOST/FOUND 记录更新为新模型向量。
- 更新依赖、环境变量示例、测试和开发证据。

不在本次范围内：稀疏向量、混合检索、rerank、多地域自动探测、后台任务队列。

## 配置

- `EMBEDDING_MODE`：`mock` 或 `dashscope`。测试默认 `mock`；真实环境显式设置为 `dashscope`。
- `DASHSCOPE_API_KEY`：仅通过环境变量读取，示例文件保留空值。
- `EMBEDDING_MODEL`：默认 `qwen3.7-text-embedding`。
- `EMBEDDING_DIMENSION`：真实运行配置固定为 `1024`；DashScope 模式拒绝其他值。单元测试可为 mock 显式指定小维度。

不把用户提供的 Key 写入 `.env`、`.env.example`、测试 fixture、命令记录或证据文件。由于 Key 已在对话中出现，交付时提醒轮换。

## 组件与数据流

### Embedding 端口

定义一个仅负责批量文本向量化的端口：输入非空文本列表，输出与输入顺序一致的 `list[list[float]]`，并暴露 `model` 与 `dimension`。业务服务依赖端口，不直接依赖 DashScope SDK。

### DashScope adapter

adapter 使用 `dashscope.TextEmbedding.call`，传入模型、文本列表、1024 维和环境中的 API Key。单次最多发送 20 条文本；重算命令按此限制分批。

adapter 必须验证：

- HTTP 状态为成功；
- `output.embeddings` 存在且数量与输入一致；
- 根据响应中的文本索引恢复输入顺序；
- 每个 embedding 均为 1024 个有限数值。

SDK 异常、非成功状态和响应结构错误统一抛出稳定的 `EmbeddingError`，错误内容不包含 Key、输入全文或原始响应。

### Mock adapter

测试使用现有 hash 算法生成确定且归一化的向量，但通过同一端口调用，并明确标记模型为 `mock-hash-v1`。mock 的维度由测试指定，不能冒充真实 Qwen 模型。

### 业务服务

- 创建 LOST 时，用 adapter 对公开名称、公开描述和公开地点组成的文本生成向量。
- 发布 FOUND 时使用相同拼接规则和 adapter。
- 保存 `embedding`、adapter 的 `model` 与 `dimension`，三者作为一个一致快照。
- 候选查询只加载与 LOST 的 `embedding_model`、`embedding_dimensions` 一致的 FOUND，避免混合 8 维与 1024 维向量。
- 外部模型失败时不发布或创建半成品记录，向 API 返回稳定错误码。

同步 DashScope SDK 调用通过线程卸载执行，避免阻塞 FastAPI 事件循环。

## 现有数据重算

提供显式命令，筛选已有 embedding 模型或维度不匹配的已发布 LOST/FOUND，按 20 条分批调用 adapter，并在事务中更新向量快照。命令支持重复执行：已是目标模型和 1024 维的记录跳过。

重算不是 Alembic schema migration：数据库的 `vector` 列未限制固定维度，无需修改表结构；把外部 API 调用放入迁移会导致部署不可重复。

重算完成前，候选逻辑会忽略不兼容向量，不会发生维度异常。

## 测试策略

严格执行 Red → Green：

1. adapter 成功响应测试：顺序、数量、1024 维。
2. adapter 失败测试：非成功状态、缺失字段、维度错误均得到稳定异常，且异常不含敏感信息。
3. service 测试：LOST/FOUND 保存 adapter 的模型和维度；候选忽略不兼容向量。
4. 重算测试：只更新旧记录、按批处理、重复执行无额外调用。
5. 配置测试：DashScope 模式缺少 Key 时快速失败，mock 模式无需 Key。
6. 聚焦测试通过后运行全量 pytest、Ruff、Mypy、compileall 与 `git diff --check`。

真实 API 只做可选人工 smoke test，自动化测试不会使用用户 Key 或访问外网。

## 验收标准

- 真实模式生成的记录标记 `qwen3.7-text-embedding` 和 `1024`。
- 所有向量数量、顺序和维度均经过校验。
- 缺少 Key 或模型失败时无半成品写入，无敏感信息泄漏。
- 新旧维度共存期间候选计算不会报错。
- 重算命令可安全重复运行，完成后已有发布记录均为目标模型和维度。
- 全量测试与静态检查通过。
