# 开发文档：AI 失物招领匹配与认领复核系统

> **文档版本：** V1.1
> **日期：** 2026-07-16  
> **状态：** 详细基线已恢复；V1.1 最小变更待增量 Review
> **需求基线：** `prd.md` V0.9
> **方案基线：** `design_option.md` V4.1，方案 A 已接受  
> **设计基线：** `docs/design/end-to-end-system-design.md` V1.4
> **执行清单：** `task.md` V1.1

本文定义开发阶段必须遵守的工程、接口、安全、测试和证据规则。本文不代表任何代码或运行测试已经完成；每项真实结果只能在对应任务执行后写入验证文档。

---

## 1. 开发目标与边界

### 1.1 本阶段目标

1. 交付一个 React Web 前端、FastAPI 服务端和 PostgreSQL + pgvector 数据库组成的可运行 MVP。
2. 跑通居民身份证与普通物品两条发布和认领路径，至少一条完整主流程达到 `CLAIMED/CLOSED`。
3. 真实触发 Top 5 候选评分、身份证 HMAC 核验、普通物品隐藏问题核验、多人认领路由、失主主动复核和交接状态机。
4. 对正常、边界、失败、误判和回归场景形成自动化结果与可追溯证据。
5. 明确区分真实外部模型、mock 模型、规则实现和人工确认，不用静态页面冒充系统能力。

### 1.2 不在本次开发范围

- 不开发 APP、小程序、学校统一认证、短信、找回密码和外部通知。
- 不实现证件真伪鉴定、法律归属判断、多人竞价式认领和完整申诉系统。
- 不使用图片向量做候选匹配；失主图片不进入多模态或评分。
- 不为 pgvector 建 ANN 索引；MVP 使用精确余弦查询。
- 不把居民身份证流程扩展到护照、学生证、驾驶证。
- 不把管理员变成默认可读取所有 PRIVATE 数据的超级查看者。
- 不实现复杂申诉；只实现未匹配复核与认领复核，管理员执行推荐候选、确认待交接或驳回。

### 1.3 开发阶段门

只有满足下列条件才可从当前任务进入下一任务：

1. 先存在针对目标行为的失败测试，且失败原因是功能尚未实现，而不是测试语法或环境错误。
2. 最小实现使目标测试通过。
3. 运行受影响模块回归测试并保持通过。
4. 更新实际测试结果和证据索引；未执行项目保持“未执行”。
5. 发生设计变化时先更新决策与设计文档，再修改接口或数据模型。

---

## 2. 技术基线与依赖策略

### 2.1 运行时

| 层 | 基线 | 约束 |
|---|---|---|
| Python | 3.11.x | 后端与测试统一版本 |
| Node.js | 20 LTS | 前端构建与 Playwright |
| PostgreSQL | 16.x | 启用 `vector` 扩展 |
| 浏览器 | Chromium | E2E 固定浏览器，答辩可使用 Chrome |
| 容器 | Docker Compose v2 | `postgres`、`backend`、`frontend`、可选 `ai-mock` |

### 2.2 Python 初始锁定版本

`backend/pyproject.toml` 声明下列直接依赖，`backend/uv.lock` 保存完整传递依赖锁。若某版本在实际镜像源不可安装，只允许在 Task 00 形成证据后做最小兼容调整并更新本节。

| 包 | 版本 | 用途 |
|---|---:|---|
| fastapi | 0.116.1 | API 与 OpenAPI |
| uvicorn | 0.35.0 | ASGI 服务 |
| pydantic | 2.11.7 | DTO/模型输出校验 |
| pydantic-settings | 2.10.1 | 配置 |
| sqlalchemy | 2.0.41 | 异步 ORM/事务 |
| asyncpg | 0.30.0 | PostgreSQL 驱动 |
| alembic | 1.16.4 | 迁移 |
| pgvector | 0.4.1 | SQLAlchemy vector 类型 |
| pyjwt | 2.10.1 | JWT |
| pwdlib[argon2] | 0.2.1 | 密码哈希 |
| python-multipart | 0.0.20 | 文件上传 |
| httpx | 0.28.1 | 模型/API 调用与测试 |
| pillow | 11.3.0 | 图片校验与脱敏 |
| pytest | 8.4.1 | 后端测试 |
| pytest-asyncio | 1.1.0 | 异步测试 |
| testcontainers[postgres] | 4.10.0 | PostgreSQL 集成测试 |

### 2.3 前端初始锁定版本

`frontend/package.json` 声明直接依赖，`frontend/package-lock.json` 为安装真源。

| 包 | 版本 | 用途 |
|---|---:|---|
| react / react-dom | 18.3.1 | Web UI |
| typescript | 5.8.3 | 类型检查 |
| vite | 6.1.0 | 构建与开发服务 |
| react-router-dom | 6.30.1 | 路由与守卫 |
| @tanstack/react-query | 5.83.0 | 服务端状态 |
| react-hook-form | 7.61.1 | 表单 |
| zod | 3.25.76 | 前端 schema |
| antd | 5.26.7 | UI 组件 |
| vitest | 3.2.4 | 单元/组件测试 |
| @testing-library/react | 16.3.0 | 组件行为测试 |
| @playwright/test | 1.54.1 | 端到端测试 |

### 2.4 外部 AI 与 mock

| 能力 | 首选模型 | MVP 降级 |
|---|---|---|
| 拾得图片提取 | MiMo-V2.5 图片理解 | 固定 JSON mock；失败后允许人工填写 |
| 隐藏问题生成/回答核验 | mimoV2.5-pro | 固定规则化 mock；失败不得自动放行 |
| 公开描述 embedding | text-embedding-v4 | 固定维度的确定性 hash embedding，仅用于离线演示并明确标注 mock |

所有模型经端口接口调用。业务代码不得直接依赖供应商 SDK 或把供应商原始响应返回前端。

---

## 3. 目标目录与职责

```text
day6/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/{deps.py,errors.py,router.py,routes/}
│   │   ├── auth/{models.py,schemas.py,service.py,security.py,rbac.py}
│   │   ├── items/{models.py,schemas.py,service.py,policies.py,state_machine.py}
│   │   ├── images/{models.py,schemas.py,service.py,storage.py,redaction.py}
│   │   ├── multimodal/{ports.py,schemas.py,openai_compatible.py,mock.py}
│   │   ├── matching/{models.py,schemas.py,embedding.py,scoring.py,service.py}
│   │   ├── verification/{models.py,schemas.py,identity.py,other.py,service.py}
│   │   ├── reviews/{models.py,schemas.py,service.py}
│   │   ├── audit/{models.py,schemas.py,service.py,projection.py}
│   │   ├── db/{base.py,session.py,enums.py}
│   │   └── core/{config.py,clock.py,ids.py,logging.py,idempotency.py}
│   ├── alembic/versions/
│   ├── tests/{unit,integration,contract}/
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── src/
│   │   ├── app/{router.tsx,providers.tsx,queryClient.ts}
│   │   ├── api/{client.ts,types.ts,errors.ts}
│   │   ├── components/
│   │   └── features/{auth,home,found-items,lost-items,candidates,claims,admin,audit}/
│   ├── tests/
│   ├── package.json
│   └── package-lock.json
├── e2e/{fixtures,seeds,specs}/
├── ai-mock/
├── storage/{private,public}/
├── evidence/{development-records,test-results,screenshots}/
├── docker-compose.yml
├── .env.example
├── dev.md
└── task.md
```

路由层只做身份解析、DTO 校验、调用服务和错误映射；领域服务负责事务与业务规则；纯函数放入对应模块；数据库模型不得直接作为 API 返回值。

---

## 4. 编码规范

### 4.1 Python

- 模块、函数和变量使用 `snake_case`；类型和 Pydantic 模型使用 `PascalCase`；常量使用 `UPPER_SNAKE_CASE`。
- 所有公共服务方法必须有类型注解；跨模块返回显式 DTO 或结果对象。
- `datetime` 一律存 UTC aware 时间，API 输出 ISO 8601；地点业务文本保留原输入，匹配字段单独规范化。
- 禁止在路由内写 HMAC、评分、状态转换或 SQL 拼装。
- 异常使用稳定错误码，错误响应不回显敏感输入。
- 对安全判断使用明确分支，不使用“异常时默认通过”。

### 4.2 TypeScript/React

- 开启 `strict`；禁止以 `any` 绕过 API 或表单类型。
- 页面只组合 feature hooks 和组件；API 调用集中到 `features/*/api.ts`。
- PRIVATE/VERIFICATION 值只保存在受控表单内存，不进入 URL、localStorage、sessionStorage、React Query 长期缓存或通用错误上报。
- 服务端状态是唯一业务真源；前端不得自行推断 `PENDING_HANDOFF`、`CLAIMED` 或管理员权限。
- 所有按钮禁用条件必须同时有服务端守卫测试，不能只靠 UI 禁用。

### 4.3 API

- API 前缀 `/api`，JSON 字段使用 `snake_case`。
- 写接口接受 `Idempotency-Key` 的场景：管理员决定、交接完成；同键同主体同请求返回同结果，不重复写事件。
- 并发更新通过 `expected_version` 或行锁保护；冲突返回 `409 VERSION_CONFLICT`。
- 认证失败 `401`，已认证但无权 `403`，资源不可见时优先用统一 `404` 防枚举。
- 候选、管理员、时间线分别使用角色投影 DTO，禁止复用“全字段详情 DTO”。

### 4.4 Git 与提交

- 每个 Task 至少一个可回退提交；推荐格式：`test(module): ...`、`feat(module): ...`、`docs(evidence): ...`。
- 不提交 `.env`、真实 API Key、真实证件、真实联系方式、上传原图和数据库卷。
- 红灯测试可短暂存在于工作区；提交前至少保证当前任务 Green，除非提交信息明确为测试基线且后续提交紧邻。

---

## 5. 配置与启动

### 5.1 必需配置

```text
APP_ENV
DATABASE_URL
JWT_SECRET
JWT_ACCESS_TTL_MINUTES
JWT_REFRESH_TTL_DAYS
ID_HMAC_KEY_V1
AI_MODE
MIMO_BASE_URL
MIMO_API_KEY
MIMO_MULTIMODAL_MODEL
MIMO_TEXT_MODEL
EMBEDDING_BASE_URL
EMBEDDING_API_KEY
EMBEDDING_MODEL
EMBEDDING_DIMENSION
PRIVATE_STORAGE_ROOT
PUBLIC_STORAGE_ROOT
MAX_UPLOAD_BYTES
MODEL_TIMEOUT_SECONDS
ORIGINAL_ACCESS_TTL_SECONDS
```

`AI_MODE` 仅允许 `real` 或 `mock`。启动日志必须打印模式与模型名，但不得打印 Key。`ID_HMAC_KEY_V1` 缺失、embedding 维度不一致或 PRIVATE/PUBLIC 目录重合时拒绝启动。

### 5.2 计划启动命令

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.db.seed_demo
```

预期：`GET /api/health/live` 返回 200；`GET /api/health/ready` 在数据库扩展、迁移与存储可用时返回 200。该结果必须在 Task 00 实际执行后记录。

---

## 6. 数据库与迁移顺序

迁移不得把全部表一次性堆入单文件。顺序固定为：

1. `0001_enable_vector_and_enums`：`vector` 扩展与数据库枚举。
2. `0002_users_and_refresh_tokens`：用户、refresh token。
3. `0003_item_records_and_images`：记录、图片、AI 提取。
4. `0004_identity_and_verification`：证件秘密、问题集与问题。
5. `0005_candidates_claims_reviews`：候选、申请、尝试、两类主动复核与管理员决定。
6. `0006_audit_and_idempotency`：审计事件、幂等结果。

每个迁移都必须通过空库 upgrade、完整 downgrade/upgrade 和模型 metadata 对齐检查。完整身份证号码和隐藏答案不得出现在迁移、seed 或 SQL 日志中。

### 6.1 业务枚举值

以下枚举值是前端下拉框与后端字段之间的稳定契约，seed 数据和接口响应必须使用相同值。

#### 地点枚举（`location_public`）

| 枚举值 | 标准化代码（`location_normalized`） | 说明 |
|---|---|---|
| `宿舍区` | `DORMITORY_AREA` | 学生宿舍楼区域 |
| `食堂` | `CANTEEN_AREA` | 校园食堂 |
| `教学楼` | `TEACHING_BUILDING` | 日常上课教学楼 |
| `科教楼` | `RESEARCH_BUILDING` | 科研/实验楼 |
| `图书馆` | `LIBRARY` | 校园图书馆 |

前端下拉框展示枚举值原样保存到 `location_public`（PUBLIC），同时后端生成标准化代码保存到 `location_normalized`（MATCH_ONLY）用于匹配评分。不支持自由输入。

#### 物品类别枚举（`public_category`）

| 枚举值 | 对应 `item_type` | 说明 |
|---|---|---|
| `电子产品` | `OTHER` | 手机、耳机、充电宝等电子设备 |
| `证件卡片` | `IDENTITY_DOCUMENT` | 居民身份证、校园卡、学生证等证件类 |
| `服饰配饰` | `OTHER` | 衣物、包袋、手表、眼镜等 |
| `学习用品` | `OTHER` | 书本、文具、U 盘等 |
| `其他` | `OTHER` | 以上分类未涵盖的物品 |

`public_category` 是 PUBLIC 字段（5 种），同时用于**候选匹配硬过滤**和前端展示。`item_type` 是决定认领核验流程的二分类（2 种）。当 `public_category` 为 `证件卡片` 时，`item_type` 强制为 `IDENTITY_DOCUMENT`；其余均为 `OTHER`。

**匹配规则：** 候选匹配以 `public_category` 精确匹配为硬门槛（5 种类别各自独立匹配），不同类别之间不能成为候选。`item_type` 决定认领核验分支（身份证件用 HMAC，其他物品用隐藏问题），不影响候选匹配范围。

**后端存储要求：** `item_records` 表必须同时存储 `item_type` 和 `public_category` 两个字段。`item_type` 用于核验流程分支，`public_category` 用于候选匹配过滤。两个字段独立存储，不能只存 `item_type` 然后靠代码推断 `public_category`（因为 `OTHER` 对应 4 种不同类别，推断不回来）。

#### 地点接近度评分映射

| 关系 | 得分 | 地点对 |
|---|---:|---|
| 同一地点 | 20 | 任意地点与自身 |
| 相邻建筑 | 14 | 教学楼 ↔ 科教楼；食堂 ↔ 宿舍区 |
| 同校园邻近 | 8 | 教学楼 ↔ 图书馆；食堂 ↔ 教学楼；宿舍区 ↔ 图书馆 |
| 明显无关 | 0 | 宿舍区 ↔ 科教楼；食堂 ↔ 科教楼；食堂 ↔ 图书馆 |

#### 时间接近度评分映射

| 条件 | 得分 |
|---|---:|
| 时间差 ≤ 1 小时 | 20 |
| 时间差 1～4 小时 | 12 |
| 同一天（时间差 ≤ 24 小时） | 6 |
| 跨日且无合理解释 | 0，标记冲突 |

---

## 7. 模块实现规则

### 7.1 M1 认证与会话

- 实现注册、登录、refresh；管理员由 seed 创建，不提供公开管理员注册。
- 密码使用 Argon2；refresh token 只保存不可逆摘要并可撤销。
- `USER` 与 `ADMIN` 是账号权限，失主/拾得者由资源关系判断。

### 7.2 M2 失物、Top 5 与未匹配复核

- 创建 LOST 后异步/同步生成公开描述 embedding；失主可选图片仅保存为 `OWNER_SUPPORT + PRIVATE`。
- 候选 SQL 硬过滤：`FOUND`、同 `public_category`、`PUBLISHED`、活动状态，方向必须与 LOST 相反。`public_category` 精确匹配（5 种），确保电子产品不会匹配到学习用品等跨类别物品。`item_type` 决定认领核验分支，不决定候选范围。
- 地点评分分两层：下拉框粗匹配（同值 20 / 相邻 14 / 邻近 8 / 无关 0）+ 详细描述语义相似度（在 50 分语义分中体现）。即使失主记错楼层或具体位置，只要详细描述语义接近仍可匹配。
- 评分固定：语义 50、时间 20、地点 20、完整度 10；返回 Top 5 安全解释，不返回内部距离与向量。
- Top 5 无合适候选时，记录创建者可提交一条活动 `UNMATCHED` 复核；请求保存理由和候选快照，不自动修改评分或创建 claim。

### 7.3 M3 招领发布

- 图片上传后先建 PRIVATE asset，再创建 FOUND 草稿。
- 多模态只写 `ai_extractions.raw_output_redacted` 与 `draft_snapshot`；拾得者确认后写 `confirmed_snapshot`。
- 身份证必须完成逐位确认和公开副本脱敏；OTHER 必须确认 2～3 个有效问题。
- 任一发布门槛不满足只可保存 DRAFT。

### 7.4 M4 分类型认领与认领复核

- 身份证：规范化 → 格式/校验位 → HMAC → 原子尝试计数 → 常量时间比较 → 重复活动记录检查。
- 同账号同候选最多 2 次；失败统一返回 `IDENTITY_NOT_VERIFIED`，第二次失败后返回/保持锁定语义但不泄露差异。
- 普通物品：问题文本可返回，答案键绝不返回；所有关键题均匹配、每题置信度 `>= 0.8`、模型结构有效且无其他活动认领时进入待交接，否则进入管理员复核。
- 候选分只用于 Top 5 排序，不与隐藏问题结果组合计算综合认领可信度。
- 核验失败、锁定、无法判断或失主不同意结果时，申请人可提交一条活动 `CLAIM_REVIEW`；原 HMAC/AI 结果不可覆盖。

### 7.5 M5 交接与记录

- 仅 `PENDING_HANDOFF` 且相关失主可读取拾得者联系方式。
- 只有对应拾得者可在正常路径确认 `handoff-complete`。
- 一次交接事务同时更新 claim、FOUND、LOST、联系授权和审计事件。

### 7.6 M6 管理员复核与审计

- P0 队列只包含五类：多人认领、普通物品核验未通过、证件核验异常、未匹配复核、认领复核。
- 默认 DTO 只包含掩码、规则/模型结果代码、事件和最小 VERIFICATION 证据；四级权限矩阵保持不变。
- 未匹配复核允许推荐候选或驳回；其它认领复核允许确认进入待交接或驳回，所有决定必须带理由。
- 原图临时授权为 P1；P0 未实现时 PRIVATE 始终脱敏，不允许直接暴露原图替代授权。
- 不实现完整身份证号码读取接口。

---

## 8. TDD 与测试策略

### 8.1 循环

```text
指定一个可观察行为
→ 写最小失败测试（Red）
→ 运行并确认失败原因正确
→ 写最小实现（Green）
→ 运行目标测试
→ 重构
→ 运行受影响模块和全量回归
→ 保存命令、结果、日志/截图和对应提交
```

### 8.2 测试层级

| 层级 | 目标 | 典型内容 |
|---|---|---|
| 后端单元 | 纯函数和状态规则 | ID 校验/HMAC/掩码、评分、状态机、问题质量规则 |
| 后端集成 | 真实 PostgreSQL、事务、RBAC、DTO | 发布不变量、2 次限制、多人认领、两类主动复核、权限、幂等、审计 |
| 模型契约 | 适配器输入输出和故障 | 合法/非法 JSON、超时、429、幻觉、低置信 |
| 前端组件 | 表单与角色交互 | 双入口、逐位确认、脱敏预览、错误/空状态、敏感状态清理 |
| API 联调 | 前后端契约 | 28 个接口的成功与错误码，OpenAPI 类型同步 |
| Playwright E2E | 完整用户价值 | 身份证主路径、普通物品主路径、多人认领、未匹配/认领主动复核 |
| 安全/回归 | 不泄露与历史行为 | DTO/日志/URL/storage 扫描、越权、并发、重复提交 |

### 8.3 测试数据

- 只使用合成号码、虚构联系方式、合成/脱敏图片。
- seed 固定五组：唯一身份证成功、普通物品全部匹配、多人认领转管理员、无合适候选主动复核、隐藏信息不足保持草稿。
- 每次 E2E 前重置 schema 并装载确定性 seed；测试不得依赖执行顺序。
- 模型 mock 响应按场景 ID 固定，保留模型元数据和调用事件。

### 8.4 质量门

| Gate | PASS 条件 | BLOCK 条件 |
|---|---|---|
| G1 契约 | OpenAPI、Pydantic、前端类型一致 | 缺接口、字段名冲突、错误码不稳定 |
| G2 隐私 | DTO/日志/URL/storage 扫描无完整号码、答案键、PRIVATE 路径 | 任一敏感值泄露 |
| G3 状态 | 所有非法转换被拒绝且有测试 | 可跳过待交接直接 CLAIMED |
| G4 核验 | 2 次限制、普通物品冲突/低置信、多人认领和两类主动复核均正确路由 | 失败/不确定/多人认领结果自动放行 |
| G5 E2E | 至少一条完整闭环和一条管理员失败路径通过 | 仅静态页面或数据库未真实改变 |
| G6 证据 | 命令、结果、截图、提交与文档可互相追溯 | 只有结论没有运行记录 |

---

## 9. 日志、审计与证据

### 9.1 普通日志允许内容

允许：`request_id`、路由模板、状态码、耗时、actor id 的不可逆内部标识、聚合 id、模型名、错误码。  
禁止：完整身份证号码、HMAC key、HMAC 值、隐藏答案、完整联系方式、原图路径/URL、token、模型未经清理的原始敏感响应。

### 9.2 审计事件最小字段

`event_id`、`event_type`、`actor_type`、`actor_id`、`aggregate_type`、`aggregate_id`、`request_id`、`occurred_at`、`rule_version`、`model_version`、`safe_payload`。

### 9.3 每个任务证据

每个 Task 完成后至少保存：

1. Red 命令与关键失败摘要；
2. Green 命令与通过数量；
3. 受影响回归命令；
4. 代码/迁移/页面文件路径；
5. 对应提交哈希或工作区变更摘要；
6. 决策变化时的 AI 日志与人工判断；
7. 可视功能的截图或视频索引。

统一写入 `evidence/development-records/TXX.md`，测试汇总同步到 `docs/validation/cases-and-results.md`。

---

## 10. 两天执行节奏

| 时间段 | 交付重点 | 阶段 Gate |
|---|---|---|
| Day 1 上午 | 工程骨架、数据库、认证、审计、安全纯函数 | G1/G2 基础通过 |
| Day 1 下午 | 图片/AI 适配、招领/失物、候选匹配 | 发布与候选集成测试通过 |
| Day 2 上午 | 双核验、两类主动复核、管理员决定、交接；三角色前端 | G3/G4 通过 |
| Day 2 下午 | E2E、失败注入、安全扫描、README、证据与答辩 | G5/G6 通过 |

时间不足时先保留：身份证完整闭环、普通物品匹配/不匹配、多人认领、两类主动复核、管理员决定和追溯时间线。优先降级：真实模型改 mock、管理员临时原图授权、自动图片框选、次要页面视觉优化。不得降级四级权限、号码保护、状态机或证据真实性。

---

## 11. 计划验证命令

```powershell
# 后端静态与测试
docker compose exec backend python -m ruff check app tests
docker compose exec backend python -m mypy app
docker compose exec backend pytest tests/unit -q
docker compose exec backend pytest tests/integration tests/contract -q

# 前端静态与测试
docker compose exec frontend npm run lint
docker compose exec frontend npm run typecheck
docker compose exec frontend npm run test -- --run

# 端到端
npx playwright test --config e2e/playwright.config.ts

# 数据库迁移回归
docker compose exec backend alembic downgrade base
docker compose exec backend alembic upgrade head

# 全量验收
docker compose exec backend pytest -q
docker compose exec frontend npm run test -- --run
npx playwright test --config e2e/playwright.config.ts
```

以上是执行阶段命令，不是已通过结果。实际命令如因容器工作目录变化而调整，必须同步 `README.md` 与证据记录。

---

## 12. Definition of Done

开发完成必须同时满足：

- [ ] 服务端、Web 前端和 PostgreSQL + pgvector 可按 README 一次启动。
- [ ] M1～M6 的 P0 接口已实现，OpenAPI 与前端类型一致。
- [ ] 居民身份证主路径真实到达 `CLAIMED/CLOSED`。
- [ ] 普通物品全部关键题匹配或转管理员路径可运行。
- [ ] Top 5 无合适候选和认领核验失败时，失主可分别提交两类主动复核。
- [ ] 多人认领同一招领记录时不提前展示联系方式，由管理员确认或驳回。
- [ ] 2 次限制、重复号码、模型失败、隐藏信息不足和越权场景有真实结果。
- [ ] 候选只暴露 PUBLIC，完整号码、答案键、PRIVATE 路径不泄露。
- [ ] 单元、集成、契约、组件、E2E 和回归测试均有实际记录。
- [ ] README 清楚区分 real/mock/手工降级/未实现。
- [ ] AI 协作的实现、验证和 Review 记录含目的、输入、建议、人工判断、验证。
- [ ] 证据链可从需求 → 设计 → Task → 测试 → 截图/日志 → 最终状态双向追溯。
