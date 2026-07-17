# Qwen3.7 文本向量迁移证据

## 范围

- 分支：`feature/backend`
- 目标模型：`qwen3.7-text-embedding`
- 真实向量维度：1024
- SDK：`dashscope==1.26.3`
- 自动化测试模式：确定性 `mock-hash-v1`，不访问外网、不消耗额度

## TDD 记录

### Adapter 与配置

Red：新增 adapter/factory 测试后运行，因 `app.matching.dashscope_embedding` 不存在产生 2 个收集错误。

Green：

```bash
../../.venv/bin/pytest tests/unit/matching/test_dashscope_embedding.py tests/unit/matching/test_embedding_factory.py tests/contract/test_embedding_contract.py -q
```

结果：`18 passed`。覆盖乱序恢复、1024 维、批量上限、非有限数值、异常脱敏、缺 Key 和非法真实配置。

### LOST、FOUND 与匹配

Red：四个业务测试因服务尚不接受 `embedding_adapter` 失败。

Green：

```bash
../../.venv/bin/pytest tests/integration/matching tests/integration/items -q
../../.venv/bin/pytest tests/contract tests/unit/matching -q
```

结果：分别 `10 passed` 和 `33 passed`。LOST/FOUND 保存 adapter 的真实模型与维度；失败时不创建 LOST、不发布 FOUND；候选 SQL 只比较模型、维度一致的记录。

### 历史数据重算

Red：测试因 `app.matching.reembed` 不存在产生 1 个收集错误。

Green：重算测试 `3 passed`，完整 matching 目录 `9 passed`。21 条旧 PUBLISHED 记录分为 `[20, 1]` 两次调用；DRAFT/CLAIMED 不变；第二次执行更新数为 0 且无额外模型调用。

## 最终质量门

```bash
../../.venv/bin/pytest -q
../../.venv/bin/ruff check .
../../.venv/bin/mypy .
../../.venv/bin/python -m compileall -q app scripts tests
../../.venv/bin/alembic check
git diff --check
```

结果：

- Pytest：`145 passed in 5.37s`
- Ruff：`All checks passed!`
- Mypy：158 个源文件无问题
- compileall、diff check：退出 0
- Alembic：`No new upgrade operations detected`

```bash
docker compose up -d --wait postgres ai-mock
docker compose ps
../../.venv/bin/python -m pip check
```

结果：PostgreSQL 与 AI mock 均为 healthy；依赖无损坏；mock 工厂输出 `mock-hash-v1 1024`。

## 安全检查

- tracked 文件扫描未发现用户 Key 前缀或非空 `DASHSCOPE_API_KEY=`。
- staged diff 扫描无匹配。
- adapter 异常只暴露稳定错误码，不包含 Key、输入原文、SDK 异常或原始响应。
- 自动化测试使用 `test-key` 和 monkeypatch，不发真实网络请求。
- 用户提供的 Key 已在对话中暴露，真实部署前必须撤销并生成新 Key。

## 运行配置与重算

使用轮换后的 Key，通过终端隐藏输入：

```bash
export EMBEDDING_MODE=dashscope
read -rsp 'DashScope API Key: ' DASHSCOPE_API_KEY
export DASHSCOPE_API_KEY
export EMBEDDING_MODEL=qwen3.7-text-embedding
export EMBEDDING_DIMENSION=1024
cd src/backend
../../.venv/bin/python -m scripts.reembed_records
```

命令仅输出 `reembedded=<count>`。重算完成前，不兼容的旧向量会被候选查询忽略，不会发生维度计算错误。

## 提交

- `3c0de8a5 feat(embedding): add validated dashscope adapter`
- `ed454c51 feat(matching): persist compatible qwen embedding snapshots`
- `ec6c9e53 feat(embedding): add idempotent qwen reembedding command`
