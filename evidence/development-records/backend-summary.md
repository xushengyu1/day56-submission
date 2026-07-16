# 后端 T00–T12 交付汇总

## 交付状态

| 任务 | 能力 | 聚焦验收 |
| --- | --- | ---: |
| T00 | FastAPI 健康检查与工程骨架 | 3 passed |
| T01 | PostgreSQL/pgvector 模型与 Alembic 迁移 | 10 passed |
| T02 | 状态机、评分、验证规则 | 52 passed |
| T03 | JWT/Refresh、密码哈希、RBAC/资源鉴权 | 14 passed |
| T04 | 脱敏审计、结构化日志、幂等 | 7 passed |
| T05 | 私有图片、校验、脱敏图与清理 | 7 passed |
| T06 | 多模态端口、OpenAI-compatible adapter、AI mock | 4 passed |
| T07 | FOUND 草稿、人工确认与安全发布 | 3 passed |
| T08 | LOST 创建、Top 5 候选和公共投影 | 4 passed |
| T09 | 身份证 HMAC 验证、次数限制、重复路由 | 3 passed |
| T10 | OTHER 问题验证与保守路由 | 3 passed |
| T11 | 用户复核请求与管理员幂等决定 | 3 passed |
| T12 | 联系授权、交接完成与角色时间线 | 3 passed |

每个任务的 Red/Green、回归和隐私证据见同目录 `T00.md` 至 `T12.md`。

## 最终质量门

- 全量测试：`122 passed in 4.84s`
- Ruff：`All checks passed!`
- Mypy：`Success: no issues found in 150 source files`
- Python 编译：`python -m compileall -q app tests` 退出 0
- 迁移：`downgrade base` 与 `upgrade head` 完整通过，前后 `alembic check` 无待生成迁移
- OpenAPI：29 个 paths，T12 三个接口均存在
- 运行态：PostgreSQL、AI mock 均 healthy
- Git：`git diff --check` 退出 0

## 对接入口

- Swagger UI：`http://localhost:8000/docs`
- OpenAPI：`http://localhost:8000/openapi.json`
- 环境变量示例：`src/backend/.env.example`
- 启动依赖：`docker compose up -d --wait postgres ai-mock`
