# AI 失物招领匹配与认领复核系统

React + FastAPI + PostgreSQL/pgvector 的可运行 MVP。系统使用公开文本生成候选，按类别和区域硬过滤；普通物品走隐藏问题核验，居民身份证走服务端 HMAC 精确核验；异常和主动申请进入管理员复核，实际交接只能由拾得者确认。

## 当前状态

截至 2026-07-17，前后端真实接口、数据库迁移和 4 条 Playwright 浏览器流程已联调通过。默认开发与 E2E 使用 `AI_MODE=mock`、`EMBEDDING_MODE=mock`，不会把 mock 结果描述成真实外部模型效果。

公开分类固定为：

- 电子产品 / 证件卡片 / 服饰配饰 / 学习用品 / 其他

公开区域固定为：

- 宿舍区 / 食堂 / 教学楼 / 科教楼 / 图书馆

楼栋、楼层、教室等细节写入公开描述并参与 embedding；隐藏核验信息不进入公开文本或向量。

## 本地启动

前置条件：Docker、Python 3.12、Node.js 和 npm。

```bash
docker compose up -d postgres ai-mock

python3 -m venv .venv
.venv/bin/pip install -e 'src/backend[dev]'

cd src/backend
../../.venv/bin/alembic upgrade head
../../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开终端启动前端：

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

访问 `http://127.0.0.1:5173`。后端环境变量模板位于 `src/backend/.env.example`；真实部署必须替换 JWT 与 HMAC 密钥。

## 验证

后端：

```bash
cd src/backend
../../.venv/bin/alembic upgrade head
../../.venv/bin/pytest -q
../../.venv/bin/ruff check app tests scripts
../../.venv/bin/mypy app
../../.venv/bin/alembic heads
```

前端：

```bash
cd frontend
npm test
npm run typecheck
npm run lint
npm run build
```

真实浏览器 E2E 使用独立的 `lost_found_e2e` 数据库。全局 setup 只允许 `APP_ENV=e2e` 且数据库名以 `_e2e` 结尾，然后自动迁移、清空应用表、写入合成账号和生成合成图片：

```bash
cd frontend
APP_ENV=e2e \
DATABASE_URL=postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found_e2e \
npm run test:e2e
```

2026-07-17 的实际结果：

- 后端：244 passed；Ruff、mypy 通过；Alembic `20260717_0010 (head)`
- 前端：110 passed；typecheck、lint、build 通过
- Playwright：4 passed，覆盖认证、OTHER 匹配认领交接、身份证核验与管理员复核、安全边界

详细结果见 `docs/validation/cases-and-results.md`。

## 安全边界

- 完整身份证号仅发送到 identity-confirmation 请求体，服务端校验后保存 HMAC 与掩码。
- token 仅保存在浏览器内存，不进入 URL、localStorage 或 sessionStorage。
- 原图为 PRIVATE；跨用户读取返回 404；管理员角色本身不自动获得任意原图权限。
- PUBLIC 身份证图片必须经过用户框选脱敏并确认。
- 候选、隐藏问题、管理员决定和交接均有服务端授权与状态约束。
- `(lost_record_id, found_record_id)` 有唯一约束，重复或并发匹配使用 upsert，避免重复候选。

## 真实实现与模拟边界

| 能力 | 当前实现 |
|---|---|
| Web、API、PostgreSQL 状态变化 | 真实实现并通过 E2E |
| 认证、RBAC、审计、幂等 | 真实实现 |
| 身份证号码核验 | 服务端确定性校验 + HMAC，不调用 LLM |
| 图片上传与脱敏 | 真实文件与服务端处理；E2E 只使用生成的合成图片 |
| mock AI / embedding | 默认可复现测试路径 |
| MiMo / DashScope 适配器 | 已实现接口与失败处理；本轮未用真实 Key 做效果声明 |
| 现实世界所有权和证件真伪 | 不在 MVP 可证明范围内 |

## 目录

- `src/backend/`：FastAPI、SQLAlchemy、Alembic、测试与 seed
- `frontend/`：React、Vitest、Playwright
- `docs/`：需求、设计、验证和复盘
- `evidence/development-records/`：实际开发与验证记录
- `prototype/`：早期静态原型，仅作设计参考
