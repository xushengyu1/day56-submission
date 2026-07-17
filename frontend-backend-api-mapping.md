# 前后端接口对照文档

> 本文档定义前端每个页面、按钮对应的后端 API 接口，以及需要新增的接口详细规格。
> 后端按 `task-backend.md` 开发，本文档用于联调对齐。

---

## 物品类型映射

后端 `item_records` 表必须同时存储 `item_type` 和 `public_category` 两个字段，独立使用：

| 前端物品类别（`public_category`） | 后端 `public_category` | 后端 `item_type` | 用途 |
|---|---|---|---|
| 电子产品 | `ELECTRONICS` | `OTHER` | 候选匹配 + 核验分支 |
| 证件卡片 | `IDENTITY_CARD` | `IDENTITY_DOCUMENT` | 候选匹配 + 核验分支 |
| 服饰配饰 | `CLOTHING` | `OTHER` | 候选匹配 + 核验分支 |
| 学习用品 | `STATIONERY` | `OTHER` | 候选匹配 + 核验分支 |
| 其他 | `OTHER_CATEGORY` | `OTHER` | 候选匹配 + 核验分支 |

- **候选匹配硬过滤**：使用 `public_category`（5 种精确匹配），电子产品只匹配电子产品，学习用品只匹配学习用品
- **认领核验分支**：使用 `item_type`（2 种），`IDENTITY_DOCUMENT` 走 HMAC 核验，`OTHER` 走隐藏问题核验
- 两个字段独立存储，不能只存 `item_type` 然后推断 `public_category`（因为 `OTHER` 对应 4 种不同类别）

---

## 一、认证模块（T03）

### 1.1 登录页 `/login`

| 前端操作 | 后端接口 | 说明 |
|---|---|---|
| 输入邮箱+密码，点击「登录」 | `POST /api/auth/login` | 前端用 `email` 登录，非 username |

**请求：**
```json
{
  "email": "zhangsan@campus.edu.cn",
  "password": "xxx"
}
```

**响应：**
```json
{
  "user": { "id": "u-001", "username": "zhangsan", "email": "zhangsan@campus.edu.cn", "role": "USER" },
  "tokens": { "access_token": "xxx", "refresh_token": "xxx", "token_type": "bearer" }
}
```

**管理员判断：** `user.role === 'ADMIN'` 时前端跳转 `/admin`，普通用户跳转 `/`。管理员账号 `admin@campus.edu.cn` 在 seed 中预置。

### 1.2 注册页 `/register`

| 前端操作 | 后端接口 |
|---|---|
| 填写用户名+邮箱+手机号+密码，点击「注册」 | `POST /api/auth/register` |

**请求：**
```json
{
  "username": "zhangsan",
  "email": "zhangsan@campus.edu.cn",
  "password": "xxx",
  "phone": "13812341234"
}
```

### 1.3 Token 刷新

| 前端操作 | 后端接口 |
|---|---|
| 401 响应时自动刷新 | `POST /api/auth/refresh` |

**请求：**
```json
{ "refresh_token": "xxx" }
```

---

## 二、首页 `/`（T08 部分）

### 2.1 数据概览面板

| 数据 | 后端接口 | 说明 |
|---|---|---|
| 寻物记录数 | `GET /api/lost-records?owner=me` | 响应中取 `total` |
| 招领记录数 | `GET /api/found-records?owner=me` | 响应中取 `total` |
| 已匹配数 | 同上两个接口 | 前端统计 `status === 'PUBLISHED'` 的数量 |
| 总记录数 | 上述两者相加 | 前端计算 |

> **建议新增：** `GET /api/stats/overview` 一次性返回统计数据，避免两次请求。

### 2.2 最新动态

| 数据 | 后端接口 | 说明 |
|---|---|---|
| 全系统最近 5 条记录 | **需新增** `GET /api/records/recent?limit=5` | 按 `created_at` 倒序，返回寻物+招领混合列表 |

**新增接口详情：**

```
GET /api/records/recent?limit=5
Authorization: Bearer {token}

响应 200:
{
  "items": [
    {
      "id": "lr-001",
      "kind": "LOST",
      "item_type": "OTHER",
      "name_public": "黑色折叠伞",
      "event_time_public": "7月16日上午",
      "location_public": "教学楼",
      "status": "PUBLISHED",
      "created_at": "2026-07-16T09:00:00Z"
    }
  ]
}
```

### 2.3 快速入口

| 前端操作 | 后端接口 | 说明 |
|---|---|---|
| 点击地点（宿舍区/食堂/教学楼/科教楼/图书馆） | 跳转 `/location/:location`，调用下方 2.4 接口 | |

### 2.4 地点物品列表页 `/location/:location`

| 数据 | 后端接口 | 说明 |
|---|---|---|
| 按地点筛选的寻物+招领列表 | **需新增** `GET /api/records?location={location}&page=1&page_size=5` | 分页查询，寻物+招领混合 |

**新增接口详情：**

```
GET /api/records?location=教学楼&page=1&page_size=5
Authorization: Bearer {token}

响应 200:
{
  "items": [
    {
      "id": "fr-001",
      "kind": "FOUND",
      "item_type": "OTHER",
      "name_public": "黑色折叠伞",
      "description_public": "黑色短柄折叠伞...",
      "event_time_public": "7月16日上午",
      "location_public": "教学楼",
      "status": "PUBLISHED",
      "created_at": "2026-07-16T11:00:00Z",
      "updated_at": "2026-07-16T11:00:00Z"
    }
  ],
  "total": 12,
  "page": 1,
  "page_size": 5
}
```

---

## 三、我要寻物 `/lost/new`（T08）

### 3.1 发布寻物

| 前端操作 | 后端接口 | 说明 |
|---|---|---|
| 填写表单，点击「提交」 | `POST /api/lost-records` | 创建失物记录 |
| 上传图片（可选） | `POST /api/uploads` | 先上传图片拿到 `image_asset_id`，再创建记录 |

**请求：**
```json
{
  "item_type": "OTHER",
  "name_public": "黑色折叠伞",
  "description_public": "黑色短柄折叠伞，普通款",
  "event_time_public": "7月16日上午",
  "location_public": "教学楼",
  "image_asset_id": "optional-asset-id"
}
```

**响应：**
```json
{
  "id": "lr-001",
  "status": "PUBLISHED"
}
```

**前端提交后跳转：** `/lost/{id}/candidates`（进入匹配结果页）

---

## 四、寻物详情 `/lost/:id`（T08）

### 4.1 查看寻物详情

| 数据 | 后端接口 | 说明 |
|---|---|---|
| 物品详情 | `GET /api/lost-records/{id}` | 返回 ItemRecord |

### 4.2 自己发布的 → 「查看匹配结果」

| 前端操作 | 后端接口 | 说明 |
|---|---|---|
| 点击按钮 | 跳转 `/lost/:id/candidates` | 见下方第五节 |

### 4.3 他人发布的 → 只读，无按钮

无需额外接口，只用 `GET /api/lost-records/{id}`。

---

## 五、候选列表 `/lost/:id/candidates`（T08）

### 5.1 获取候选列表

| 数据 | 后端接口 | 说明 |
|---|---|---|
| Top 5 候选 | `GET /api/lost-records/{id}/candidates` | SSE 进度条完成后获取 |

### 5.2 SSE 匹配进度（实时）

| 前端操作 | 后端接口 | 说明 |
|---|---|---|
| 进入页面 / 点击「重新匹配」 | **需新增** `GET /api/lost-records/{id}/match` (SSE) | 实时推送匹配进度 |

**新增接口详情：**

```
GET /api/lost-records/{id}/match
Authorization: Bearer {token}
Accept: text/event-stream

响应（SSE 流）：
event: progress
data: {"step":"searching","label":"正在检索招领记录...","progress":15}

event: progress
data: {"step":"filtering","label":"筛选同类型已发布记录...","progress":30}

event: progress
data: {"step":"embedding","label":"生成文本向量...","progress":50}

event: progress
data: {"step":"matching","label":"语义匹配计算中...","progress":70}

event: progress
data: {"step":"scoring","label":"综合评分排序...","progress":85}

event: progress
data: {"step":"finalizing","label":"生成匹配结果...","progress":100}

event: done
data: {"candidates":[...]}

event: error
data: {"error_code":"MATCHING_FAILED","message":"匹配失败"}
```

**step 枚举值：** `searching` / `filtering` / `embedding` / `matching` / `scoring` / `finalizing`

### 5.3 「重新匹配」按钮

触发 SSE 重新连接（同 5.2）。

### 5.4 「提交未匹配复核」按钮

跳转 `/lost/:id/unmatched-review`（见第七节）。

---

## 六、候选详情 `/candidates/:id`（T08/T09/T10）

### 6.1 获取候选详情

| 数据 | 后端接口 | 说明 |
|---|---|---|
| 候选详情 | `GET /api/candidates/{id}` | 返回候选详情 + 关联的招领记录 PUBLIC 投影 |

### 6.2 「发起认领」按钮

根据物品类型跳转不同页面：

| 物品类型 | 跳转 | 对应后端 |
|---|---|---|
| `IDENTITY_DOCUMENT`（证件卡片） | `/claims/identity/:candidateId` | 身份证核验（T09） |
| `OTHER`（其他所有类别） | `/claims/other/:candidateId` | OTHER 核验（T10） |

---

## 七、提交未匹配复核 `/lost/:id/unmatched-review`（T11）

### 7.1 提交复核申请

| 前端操作 | 后端接口 | 说明 |
|---|---|---|
| 填写表单，点击「提交复核申请」 | `POST /api/lost-records/{id}/review-requests` | 已有接口 |

**请求：**
```json
{
  "request_type": "UNMATCHED",
  "reason": "物品详细描述：黑色折叠伞，品牌天堂，手柄有磨损...",
  "supplement": "丢失地点在教学楼B区3楼，7月16日上午10点左右"
}
```

**响应：**
```json
{
  "id": "rr-001",
  "status": "PENDING_ADMIN_REVIEW"
}
```

> **注意：** 后端 `task-backend.md` T11 已定义此接口，前端的 `reason` 字段会包含用户填写的所有信息（物品名称、描述、地点、时间、补充说明）。

---

## 八、认领核验（T09/T10）

### 8.1 身份证认领 `/claims/identity/:candidateId`

| 前端操作 | 后端接口 | 说明 |
|---|---|---|
| 输入身份证号码，点击「验证」 | `POST /api/candidates/{candidateId}/claims/identity` | T09 |

**请求：**
```json
{
  "full_number": "110101199001011234"
}
```

**响应（成功）：**
```json
{
  "claim_id": "cl-001",
  "status": "PENDING_HANDOFF"
}
```

**响应（失败）：**
```json
{
  "error_code": "IDENTITY_NOT_VERIFIED",
  "message": "无法完成验证",
  "attempts_remaining": 1
}
```

**响应（锁定）：**
```json
{
  "error_code": "ATTEMPT_LOCKED",
  "message": "尝试次数已用完"
}
```

### 8.2 OTHER 认领 `/claims/other/:candidateId`

**步骤一：获取问题**

| 前端操作 | 后端接口 | 说明 |
|---|---|---|
| 进入页面时加载问题 | `GET /api/candidates/{candidateId}/questions` | T10 |

**响应：**
```json
{
  "questions": [
    { "question_id": "q-001", "question_text": "这个物品有什么特殊标记？" },
    { "question_id": "q-002", "question_text": "物品的颜色和品牌是什么？" }
  ]
}
```

> **注意：** 只返回问题文本和 ID，不返回答案要点。

**步骤二：提交回答**

| 前端操作 | 后端接口 | 说明 |
|---|---|---|
| 填写回答，点击「提交验证」 | `POST /api/candidates/{candidateId}/claims/answers` | T10 |

**请求：**
```json
{
  "answers": [
    { "question_id": "q-001", "answer_text": "伞套内侧有SZY字样" },
    { "question_id": "q-002", "answer_text": "黑色折叠伞，无品牌" }
  ]
}
```

**响应（自动通过）：**
```json
{
  "claim_id": "cl-001",
  "status": "PENDING_HANDOFF"
}
```

**响应（转管理员）：**
```json
{
  "claim_id": "cl-001",
  "status": "PENDING_ADMIN_REVIEW",
  "message": "已提交人工复核"
}
```

---

## 九、认领进度 `/claims/:id/progress`（T12）

### 9.1 获取认领状态

| 数据 | 后端接口 | 说明 |
|---|---|---|
| 认领申请状态 | `GET /api/claims/{id}` | **需新增** |

**新增接口详情：**

```
GET /api/claims/{id}
Authorization: Bearer {token}

响应 200:
{
  "id": "cl-001",
  "candidate_id": "c-001",
  "status": "PENDING_HANDOFF",
  "verification_mode": "HIDDEN_FEATURE",
  "created_at": "2026-07-16T14:30:00Z",
  "timeline": [
    { "event": "SUBMITTED", "time": "2026-07-16T14:30:00Z" },
    { "event": "VERIFYING", "time": "2026-07-16T14:30:05Z" },
    { "event": "PENDING_HANDOFF", "time": "2026-07-16T14:31:00Z" }
  ]
}
```

---

## 十、我要招领 `/found/new`（T05/T07）

### 10.1 上传图片

| 前端操作 | 后端接口 | 说明 |
|---|---|---|
| 选择图片 | `POST /api/uploads` | T05 |

**请求：** `multipart/form-data`
```
file: <binary>
purpose: FINDER_ORIGINAL
```

**响应：**
```json
{
  "image_asset_id": "img-001",
  "purpose": "FINDER_ORIGINAL"
}
```

### 10.2 AI 自动识别（上传后自动触发）

| 前端操作 | 后端接口 | 说明 |
|---|---|---|
| 上传图片后自动调用 | `POST /api/found-records/{id}/extract` | T07，AI 提取物品信息 |

> **注意：** 前端流程是先 `POST /api/found-records` 创建草稿拿到 `id`，再 `POST /api/found-records/{id}/extract` 触发 AI 提取。

**创建草稿请求：**
```json
{
  "image_asset_id": "img-001",
  "event_time_public": "7月16日上午",
  "location_public": "教学楼"
}
```

**AI 提取响应：**
```json
{
  "suggested_name": "黑色折叠伞",
  "suggested_category": "其他",
  "suggested_description": "黑色短柄折叠伞，伞面完好",
  "confidence": { "name": 0.92, "category": 0.88, "description": 0.85 }
}
```

### 10.3 提交招领（确认并发布）

| 前端操作 | 后端接口 | 说明 |
|---|---|---|
| 修改/确认 AI 填充内容，点击「提交」 | `PUT /api/found-records/{id}/confirmation` | T07，确认公开信息 |
| 然后 | `POST /api/found-records/{id}/publish` | T07，正式发布 |

**确认请求：**
```json
{
  "name_public": "黑色折叠伞",
  "category": "其他",
  "description_public": "黑色短柄折叠伞，伞面完好，手柄无磨损",
  "expected_version": 1
}
```

**发布响应：**
```json
{
  "id": "fr-001",
  "status": "PUBLISHED"
}
```

> **简化方案：** 前端可以将创建草稿 + 确认 + 发布合并为一次提交，后端在一个事务中处理。具体看联调时的接口设计。

---

## 十一、招领详情 `/found/:id`（T08）

### 11.1 获取招领详情

| 数据 | 后端接口 | 说明 |
|---|---|---|
| 招领物品详情 | `GET /api/found-records/{id}` | **需新增**，或复用 `GET /api/records/{id}` |

**新增接口详情：**

```
GET /api/found-records/{id}
Authorization: Bearer {token}

响应 200:
{
  "id": "fr-001",
  "kind": "FOUND",
  "item_type": "OTHER",
  "name_public": "黑色折叠伞",
  "description_public": "黑色短柄折叠伞，伞面完好",
  "event_time_public": "7月16日上午",
  "location_public": "教学楼",
  "status": "PUBLISHED",
  "created_at": "2026-07-16T11:00:00Z",
  "updated_at": "2026-07-16T11:00:00Z"
}
```

---

## 十二、我的记录 `/records`（T08/T12）

### 12.1 获取我的记录列表

| 数据 | 后端接口 | 说明 |
|---|---|---|
| 我发布的寻物+招领 | **需新增** `GET /api/records/mine?page=1&page_size=5` | 按 `updated_at` 倒序 |

**新增接口详情：**

```
GET /api/records/mine?page=1&page_size=5
Authorization: Bearer {token}

响应 200:
{
  "items": [
    {
      "id": "lr-001",
      "kind": "LOST",
      "item_type": "OTHER",
      "name_public": "黑色折叠伞",
      "description_public": "...",
      "event_time_public": "7月16日上午",
      "location_public": "教学楼",
      "status": "PUBLISHED",
      "created_at": "2026-07-16T09:00:00Z",
      "updated_at": "2026-07-16T14:05:00Z"
    }
  ],
  "total": 7,
  "page": 1,
  "page_size": 5
}
```

### 12.2 招领物品 → 「确认交接」按钮

| 前端操作 | 后端接口 | 说明 |
|---|---|---|
| 点击「确认交接」 | `POST /api/claims/{id}/handoff-complete` | T12，拾得者确认线下交接完成 |

**响应：**
```json
{
  "claim_id": "cl-001",
  "status": "CLAIMED",
  "found_record_status": "CLAIMED",
  "lost_record_status": "CLAIMED"
}
```

> **注意：** 前端目前用的是 `foundItemId`，需要先通过 claim 关系找到对应的 `claim_id`。建议后端在 `GET /api/records/mine` 响应中对 `PENDING_HANDOFF` 状态的招领记录返回关联的 `claim_id`。

---

## 十三、管理员模块（T11）

### 13.1 复核队列 `/admin`

| 数据 | 后端接口 | 说明 |
|---|---|---|
| 待复核列表 | `GET /api/admin/reviews` | T11 |

**响应：**
```json
{
  "items": [
    {
      "id": "rv-001",
      "review_type": "MULTI_CLAIM",
      "target_id": "fr-002",
      "target_name": "居民身份证",
      "target_type": "CLAIM",
      "applicant_id": "u-001",
      "applicant_name": "张同学",
      "reason": "同一物品有2人认领",
      "status": "PENDING",
      "created_at": "2026-07-16T15:00:00Z"
    }
  ]
}
```

> **注意：** 前端需要 `target_name`（物品名称）和 `applicant_name`（申请人姓名），请后端在列表 DTO 中包含这两个字段。

### 13.2 复核详情 `/admin/reviews/:id`

| 数据 | 后端接口 | 说明 |
|---|---|---|
| 复核详情 + 证据 | `GET /api/admin/reviews/{id}` | T11 |

### 13.3 提交复核决定

| 前端操作 | 后端接口 | 说明 |
|---|---|---|
| 选择通过/驳回，填写理由，点击「提交决定」 | `POST /api/admin/reviews/{id}/decision` | T11 |

**请求：**
```json
{
  "decision": "APPROVE_TO_HANDOFF",
  "reason": "经核实，张同学的回答与隐藏特征一致"
}
```

**`decision` 枚举：** `APPROVE_TO_HANDOFF`（通过待交接）/ `REJECT`（驳回）

### 13.4 审计日志 `/admin/audit`

| 数据 | 后端接口 | 说明 |
|---|---|---|
| 审计事件列表 | `GET /api/admin/audit-events` | T11 |

**响应：**
```json
{
  "items": [
    {
      "id": "ae-001",
      "event_type": "HANDOFF_COMPLETE",
      "actor_name": "李同学",
      "detail": "拾得者确认已完成线下交接",
      "occurred_at": "2026-07-16T16:30:00Z"
    }
  ]
}
```

> **注意：** 前端需要 `actor_name`（操作人姓名）和 `detail`（中文描述），event_type 映射为中文标签由前端处理。

---

## 十四、认领复核（T11）

### 14.1 提交认领复核

| 前端操作 | 后端接口 | 说明 |
|---|---|---|
| 核验失败后点击「申请认领复核」 | `POST /api/claims/{id}/review-requests` | T11 |

**请求：**
```json
{
  "request_type": "CLAIM_REVIEW",
  "reason": "我认为核验结果有误，物品确实是我的"
}
```

---

## 十五、SSE 匹配进度（需新增）

### 接口规格

```
GET /api/lost-records/{id}/match
Authorization: Bearer {token}
Accept: text/event-stream
Cache-Control: no-cache

响应 Content-Type: text/event-stream
```

### 事件类型

| event | data 格式 | 说明 |
|---|---|---|
| `progress` | `{"step":"string","label":"string","progress":0-100}` | 进度更新 |
| `done` | `{"candidates":[...]}` | 匹配完成，返回候选列表 |
| `error` | `{"error_code":"string","message":"string"}` | 匹配失败 |

### step 枚举

| step | 中文标签 | 说明 |
|---|---|---|
| `searching` | 检索招领记录 | 查询同类型已发布记录 |
| `filtering` | 筛选同类型记录 | 硬过滤：方向相反、类型相同、状态PUBLISHED |
| `embedding` | 生成文本向量 | 调用 embedding 模型 |
| `matching` | 语义匹配计算 | pgvector 余弦相似度 |
| `scoring` | 综合评分排序 | 50/20/20/10 四维评分 |
| `finalizing` | 生成匹配结果 | 保存 Top 5 快照 |

---

## 十六、新增接口汇总

以下是后端 `task-backend.md` 中**未定义**但前端需要的接口：

| # | 接口 | 方法 | 说明 | 优先级 |
|---|---|---|---|---|
| 1 | `/api/records/recent?limit=5` | GET | 全系统最新动态 | P0 |
| 2 | `/api/records?location={location}&page=1&page_size=5` | GET | 按地点分页查询 | P0 |
| 3 | `/api/records/mine?page=1&page_size=5` | GET | 我的记录分页 | P0 |
| 4 | `/api/lost-records/{id}/match` | GET (SSE) | 实时匹配进度 | P1 |
| 5 | `/api/found-records/{id}` | GET | 招领详情 | P0 |
| 6 | `/api/claims/{id}` | GET | 认领申请详情+状态 | P0 |
| 7 | `/api/stats/overview` | GET | 首页统计数据 | P2 |

> P0 = 联调必须，P1 = 体验优化可后续迭代，P2 = 可选

---

## 十七、后端响应 DTO 字段要求

### ItemRecord（前端期望字段）

```typescript
{
  id: string
  owner_user_id: string
  kind: 'LOST' | 'FOUND'           // 记录方向
  item_type: 'IDENTITY_DOCUMENT' | 'OTHER'
  name_public: string               // 公开名称
  description_public?: string       // 公开描述
  event_time_public: string         // 模糊时间
  location_public: string           // 公开地点
  masked_document_number?: string   // 仅身份证件
  status: RecordStatus
  created_at: string                // ISO 8601
  updated_at: string                // ISO 8601
}
```

### MatchCandidate（前端期望字段）

```typescript
{
  id: string
  lost_record_id: string
  found_record_id: string
  total_score: number               // 总分 0-100
  reason_texts: string[]            // 匹配理由文案
  conflict_texts: string[]          // 冲突点文案
  retention_reason: string          // 保留原因
  found_record: ItemRecord          // 关联招领记录 PUBLIC 投影
  created_at: string
}
```

### ReviewRecord（前端期望字段）

```typescript
{
  id: string
  review_type: 'MULTI_CLAIM' | 'VERIFICATION_FAILED' | 'IDENTITY_ANOMALY' | 'UNMATCHED' | 'CLAIM_REVIEW'
  target_id: string
  target_name?: string              // 物品名称（列表展示用）
  target_type: 'LOST' | 'CLAIM'
  applicant_id: string
  applicant_name?: string           // 申请人姓名（列表展示用）
  reason: string
  status: 'PENDING' | 'APPROVED' | 'REJECTED'
  created_at: string
}
```

---

## 十八、前端已有但后端 task-backend.md 已覆盖的接口

| 前端页面 | 后端 Task | 接口 |
|---|---|---|
| 登录/注册 | T03 | `POST /api/auth/login` / `register` / `refresh` |
| 发布寻物 | T08 | `POST /api/lost-records` |
| 候选列表 | T08 | `GET /api/lost-records/{id}/candidates` / `GET /api/candidates/{id}` |
| 身份证认领 | T09 | `POST /api/candidates/{id}/claims/identity` |
| OTHER 认领 | T10 | `GET /api/candidates/{id}/questions` / `POST /api/candidates/{id}/claims/answers` |
| 未匹配复核 | T11 | `POST /api/lost-records/{id}/review-requests` |
| 认领复核 | T11 | `POST /api/claims/{id}/review-requests` |
| 管理员队列 | T11 | `GET /api/admin/reviews` / `GET /api/admin/reviews/{id}` / `POST /api/admin/reviews/{id}/decision` |
| 审计日志 | T11 | `GET /api/admin/audit-events` |
| 交接确认 | T12 | `POST /api/claims/{id}/handoff-complete` |
| 图片上传 | T05 | `POST /api/uploads` |
| 招领发布 | T07 | `POST /api/found-records` + `extract` + `confirmation` + `publish` |
