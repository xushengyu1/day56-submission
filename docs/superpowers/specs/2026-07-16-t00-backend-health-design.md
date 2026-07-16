# T00 后端工程骨架与健康检查设计

## 背景

当前 `day56-development` 从 `master` 创建，主线只有 PRD、技术方案和任务文档，没有可运行的后端源文件。`codex/t001-health-scaffold` 的提交 `64cb913` 提供了可参考的 FastAPI 依赖组织和数据库检查思路，但其 `/health` 路径、Python 版本约束和认证模型与当前 V1.1 文档不完全一致。

本设计只覆盖 `task-backend.md` 的 T00，不恢复旧分支的业务模块。

## 目标与边界

T00 完成后，后端具备可测试的最小 FastAPI 入口、配置读取和存活/就绪检查：

- `GET /api/health/live` 返回 HTTP 200 和 `{"status":"ok"}`。
- `GET /api/health/ready` 在数据库检查成功时返回 HTTP 200 和 `{"status":"ok"}`。
- `GET /ready` 作为任务文档兼容别名，复用同一个就绪处理函数。
- 数据库不可用时就绪接口返回 HTTP 503 和稳定的 `{"status":"unavailable"}`，不泄露异常文本。
- 测试可以替换数据库检查函数，不依赖本地 PostgreSQL。

T00 不包含认证、数据模型、Alembic 迁移、图片、AI、前端、Docker 全栈编排或业务 API。

## 方案选择

1. 直接复制旧分支 T00：实现快，但会带入旧的 `/health` 接口和不一致的运行时约束，后续需要返工。
2. 按当前 V1.1 重新实现最小后端 T00：只复用旧分支的依赖组织和数据库检查思路，接口以当前 `dev.md`/`task.md` 为准，并保留 `/ready` 别名。该方案改动最小、边界最清楚，选用此方案。
3. 一次性恢复旧分支全部后端：功能面大，但违反逐模块 Red-Green 节奏，无法逐项证明任务完成，不采用。

## 组件与数据流

- `src/backend/app/settings.py`：读取 `APP_ENV` 和 `DATABASE_URL` 等 T00 所需配置，提供默认的本地测试值；不提前校验后续任务的 JWT、HMAC、AI 和存储配置。
- `src/backend/app/health.py`：定义 health 响应模型、数据库检查端口和两个路由路径。路由只把检查成功/失败映射为 HTTP 状态码和稳定错误体。
- `src/backend/app/main.py`：创建 FastAPI 应用并注册 health 路由。
- `src/backend/tests/unit/test_health.py`：通过 FastAPI `TestClient` 和可替换检查函数覆盖 live、ready 成功和 ready 失败。

就绪请求的数据流为：路由调用异步数据库检查 → 成功返回 200；捕获数据库连接/查询异常 → 返回 503，不把异常消息写入响应。

## 依赖与兼容性

- 代码放在当前仓库实际目录 `src/backend`。
- `pyproject.toml` 保持 Python 3.11+ 兼容；依赖遵循 `dev.md` 的 FastAPI、Pydantic、SQLAlchemy、asyncpg、pytest 基线，实际安装结果以本机环境验证为准。
- 不复制旧分支的业务源码；后续任务若需要，再逐模块从旧分支提取并用当前任务的测试重新验证。

## 验证标准

严格执行以下顺序：

1. 先新增 health 测试并运行，确认因入口不存在或行为缺失而失败。
2. 写满足失败测试的最小实现，再运行 `pytest tests/unit/test_health.py -q`。
3. 使用 `TestClient` 直接验证两个就绪路径的功能行为，并运行当前后端全量测试（当前仅有 T00 测试）。
4. 将命令、输出、环境限制和未执行项写入 `evidence/development-records/T00.md`，再判断是否进入 T01。

## 未决事项

T00 不决定后续认证方式、数据库迁移结构、真实配置必填项和 Docker 服务编排；这些内容分别由 T01、T03、T04/T06 及最终部署任务按 PRD 和详细设计继续锁定。
