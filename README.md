# AI 失物招领匹配与认领复核系统

React + FastAPI + PostgreSQL/pgvector 的可运行 MVP。系统使用公开文本生成候选，按类别和区域硬过滤；普通物品走隐藏问题核验，居民身份证走服务端 HMAC 精确核验；异常和主动申请进入管理员复核，实际交接只能由拾得者确认。

## 当前状态

截至 2026-07-17，前后端真实接口、数据库迁移和 4 条 Playwright 浏览器流程已联调通过。默认开发与 E2E 使用 `AI_MODE=mock`、`EMBEDDING_MODE=mock`，不会把 mock 结果描述成真实外部模型效果。

公开分类固定为：

- 电子产品 / 证件卡片 / 服饰配饰 / 学习用品 / 其他

公开区域固定为：

- 宿舍区 / 食堂 / 教学楼 / 科教楼 / 图书馆

楼栋、楼层、教室等细节写入公开描述并参与 embedding；隐藏核验信息不进入公开文本或向量。

## 团队分工与工作职责

以下分工依据宋姿毅新版 AI 协作日志（记录 1～48）、
`codex/t001-health-scaffold` 分支的 `ai-log.md`，以及 `master` 中
`evidence/development-records/` 的实际开发和验证记录归纳。职责按主责划分，
共同决策和联调工作单独说明，不以 Git 作者信息机械代替个人贡献。

### 宋姿毅

**主要职责：产品方案、文档体系、前端实现与联调规则设计。**

- 负责需求分析和 MVP 范围收敛，定义失主、拾得者、管理员的职责边界，以及
  “发布—匹配—核验—复核—交接—审计”的核心业务闭环。
- 主导 PRD、方案比较和详细设计迭代，维护 Goals / Non-Goals、状态机、接口
  规划、失败回退、Design Review、TDD 任务拆分和过程证据。
- 将徐胜宇提出的四级数据分类工程化写入 PRD、详细设计、DTO、AI 输入、日志和
  测试规则，形成可执行、可验证的数据权限边界。
- 负责 AI 产品边界设计，包括候选匹配不等于归属确认、受控多模态结果必须经
  人工确认、隐藏特征生成开放式问题、模型失败转人工，以及身份证号码不进入
  LLM 和向量。
- 负责候选评分和核验规则的产品定义，包括类别硬过滤、公开语义/时间/地点/
  完整度评分，以及高可信结果最多进入“待交接”、不能直接标记“已认领”。
- 负责前端 UI、原型和 React 页面实现，覆盖认证与路由守卫、拾得者发布向导、
  失物发布与 Top 5 候选、两类认领核验、认领进度、管理员复核和审计页面。
- 负责前后端联调前的契约梳理和前端对齐，包括五类物品与五个校园区域枚举、
  `public_category` 硬过滤、字段/状态命名、email 登录、全系统最新动态和自己/
  他人寻物权限差异。
- 负责前端 SSE 匹配进度接入、隐藏信息表单、管理员队列筛选，以及页面操作与
  后端 API 的逐项映射，为后续真实接口替换 Mock 流程提供明确边界。
- 参与运行环境和 AI 能力落地排查，包括 embedding 配置、一次性种子数据枚举
  修正、Qwen 模型切换、中文提示词和“物品主体/背景”识别约束；同时记录直接
  调用验证与 HTTP 集成验证之间的边界。
- 设计 AI 服务熔断与降级规则，明确图片理解、向量生成、问题生成和回答核验
  失败时分别回退到手工填写、匹配失败、稍后重试或管理员复核。
- 负责项目说明、方案取舍、个人 AI 协作记录和汇报材料的整理，区分设计结论、
  模拟能力和真实运行验证，避免把计划或 Mock 结果写成已验证事实。

### 徐胜宇

**主要职责：后端工程、前后端联调与质量交付。**

- 负责 FastAPI 工程骨架、健康检查、配置管理，以及 PostgreSQL/pgvector、
  SQLAlchemy、Alembic 和数据库运行环境的建立与维护。
- 负责认证与安全基础能力，包括密码哈希、JWT/Refresh、RBAC、资源归属校验、
  四级数据访问控制、敏感字段投影、结构化审计和幂等处理。
- 负责失物与招领后端业务，包括图片资产隔离、招领草稿与发布、公开文本向量、
  Top 5 候选匹配、候选快照和重复匹配 upsert。
- 负责认领和复核闭环，包括身份证 HMAC 精确核验与尝试限制、普通物品隐藏问题
  核验、异常转管理员、管理员决定、联系方式授权、拾得者确认交接和角色化时间线。
- 负责把前端 Mock 流程接入真实类型化 API，完成登录会话、记录页面、图片上传、
  匹配、认领、管理员复核和交接流程的前后端契约对齐。
- 负责测试与交付质量，包括隔离 E2E 数据库和 seed、后端/前端回归、Playwright
  主流程、安全与失败场景、静态检查、迁移检查、缺陷闭环和最终验证记录。
- 提出 `PUBLIC / MATCH_ONLY / VERIFICATION / PRIVATE` 四级数据分类，并与
  宋姿毅协作将其落实到服务端权限、DTO、AI 输入、日志和测试边界。

### 共同职责

- 宋姿毅与徐胜宇共同完成受控图片识别方案的评估和边界确认：图片模型只生成
  可编辑草稿，不直接发布、不参与视觉相似度认领，失败时允许人工补录。
- T13～T16 的前后端流程由宋姿毅主责前端、徐胜宇主责后端，通过接口契约共同
  完成认证、发布、匹配、认领和管理员工作台联调。
- 两人共同维护安全底线：隐藏答案和 PRIVATE 数据不进入候选响应或向量，身份证
  完整号码不进入 LLM、普通日志和公开页面，最终交接状态只能由拾得者确认。

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

首次创建 PostgreSQL volume 时，Docker 会从
`src/backend/docker/postgres/002-persistent-data.sql` 一次性导入已验证的物品、
匹配、认领、管理员复核和审计数据；后续重启不会重复导入。登录账号：

- 普通用户：`user@campus.edu.cn` / `User123456!`
- 管理员：`admin@campus.edu.cn` / `Admin123456!`

如果本机已经存在旧的 `lost_found` volume，需要主动替换其中的应用数据时执行：

```bash
cd src/backend
../../.venv/bin/python -m scripts.initialize_persistent_data --replace
```

该命令会替换当前 `lost_found` 数据库中的应用数据，不能作为每次启动命令使用。

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
