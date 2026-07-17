# 前后端联调与完整验收设计

**日期：** 2026-07-17

**状态：** 已获用户总体设计批准，待书面 Spec 复核

**范围：** `frontend/`、`src/backend/`、数据库迁移、API 契约、单元测试、集成测试与全栈 E2E

## 1. 背景与权威来源

当前 `master` 已同时包含前端任务和后端任务，但二者是独立完成的，尚未形成可运行的真实业务闭环。`task.md` 和 `frontend-backend-api-mapping.md` 提供任务与接口参考；发生冲突时，按以下优先级解释需求：

1. 用户在本次联调中确认的业务规则；
2. `frontend/` 中现有页面、路由、交互流程和展示需求；
3. `task.md` 的安全、状态机与验收约束；
4. `frontend-backend-api-mapping.md` 的接口建议；
5. 现有后端接口与 DTO，可在不破坏安全规则的前提下调整。

`frontend_副本/` 是用户保留的备份，不读取、不修改、不纳入提交。

## 2. 当前基线与已确认问题

设计前的只读基线检查得到以下结果：

- 后端测试：`172 passed`。
- 前端测试：36 个通过、14 个失败；失败集中在过期页面文案、静态 mock 数据、DTO 不一致和测试环境的 `AbortSignal` 兼容问题。
- 前端类型检查失败：`CandidateListPage.tsx` 存在重复的 `border` 属性。
- FastAPI、PostgreSQL 和 `ai-mock` 可以启动，健康检查通过，数据库迁移位于当前 head。
- 前端业务页面普遍直接调用 `mockApi`；认证模块还把 `USE_MOCK` 固定为 `true`。
- 多个页面提交后跳转到固定 ID，如 `lr-001`、`cl-001`、`cl-002`，并没有消费后端返回的真实 ID。
- 后端缺少前端实际流程需要的若干查询、详情、进度和状态接口。
- 认证、候选、管理员复核、上传等 DTO 在前后端之间不一致。
- 当前后端只有 `IDENTITY_DOCUMENT` 和 `OTHER` 两种 `item_type`，没有五类公开物品类别和五类地点区域。
- 当前匹配只按 `item_type` 过滤；类别比较实际使用的也是 `item_type`，因此无法区分电子产品、服饰配饰、学习用品和其他。
- 当前地点只做字符串相等评分，不是五个区域的硬过滤。

这些问题是联调的已知输入，不代表已经获准逐项修改。实施时仍按第 12 节的缺陷确认门禁分组报告并获得用户确认。

## 3. 目标与非目标

### 3.1 目标

1. 前端默认通过真实 HTTP/SSE 调用 FastAPI，不再默认依赖 mock。
2. 跑通注册登录、首页、地点列表、寻物发布、招领发布、候选匹配、两类认领核验、复核、交接、个人记录和审计页面的真实闭环。
3. 物品类别和地点区域都按五种稳定枚举做硬过滤。
4. 楼栋、教室、楼层等公开细节通过物品公开描述参与向量匹配。
5. 隐藏特征、完整证件号码、token、私有图片路径不进入向量、普通日志、URL 或公开 DTO。
6. 为新增或修复的行为先写失败测试，再完成最小修复；最终通过单元、契约、数据库集成和浏览器 E2E 验证。
7. 每个缺陷根因组在修改前向用户展示定位、证据、方案和权衡，得到逻辑确认后才修复。

### 3.2 非目标

- 不重做页面视觉设计，不替换现有 React/FastAPI 技术栈。
- 不重构与联调无关的代码，也不清理既有无关死代码。
- 不把真实 AI 服务作为自动化测试的硬依赖。
- 不在本轮增加五类之外的新类别、地点或可配置字典系统。
- 不使用 token URL 参数，不把认证 token 写入 `localStorage`、`sessionStorage` 或其他浏览器持久存储。

## 4. 方案选择

### 4.1 采用：契约优先、分阶段打通

先锁定领域枚举、DTO、错误体和状态流，再按后端契约、前端适配、全栈测试的顺序实施。数据库和匹配逻辑先对齐，页面再消费真实接口。该方案改动边界清楚，能用契约测试阻止前后端再次漂移，也是本设计采用的方案。

### 4.2 未采用：只在前端增加兼容适配层

该方案改动较少，但无法解决后端缺失的类别/区域字段、硬过滤、详情接口和真实状态流，只能把 mock 外观包装成 API 外观，不能满足完整联调目标。

### 4.3 未采用：重写后端或前端

重写可以统一模型，但会丢失现有 172 个后端测试和已完成页面，修改面远超必要范围，风险和验证成本都更高。

## 5. 总体架构与边界

系统仍采用单仓库模块化结构：

- `frontend/src/api/`：唯一 HTTP/SSE 边界，负责认证头、一次刷新、错误归一化和 DTO 类型。
- `frontend/src/features/`：页面与业务交互，只调用对应 API 模块，不直接导入 `mockApi`。
- `src/backend/app/api/routes/`：HTTP 契约、鉴权、输入输出模型和状态码。
- `src/backend/app/items/`：失物/招领记录和发布状态流。
- `src/backend/app/matching/`：硬过滤、向量相似度、结构化评分和 Top 5。
- `src/backend/app/verification/`、`reviews/`、`audit/`：核验、复核与安全投影。
- PostgreSQL/pgvector：结构化事实、状态、审计和公开文本向量的权威存储。
- `ai-mock`：自动化测试的确定性多模态/语义服务；真实 MiMo/Embedding 仅用于具备 Key 时的附加 smoke test。

页面不得绕过后端自行制造业务状态；后端不得返回前端不应看到的私有字段。

## 6. 领域数据契约

### 6.1 公开物品类别

新增独立枚举 `PublicCategory`：

| 前端中文 | API/数据库值 | 核验用 `item_type` |
|---|---|---|
| 电子产品 | `ELECTRONICS` | `OTHER` |
| 证件卡片 | `IDENTITY_CARD` | `IDENTITY_DOCUMENT` |
| 服饰配饰 | `CLOTHING` | `OTHER` |
| 学习用品 | `STATIONERY` | `OTHER` |
| 其他 | `OTHER_CATEGORY` | `OTHER` |

`public_category` 决定候选硬过滤，`item_type` 只决定身份证号码核验或隐藏问题核验。两者都持久化；创建或确认请求只提交 `public_category`，后端按上表推导并写入 `item_type`，避免接受不一致组合。响应同时返回两个字段。

### 6.2 地点区域

新增独立枚举 `LocationArea`：

| 前端中文 | API/数据库值 |
|---|---|
| 宿舍区 | `DORMITORY` |
| 食堂 | `CANTEEN` |
| 教学楼 | `TEACHING_BUILDING` |
| 科教楼 | `SCIENCE_BUILDING` |
| 图书馆 | `LIBRARY` |

`location_area` 是候选硬过滤字段。楼栋、教室、楼层、楼梯口等细节由用户写入 `description_public`，作为公开特征进入向量文本。`location_public` 保留为公开展示兼容字段，由后端按 `location_area` 生成对应中文区域名称，不作为硬过滤权威值。

### 6.3 向量输入与隐私边界

匹配向量的规范文本按固定顺序生成：

```text
name_public
description_public
location_public
```

因此写在 `description_public` 中的“教学楼 B 区 302 教室”等细节会参与语义相似度。以下内容明确禁止进入向量文本：

- `hidden_description` / `hiddenInfo`；
- 问题答案或答案键；
- 完整身份证号码及 HMAC；
- 私有图片路径、token、手机号。

时间继续使用结构化时间差评分，不拼入向量文本。

### 6.4 数据迁移

迁移按以下规则执行：

1. 新增数据库枚举、`public_category` 和 `location_area` 列及匹配索引。
2. 旧 `IDENTITY_DOCUMENT` 记录回填 `IDENTITY_CARD`。
3. 旧 `OTHER` 无法可靠反推四个公开类别，保守回填 `OTHER_CATEGORY`，不根据名称或描述猜测。
4. `location_public` 只按五个已确认中文区域值回填 `location_area`。
5. 迁移前检查未知地点；发现未知值则明确失败并列出待处理值，禁止任意归类。
6. 完成回填后，新记录的两个字段均为非空，并添加组合一致性约束。

当前本地数据库只有两条 `PUBLISHED / 图书馆` 记录，符合无歧义地点回填条件。

## 7. 匹配设计

### 7.1 硬过滤

对每条寻物记录，只查询同时满足以下条件的招领记录：

1. 方向相反：`LOST` 对 `FOUND`；
2. 招领记录状态为 `PUBLISHED`；
3. `public_category` 完全相同；
4. `location_area` 完全相同；
5. `item_type` 与类别推导结果一致；
6. embedding 存在，且模型与维度兼容。

任意硬条件不满足的记录不进入评分候选集。特别地，电子产品不能匹配服饰配饰；教学楼不能匹配科教楼。

### 7.2 评分与排序

保留当前 100 分结构：语义 50、时间 20、地点 20、公开字段完整度 10。类别与区域已经是硬门槛；区域相同得到结构化地点分，楼栋/教室细节通过公开描述影响语义分。候选低于既有可保留门槛的不返回。

最终按总分降序、候选 ID 升序稳定排序，最多返回 5 条。重新匹配替换没有关联认领的旧候选快照，不破坏已经进入认领流程的候选。

### 7.3 匹配失败

- embedding 或匹配失败必须返回稳定错误并保留可重试状态。
- 前端显示错误和重试入口，不展示虚假候选。
- 禁止网络失败、AI 失败或空结果时回退到 `mockApi`。

## 8. 统一 API 契约

### 8.1 认证

认证响应采用前端现有嵌套结构：

```json
{
  "user": {
    "id": "uuid",
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "role": "USER",
    "created_at": "2026-07-17T00:00:00Z"
  },
  "tokens": {
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "bearer"
  }
}
```

后端用户表增加非空 `username`；登录仍只使用 email。旧用户以 email 的 `@` 前缀回填显示名，username 不作为登录标识。需要提供：

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/auth/me`

token 只保存在前端运行时内存。401 最多用 refresh token 续期一次；续期失败清空内存并跳转登录。浏览器整页刷新会丢失内存会话并要求重新登录，这是不持久化 token 的明确取舍。

### 8.2 记录、候选与认领 DTO

公开 `ItemRecord` 至少返回：真实 ID、owner ID、kind、`public_category`、`location_area`、`item_type`、status、公开名称/描述/时间/地点、公开图片引用和时间戳。私有路径、隐藏信息和完整证件号永不返回。

候选详情采用前端页面需要的嵌套公开投影：

```json
{
  "id": "candidate-uuid",
  "lost_record_id": "lost-uuid",
  "found_record_id": "found-uuid",
  "total_score": 86.5,
  "level": "HIGH",
  "reason_codes": ["SEMANTIC_MATCH", "TIME_CLOSE", "AREA_MATCH"],
  "conflict_codes": [],
  "found_record": { "id": "found-uuid", "kind": "FOUND" },
  "created_at": "2026-07-17T00:00:00Z"
}
```

后端返回稳定 code；中文理由和冲突文案由前端集中映射，避免把展示语言固化在 API。管理员队列使用摘要 DTO，管理员详情使用包含安全证据投影的详情 DTO，不能用同一个贫化结构冒充详情。

### 8.3 必须覆盖的端点

| 模块 | 端点 |
|---|---|
| 认证 | `POST /api/auth/register`、`login`、`refresh`；`GET /api/auth/me` |
| 首页/地点 | `GET /api/records/recent`、`GET /api/records?location_area=...` |
| 我的记录 | `GET /api/records/mine?kind=...` |
| 寻物 | `POST /api/lost-records`、`GET /api/lost-records/{id}`、`GET /api/lost-records/{id}/candidates` |
| 匹配进度 | `GET /api/lost-records/{id}/match`，SSE |
| 招领 | `POST /api/found-records`、`extract`、`confirmation`、身份/问题确认、`publish`、`GET /api/found-records/{id}` |
| 候选/认领 | `GET /api/candidates/{id}`、问题获取、两类核验提交、`GET /api/claims/{id}` |
| 复核 | 寻物未匹配复核、认领复核、管理员队列/详情/决定 |
| 交接/审计 | 联系方式、确认交接、记录时间线、管理员审计事件 |
| 上传 | `POST /api/uploads`，返回 `image_asset_id` 和 purpose |

分页列表统一返回 `{items,total,page,page_size}`。创建和提交接口必须返回真实资源 ID，前端后续路由只使用这些 ID。

### 8.4 错误体与状态码

所有 JSON 错误统一为：

```json
{
  "error_code": "VERSION_CONFLICT",
  "message": "记录已被更新，请重新加载",
  "field_errors": {"email": "邮箱已被注册"}
}
```

`field_errors` 仅在字段错误时出现。错误策略：

- 401：刷新一次，仍失败则登录；
- 403：显示无权限，不重试；
- 404：显示资源不存在；
- 409：提示重新加载最新版本；
- 422：映射到表单字段；
- 423：显示安全锁定提示，不泄露核验细节；
- AI/embedding 失败：保留草稿或失败状态并提供显式重试。

FastAPI 默认 `detail` 错误、领域异常和请求校验错误都转换成上述结构。消息不得包含完整号码、隐藏答案、token 或对象路径。

## 9. 前端真实 API 设计

### 9.1 API 边界

业务页面只依赖按领域拆分的 API 函数，不直接使用 Axios、`fetch` 或 `mockApi`。公共客户端负责认证头、刷新、错误解析和取消请求。

`VITE_USE_MOCK` 默认视为 `false`。只有显式设置为 `true` 时才启用离线演示适配器，并在页面显示“Mock 演示模式”；网络失败绝不自动切换 mock。单元测试可直接注入 mock adapter。

开发环境通过 Vite `/api` 代理连接本地 FastAPI，避免跨域和环境地址散落；部署环境通过 `VITE_API_BASE_URL` 指定同一 API 边界。

### 9.2 SSE

原生 `EventSource` 不能安全地设置 Bearer 认证头，因此匹配进度改用 `fetch` 流式读取 `text/event-stream`：

- Authorization 放请求头，不放 URL；
- 支持 `AbortController` 在离开页面时取消；
- 初始 401 只刷新一次后重连；
- 流中断显示错误与“重新匹配”，不伪造 100% 进度；
- `done` 事件携带或触发加载真实候选列表。

### 9.3 页面状态

每个真实请求都有 loading、empty、error、success 状态。提交按钮在进行中禁用，避免重复提交。React Query 的 key 必须包含真实资源 ID、页码和筛选条件；成功 mutation 后只失效相关查询。

## 10. 关键业务数据流

### 10.1 招领发布：已确认的方案 2

1. 用户选择图片时只创建本地预览，不调用 AI，不随机填充表单。
2. 用户填写表单并点击第一次提交。
3. 前端创建 `DRAFT`，取得真实 `found_record_id`。
4. 有图片时上传并取得 `image_asset_id`，随后调用提取接口；无图片时跳过 AI，进入人工确认。
5. 页面展示 AI 建议和用户原输入。用户非空输入不被静默覆盖；所有最终公开字段都可编辑。
6. 用户执行第二次确认，提交最终 `public_category`、区域、时间、名称和公开描述。后端推导 `item_type`。
7. `IDENTITY_CARD` 完成证件 HMAC 与必要的图片脱敏确认；其他四类用 `hiddenInfo` 生成并确认隐藏问题。
8. 用户明确点击发布，后端校验版本和核验前置条件后进入 `PUBLISHED`。

AI 超时或无效时记录保持 `DRAFT`，允许人工填写/重试；绝不自动发布 AI 输出。

### 10.2 寻物发布与匹配

1. 前端把五类中文选择映射成 `public_category`，把五个地点映射成 `location_area`。
2. 后端推导 `item_type`，生成只含公开文本的 embedding，并创建 `PUBLISHED` 寻物记录。
3. 有可选图片时，在取得真实记录 ID 后上传；上传失败不删除已发布记录，页面明确显示失败和重试入口。
4. 后端按类别和区域硬过滤，计算并持久化 Top 5。
5. 前端通过认证的 SSE 显示真实进度，完成后加载真实候选并跳转 `/lost/{real_id}/candidates`。

### 10.3 认领、复核与交接

- `IDENTITY_CARD` 进入号码核验，最多尝试次数和锁定状态来自 API，不能使用前端常量模拟。
- 其他四类加载后端问题，提交真实回答，使用响应中的 `claim_id` 进入进度页。
- 核验失败或未匹配可创建真实复核申请；管理员页面加载真实队列、详情、安全证据和审计事件。
- 只有获准进入交接状态后才可读取受控联系方式。
- 正常路径仅由对应拾得者确认线下交接并把记录推进到 `CLAIMED`。

## 11. 测试设计

### 11.1 TDD 顺序

每个获准修复的根因组都遵循：

1. 写一个能够复现问题的最小失败测试；
2. 运行并保存失败证据；
3. 做最小实现；
4. 运行目标测试；
5. 运行相关回归；
6. 在阶段结束时运行全量验证。

### 11.2 后端单元与集成测试

至少覆盖：

- 五类 `PublicCategory`、五类 `LocationArea` 及类别到 `item_type` 的唯一映射；
- 不同类别或不同区域绝不进入候选评分；
- 公开详细地点进入 embedding，隐藏特征和证件信息不进入；
- Top 5、门槛、稳定排序和已有 claim 的候选保留；
- 统一错误体、鉴权、资源归属、状态机和敏感字段投影；
- 所有新增端点、分页、详情、真实 ID 和 SSE 事件序列；
- Alembic upgrade、约束、索引和已存在数据回填；
- 在真实 PostgreSQL/pgvector 上完成发布、匹配、认领、复核、交接事务。

### 11.3 前端单元与契约测试

至少覆盖：

- 五类/五地点中文与 API 枚举双向映射；
- 页面不直接导入 `mockApi`，真实模式为默认值，mock 模式有明显标记；
- 招领方案 2 的本地预览、第一次提交、AI 结果确认、第二次发布；
- 所有跳转使用后端真实 ID；
- 候选、问题、复核、个人记录、详情和审计页面消费真实 DTO；
- 401 刷新一次、403/409/422/423 和 AI 失败展示；
- token 不写浏览器持久存储；
- SSE 认证、进度、取消、中断和重试。

契约测试用后端 OpenAPI/Pydantic 响应与前端 DTO fixture 验证字段、枚举、状态码和错误体，避免两套手写类型再次漂移。

### 11.4 Playwright 全栈 E2E

自动化环境启动真实前端、FastAPI 和 PostgreSQL，AI 使用确定性的 `ai-mock`。至少覆盖：

1. 注册、登录、access token 失效后以 refresh token 续期，并继续访问受保护路由；
2. OTHER 招领方案 2 完整发布；
3. 寻物发布后只匹配相同类别和相同区域，并验证不同类别/区域被排除；
4. 详细楼栋/教室文本改变语义排序；
5. OTHER 问题核验到 claim 状态；
6. 身份证核验成功、失败次数和锁定安全提示；
7. 未匹配/认领复核、管理员决定和审计事件；
8. 交接联系方式授权与拾得者确认完成；
9. 首页最近动态、地点列表、详情和我的记录均展示数据库真实数据。

真实 MiMo/Embedding 只在存在有效 Key 时运行附加 smoke，不作为可重复自动化验收的必要条件。

## 12. 缺陷定位与用户确认门禁

实施过程中按共同根因分组，不逐条制造噪音。每组在修改前必须展示：

1. 可复现命令和实际失败；
2. 精确文件与行号；
3. 根因和影响路径；
4. 前端、后端或联调分类；
5. 至少两个可行方案及权衡；
6. 推荐方案和预计修改边界。

用户明确确认该组后，才写失败测试并修复。确认覆盖同一根因、同一修改边界内的回归问题；出现新的独立根因时重新报告并确认。当前已知问题预计分为：

- 领域模型与匹配硬过滤缺失；
- API/DTO/错误契约漂移及缺失端点；
- 前端 mock 硬编码、静态 ID 和方案 2 缺失；
- 过期测试、TypeScript 编译错误与测试环境兼容问题。

## 13. 实施阶段与检查点

本设计使用一个共享 Spec，因为领域契约、API 和 E2E 流程相互依赖；详细实施计划拆成以下顺序检查点：

1. **领域与迁移：** 枚举、字段、约束、数据回填、硬过滤和匹配单元测试。
2. **后端契约：** 认证 DTO、统一错误体、缺失端点、查询/详情/SSE 与后端集成测试。
3. **前端接线：** 真实 API adapter、方案 2、真实 ID、页面状态和前端单元测试。
4. **业务闭环：** 两类核验、复核、管理员、交接、个人记录和契约测试。
5. **全栈验收：** Playwright、失败路径、安全扫描、构建和完整需求审计。

每个检查点都受第 12 节确认门禁约束；不借机重构相邻代码。

## 14. 完成标准与验收证据

只有以下全部成立，才能声称联调目标完成：

- `frontend/` 默认真实 API；除显式 mock adapter 和测试外，没有业务页面直接导入 `mockApi`。
- 页面不存在固定业务 ID、随机 AI 结果或静态业务成功跳转。
- 五类物品和五个区域在前端、API、数据库、匹配查询和测试中一致。
- 类别、区域硬过滤有正反例；详细地点参与向量；隐藏信息不参与向量。
- OpenAPI 包含所有实际页面需要的端点，前端 DTO 与真实响应契约测试通过。
- 后端全量测试、前端单元测试、typecheck、lint、build 全部通过。
- 真实 PostgreSQL/pgvector 集成测试通过，迁移可从空库和当前本地库升级。
- Playwright 通过真实网络请求完成第 11.4 节全部关键用户旅程。
- 浏览器网络记录中无 mock 业务调用、token URL 参数或意外敏感字段。
- 所有发现的必需流程缺陷都已按门禁确认并修复；不存在已知未解决的必需流程 bug。
- `frontend_副本/` 未被读取、修改或提交；无关用户文件和改动保持不变。

最终报告按原始目标逐条列出证据，不用单个绿灯替代完整需求审计。
