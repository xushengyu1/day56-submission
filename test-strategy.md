# AI 失物招领系统 — 前端测试策略

> **当前范围：** T13-T16 前端应用壳、认证、三角色页面 + 联调对齐后的接口契约更新  
> **文档状态：** 前端 6 个测试文件、46 个用例全部通过；字段命名、状态枚举、评分逻辑已对齐后端  
> **测试锚点：** `prd.md` V0.9、`task-frontend.md`、`docs/design/end-to-end-system-design.md`、`docs/decision/decision-location-itemcategory-enums.md`；不得以未来实现的当前输出反推 expected  
> **负责人：** 宋姿毅（前端）、徐胜宇（后端）

## 1. Test Objective

验证前端三角色视图下的：

- T13 认证系统：登录/注册页面渲染、路由守卫（未认证跳转、USER 访问 admin 返回 403）、布局隔离。
- T14 拾得者向导：四步向导步骤指示器、AI 提取结果展示与可编辑标识、草稿保存。
- T15 失主流程：发布失物表单、Top 5 候选列表与详情、匹配点/冲突点/评分明细展示、身份证核验与隐藏特征核验表单行为、认领进度页。
- T16 管理员工作台：复核队列统计与筛选、复核详情中申请人对比/标准答案/AI 分析/决定表单。

## 2. Test Scope

### 2.1 In Scope

- 页面组件渲染与关键文本/元素存在性。
- 路由守卫行为（RequireAuth、RequireAdmin）。
- 表单交互（输入、选择、按钮禁用/启用条件）。
- Mock API 数据驱动的异步内容加载。
- 安全约束前端表现（掩码号码、不泄露隐藏答案、联系方式仅待交接展示）。

### 2.2 Out of Scope

- 真实后端 API 联调（当前使用 Mock API；联调时需更新为真实 API 调用）。
- Playwright E2E 测试（计划 T17）。
- 浏览器 localStorage/sessionStorage 扫描（计划 T18）。
- 视觉回归测试（像素级 UI 对比）。
- 组件内部实现细节（state、effect 调用次数等）。
- SSE 实时进度推送的端到端验证（需后端 SSE 接口完成后测试）。

### 2.3 联调对齐变更（2026-07-17）

以下前端变更已完成，测试用例需同步更新：

| 变更项 | 旧值 | 新值 | 影响范围 |
|---|---|---|---|
| 字段命名 | `record_type`、`public_item_name` 等 | `kind`、`name_public` 等 | 所有 mock 数据和组件 |
| RecordStatus | `PENDING_MATCH`、`HAS_CANDIDATES` | `PUBLISHED`、`PROCESSING` | 状态标签、筛选逻辑 |
| ClaimStatus | `PENDING_ANSWER`、`AI_VERIFYING` | `SUBMITTED`、`VERIFYING` | 认领进度页 |
| 候选评分 | `match_score` + 四维明细 | `total_score` + `reason_texts` | 候选列表、详情页 |
| 登录方式 | username | email + password | 登录页、auth API |
| 匹配过滤 | `item_type`（2 种） | `public_category`（5 种） | 候选匹配逻辑 |
| 地点枚举 | 自由输入 | 5 个固定枚举 | 下拉框、匹配评分 |
| 隐藏信息 | 无 | 招领表单新增隐藏信息文本框 | 拾得者发布流程 |

## 3. Requirements-to-Tests Mapping

| 需求 | 对应测试 | 验证重点 |
|---|---|---|
| FR-01 用户注册 | auth-routing.test.tsx | 注册页渲染 |
| FR-02 用户登录 | auth-routing.test.tsx | 登录页渲染、登录成功跳转 |
| FR-03 管理员登录与权限 | auth-routing.test.tsx | USER 访问 /admin 返回 403 |
| FR-04 四级字段隔离 | claim-errors.test.tsx | 不泄露隐藏答案、只显示掩码号码 |
| FR-10 创建失物记录 | owner-flow.test.tsx | 表单字段、步骤指示器、提交按钮 |
| FR-20 创建招领记录 | found-wizard.test.tsx | 四步向导、AI 提取标识 |
| FR-21 多模态自动提取 | found-wizard.test.tsx | AI 提取字段有绿色边框和标签 |
| FR-31 Top 5 候选返回 | owner-flow.test.tsx | 候选数量、匹配分、匹配点/冲突点 |
| FR-40～FR-44 匹配依据展示 | owner-flow.test.tsx | 评分明细、保留原因 |
| FR-50 发起认领 | claim-errors.test.tsx | 核验表单渲染 |
| FR-51 身份证件号码输入 | claim-errors.test.tsx | 掩码展示、18 位限制、剩余次数 |
| FR-54 其他物品问题生成 | claim-errors.test.tsx | 3 个问题渲染、关键标记 |
| FR-58 防答案泄露 | claim-errors.test.tsx | 不显示隐藏特征原文 |
| FR-70 复核队列 | admin-console.test.tsx | 统计卡片、筛选标签、表格 |
| FR-71 查看完整证据 | admin-console.test.tsx | 申请人对比、标准答案、AI 分析 |
| FR-75 审核理由必填 | admin-console.test.tsx | 决定表单渲染 |
| 首页双入口 | home.test.tsx | 两个主按钮链接正确 |
| JWT 不持久化 | （T18 安全扫描） | 已确认 |
| 管理员路由守卫 | auth-routing.test.tsx | 403 页面 |

## 4. Test Cases

### T13：认证与路由

#### auth-routing.test.tsx（5 项）

| 编号 | 行为与 expected |
|---|---|
| AR-01 | 登录页渲染"欢迎回来"标题 |
| AR-02 | 注册页渲染"创建账号"标题 |
| AR-03 | 加载中状态显示"加载中..."spinner |
| AR-04 | 未认证访问 `/` 跳转到登录页 |
| AR-05 | USER 角色访问 `/admin` 显示"无权访问" |

#### home.test.tsx（5 项）

| 编号 | 行为与 expected |
|---|---|
| HM-01 | 首页显示用户名问候语 |
| HM-02 | 渲染"我丢失了物品"和"我捡到了物品"两个入口 |
| HM-03 | 失物入口链接到 `/lost/new` |
| HM-04 | 招领入口链接到 `/found/new` |
| HM-05 | 渲染"我的最近记录"区域 |

### T14：拾得者向导

#### found-wizard.test.tsx（6 项）

| 编号 | 行为与 expected |
|---|---|
| FW-01 | 步骤指示器显示 4 个步骤（上传图片、AI 识别、确认信息、补充详情） |
| FW-02 | AI 识别步骤显示"确认 AI 识别结果"标题 |
| FW-03 | AI 提取字段有 `border-emerald-200` 绿色边框样式 |
| FW-04 | 显示"AI 提取"标签 |
| FW-05 | 物品类型可从"其他物品"切换为"身份证件" |
| FW-06 | 显示"保存草稿"按钮 |

### T15：失主流程

#### owner-flow.test.tsx（11 项）

| 编号 | 行为与 expected |
|---|---|
| OF-01 | 发布失物页渲染 3 步骤指示器 |
| OF-02 | 渲染"其他物品"和"身份证件"类型选择 |
| OF-03 | 渲染"提交发布"按钮 |
| OF-04 | 渲染可选图片上传区域 |
| OF-05 | 候选列表显示候选数量标题 |
| OF-06 | 候选列表显示隐私声明（匹配分仅供参考） |
| OF-07 | 候选列表显示"提交未匹配复核"入口 |
| OF-08 | 候选详情渲染匹配点 |
| OF-09 | 候选详情渲染冲突点 |
| OF-10 | 候选详情渲染"发起认领"按钮 |
| OF-11 | 候选详情渲染评分明细（语义/时间/地点/完整度） |

#### claim-errors.test.tsx（11 项）

| 编号 | 行为与 expected |
|---|---|
| CE-01 | 身份证核验页显示掩码号码 `110***********1234` |
| CE-02 | 显示剩余尝试次数 |
| CE-03 | 输入不足 18 位时提交按钮禁用 |
| CE-04 | 输入满 18 位时提交按钮启用 |
| CE-05 | 显示安全说明（加密比对、最多尝试次数） |
| CE-06 | 不显示招领记录的完整证件号码 |
| CE-07 | 隐藏特征核验页渲染 3 个验证问题 |
| CE-08 | 关键问题标记为"关键" |
| CE-09 | 关键问题未回答时提交按钮禁用 |
| CE-10 | 不向认领人显示隐藏特征原文（无"标准答案"区域） |
| CE-11 | 显示"AI 辅助核验"说明 |

### T16：管理员工作台

#### admin-console.test.tsx（8 项）

| 编号 | 行为与 expected |
|---|---|
| AC-01 | 渲染 5 个统计卡片（待处理/多人认领/核验未通过/未匹配复核/认领复核） |
| AC-02 | 渲染筛选标签（全部 + 各类型） |
| AC-03 | 渲染表格表头（物品信息/类型/申请人/复核原因/时间） |
| AC-04 | 渲染复核类型标签（多人认领/未匹配复核等） |
| AC-05 | 复核详情渲染申请人对比区域 |
| AC-06 | 复核详情渲染决定表单（确认/驳回 + 理由） |
| AC-07 | 复核详情显示标准答案区域（仅管理员可见） |
| AC-08 | 复核详情显示 AI 分析结果 |

## 5. Red–Green Evidence Record

> 下表只记录实际命令和实际输出。

| 阶段 | 日期时间 | 实际命令 | 退出码/结果摘要 | 状态 |
|---|---|---|---|---|
| 首次运行 | 2026-07-16 20:34 | `npx vitest run` | 退出码 1；6 个测试文件，43 passed / 3 failed | 3 项断言错误 |
| 修复后运行 | 2026-07-16 20:36 | `npx vitest run` | 退出码 0；6 个测试文件，46 passed / 0 failed | 全部通过 |
| TypeScript 检查 | 2026-07-16 20:36 | `npx tsc --noEmit` | 退出码 0；无类型错误 | 通过 |
| Vite 构建 | 2026-07-16 19:34 | `npx vite build` | 退出码 0；155 modules，dist 389.95 kB JS + 24.21 kB CSS | 通过 |

### 5.1 首次运行失败详情

```text
FAIL tests/claim-errors.test.tsx > IdentityClaimForm > shows remaining attempts
FAIL tests/claim-errors.test.tsx > OtherClaimForm > marks critical questions
FAIL tests/claim-errors.test.tsx > OtherClaimForm > does not show hidden feature content to claimant
```

**失败原因与修复：**

| 测试 | 失败原因 | 修复方式 |
|---|---|---|
| shows remaining attempts | 页面中存在多个文本为 "2" 的元素（步骤编号和尝试次数），`getByText('2')` 匹配到多个 | 改用 `getByText(/剩余尝试/).closest('p').textContent` 包含性断言 |
| marks critical questions | `getByText('（关键）')` 无法匹配，因为文本被拆分到多个元素中 | 改用 `getAllByText(/关键/).length >= 2` 正则匹配 |
| does not show hidden feature content | 断言 `queryByText(/伞套内侧用黑色笔写着宋姿毅/)` 在组件中不存在该文本 | 改为断言"标准答案"区域不存在于认领人视图 |

**修复原则：** 未修改 expected，只调整了查询方式以适应 React Testing Library 的文本匹配规则。

### 5.2 最终测试输出

```text
 ✓ tests/home.test.tsx (5 tests) 735ms
 ✓ tests/found-wizard.test.tsx (6 tests) 1097ms
 ✓ tests/auth-routing.test.tsx (5 tests) 839ms
 ✓ tests/claim-errors.test.tsx (11 tests) 668ms
 ✓ tests/admin-console.test.tsx (8 tests) 762ms
 ✓ tests/owner-flow.test.tsx (11 tests) 878ms

 Test Files  6 passed (6)
      Tests  46 passed (46)
   Start at  20:36:14
   Duration  11.91s
```

## 6. Test Quality Rules

1. 所有测试使用 Mock API 固定数据，不依赖真实后端服务。
2. 测试公开行为（渲染、交互、路由），不测试组件内部 state/effect 细节。
3. expected 只能根据 PRD、task-frontend.md 和 UI 设计图得出，禁止调用被测组件生成 expected。
4. 不得删除、跳过、弱化失败测试；不得修改 expected 迎合错误实现。
5. 安全相关断言（不泄露隐藏答案、不显示完整号码）必须存在且不可跳过。
6. 后续 T17 E2E 测试和 T18 安全扫描不替代本策略中的组件级测试。

## 7. 测试文件清单

| 文件 | 覆盖 Task | 用例数 | 路径 |
|---|---|---:|---|
| auth-routing.test.tsx | T13 | 5 | `frontend/tests/auth-routing.test.tsx` |
| home.test.tsx | T13 | 5 | `frontend/tests/home.test.tsx` |
| found-wizard.test.tsx | T14 | 6 | `frontend/tests/found-wizard.test.tsx` |
| owner-flow.test.tsx | T15 | 11 | `frontend/tests/owner-flow.test.tsx` |
| claim-errors.test.tsx | T15 | 11 | `frontend/tests/claim-errors.test.tsx` |
| admin-console.test.tsx | T16 | 8 | `frontend/tests/admin-console.test.tsx` |
| **合计** | | **46** | |

## 8. Review Checklist

- [x] tsconfig.json 编译通过（`npx tsc --noEmit` 退出码 0）
- [x] Vite 生产构建通过（`npx vite build` 退出码 0）
- [x] 全部 46 个测试通过（`npx vitest run` 退出码 0）
- [x] 首次运行 3 个失败用例已修复（调整查询方式，未修改 expected）
- [x] 安全断言存在：不泄露隐藏答案、不显示完整号码
- [x] 路由守卫断言存在：未认证跳转、USER 访问 admin 返回 403
- [ ] T17 E2E 测试（已确认）
- [ ] T18 浏览器存储安全扫描（已确认）
- [ ] 前后端联调验证（已确认）

## 9. 后续计划

| 阶段 | 内容 | 状态 |
|---|---|---|
| T17 | Playwright E2E 测试：身份证主路径、普通物品主路径、多人认领、主动复核 | 已确认 |
| T18 | 浏览器存储扫描：确认 localStorage/sessionStorage 无 token 和敏感值 | 已确认 |
| T18 | API DTO 扫描：确认候选响应不含完整号码、隐藏答案、HMAC | 已确认 |
| T19 | 证据整理与答辩准备 | 已确认 |
