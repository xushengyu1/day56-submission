# 验证案例与实际结果

**执行日期：** 2026-07-17

**环境：** macOS，本地 PostgreSQL/pgvector，`AI_MODE=mock`，`EMBEDDING_MODE=mock`

**数据边界：** 仅合成账号、合成号码和程序生成图片

## 质量门禁

| 范围 | 实际命令 | 结果 |
|---|---|---|
| 后端全量 | `cd src/backend && ../../.venv/bin/pytest -q` | 244 passed |
| 后端静态检查 | `ruff check app tests scripts`、`mypy app` | 全部通过 |
| 数据库迁移 | `alembic upgrade head`、`alembic heads` | `20260717_0010 (head)` |
| 前端单测 | `cd frontend && npm test` | 110 passed |
| 前端质量 | `npm run typecheck && npm run lint && npm run build` | 全部通过 |
| 浏览器 E2E | 隔离 `_e2e` 数据库执行 `npm run test:e2e` | 4 passed |

## 浏览器端到端结果

| 用例 | 真实覆盖 | 结果 |
|---|---|---|
| `auth-home.spec.ts` | 注册、退出、登录、真实 API 请求、token 不持久化 | PASS |
| `matching-other.spec.ts` | 五类/五地点映射；类别/区域硬过滤；A101 比 A201 排名更高；问题核验；真实 claim ID；联系方式；拾得者确认交接 | PASS |
| `identity-admin.spec.ts` | 明确号码确认、用户框选脱敏、正确号码待交接、同账号两次错误锁定、管理员批准 claim、未匹配推荐候选、审计日志 | PASS |
| `security-failures.spec.ts` | 未认证 admin 401、普通用户 admin 403、跨用户原图 404、owner 原图 200；URL/storage/普通 payload/page 无 token 或完整号码 | PASS |

## 关键集成结论

1. `public_category` 的五类精确匹配与 `location_area` 的五区硬过滤在真实数据库上生效。
2. 楼栋/教室细节保留在公开描述中并影响 mock embedding 排序；隐藏描述没有进入候选公开 DTO。
3. 同一失物连续触发匹配时，候选组合保持唯一且 candidate ID 不变。
4. OTHER 全部关键题匹配后才进入 `PENDING_HANDOFF`；错误回答进入管理员复核。
5. 身份证使用服务端 HMAC 核验；两次失败后锁定，不由模型判断号码。
6. 管理员未匹配复核只能推荐候选，推荐后仍需走对应分类型核验，不能直接交接。

## 本轮发现并修复的缺陷

| 缺陷 | 证据 | 修复 | 回归 |
|---|---|---|---|
| 连续/相邻匹配生成重复候选 | 同一 `(lost, found)` 各出现 2 行，创建时间相差约 16ms | 唯一约束 + PostgreSQL upsert + 只删除过期未认领候选 | 相关集成测试 16 passed；全量 244 passed；OTHER E2E PASS |
| Vitest 收集 Playwright spec | 110 个单测通过后额外出现 4 个错误套件 | Vitest include 限定为 `tests/**/*.test.{ts,tsx}` | 15 files / 110 tests PASS |
| demo seed 测试无法导入 `scripts` | 标准 pytest 收集报 `ModuleNotFoundError: scripts` | 测试按精确文件路径加载脚本，不扩大生产包 | 后端全量 PASS |

## 未作出的声明

- 本次没有真实 MiMo 或 DashScope Key 的在线效果数据，因此不声明真实模型质量。
- E2E 证明受控软件流程和权限边界，不证明现实世界所有权、证件真伪或线下交接事实。
- React Router v7 future-flag 警告仍存在，但不影响当前 React Router v6 测试和构建。
