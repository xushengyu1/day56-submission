# 前端开发任务计划（成员B）

> **负责范围：** T13-T16（前端）+ T17-T19（E2E测试与文档）
> **交付物：** 完整的React前端、E2E测试、文档交付包
> **预计工时：** 15-18小时

---

## 开发顺序

```
T13 → T14/T15/T16（并行） → T17 → T18 → T19
```

---

## 环境准备

### 本地环境要求
- Node.js 18+
- Docker Desktop
- Git
- 后端API（可使用mock或连接成员A的后端）

### 初始化命令
```bash
# 克隆项目
git clone <repo>
cd day6

# 创建前端分支
git checkout -b feature/frontend

# 安装前端依赖
cd frontend
npm install

# 启动开发服务器（使用mock API）
npm run dev
```

### API对接方案

**方案1：使用Mock API（推荐）**
```bash
# 启动mock服务
docker compose up -d ai-mock

# 前端配置mock API地址
VITE_API_BASE_URL=http://localhost:8001
```

**方案2：连接成员A的后端**
```bash
# 获取成员A的后端地址
VITE_API_BASE_URL=http://<成员A的IP>:8000
```

---

## Task T13：实现前端应用壳与认证

**目标：** 建立前端基础架构和认证

**文件清单：**
- `frontend/src/app/router.tsx`
- `frontend/src/app/providers.tsx`
- `frontend/src/app/queryClient.ts`
- `frontend/src/api/client.ts`
- `frontend/src/api/types.ts`
- `frontend/src/api/errors.ts`
- `frontend/src/features/auth/api.ts`
- `frontend/src/features/auth/hooks.ts`
- `frontend/src/features/auth/LoginPage.tsx`
- `frontend/src/features/auth/RegisterPage.tsx`
- `frontend/src/features/auth/guards.tsx`
- `frontend/src/features/home/HomePage.tsx`
- `frontend/src/components/UserLayout.tsx`
- `frontend/src/components/AdminLayout.tsx`
- `frontend/src/components/ErrorState.tsx`
- `frontend/tests/auth-routing.test.tsx`
- `frontend/tests/home.test.tsx`

**验收标准：**
```bash
# 运行测试
npm run test -- --run tests/auth-routing.test.tsx tests/home.test.tsx

# 类型检查
npm run typecheck

# 预期：
# - 未登录访问业务页跳转登录
# - USER访问/admin显示无权
# - ADMIN进入独立Layout
# - 首页两个主按钮跳转正确
```

**建议提交：** `feat(frontend): add auth shell dual task home and admin guard`

---

## Task T14：实现拾得者发布向导

**目标：** 实现"我捡到了物品"四步向导

**文件清单：**
- `frontend/src/features/found-items/api.ts`
- `frontend/src/features/found-items/types.ts`
- `frontend/src/features/found-items/FoundWizardPage.tsx`
- `frontend/src/features/found-items/components/ImageUploadStep.tsx`
- `frontend/src/features/found-items/components/AiDraftStep.tsx`
- `frontend/src/features/found-items/components/IdentityConfirmationStep.tsx`
- `frontend/src/features/found-items/components/OtherVerificationStep.tsx`
- `frontend/src/features/found-items/components/PublishPreviewStep.tsx`
- `frontend/tests/found-wizard.test.tsx`
- `frontend/tests/found-sensitive-state.test.tsx`

**功能要点：**
1. 图片上传后显示AI loading/success/failure
2. AI值与人工修改值清晰区分
3. 身份证：逐位确认、脱敏预览、不泄露完整号码
4. OTHER：信息不足时显示"保存草稿"

**验收标准：**
```bash
npm run test -- --run tests/found-wizard.test.tsx tests/found-sensitive-state.test.tsx
```

**建议提交：** `feat(frontend): implement finder publishing wizard`

---

## Task T15：实现失主流程

**目标：** 实现"我丢失了物品"完整流程

**文件清单：**
- `frontend/src/features/lost-items/api.ts`
- `frontend/src/features/lost-items/LostCreatePage.tsx`
- `frontend/src/features/lost-items/LostDetailPage.tsx`
- `frontend/src/features/candidates/CandidateList.tsx`
- `frontend/src/features/candidates/CandidateDetailPage.tsx`
- `frontend/src/features/claims/IdentityClaimForm.tsx`
- `frontend/src/features/claims/OtherClaimForm.tsx`
- `frontend/src/features/claims/ClaimProgressPage.tsx`
- `frontend/src/features/claims/ReviewRequestDialog.tsx`
- `frontend/tests/owner-flow.test.tsx`
- `frontend/tests/candidate-privacy.test.tsx`
- `frontend/tests/claim-errors.test.tsx`
- `frontend/tests/owner-review-requests.test.tsx`

**功能要点：**
1. 失主图片上传不触发AI
2. 候选只渲染PUBLIC字段
3. 身份证错误不显示错误位
4. OTHER只显示开放问题
5. 无合适候选时可提交UNMATCHED
6. 核验失败可提交CLAIM_REVIEW

**验收标准：**
```bash
npm run test -- --run tests/owner-flow.test.tsx tests/candidate-privacy.test.tsx tests/claim-errors.test.tsx tests/owner-review-requests.test.tsx
```

**建议提交：** `feat(frontend): implement owner candidates claims and progress`

---

## Task T16：实现管理员工作台

**目标：** 实现管理员五类复核工作台

**文件清单：**
- `frontend/src/features/admin/api.ts`
- `frontend/src/features/admin/AdminQueuePage.tsx`
- `frontend/src/features/admin/AdminReviewPage.tsx`
- `frontend/src/features/admin/AdminAuditPage.tsx`
- `frontend/src/features/admin/components/MaskedEvidencePanel.tsx`
- `frontend/src/features/admin/components/DecisionForm.tsx`
- `frontend/src/features/admin/components/CandidateRecommendationPanel.tsx`
- `frontend/tests/admin-console.test.tsx`
- `frontend/tests/admin-review-types.test.tsx`

**功能要点：**
1. 默认只显示掩码和事件
2. 未匹配复核显示候选推荐动作
3. 认领复核显示确认待交接/驳回动作
4. 决定理由为空不能提交
5. 重复点击只发送同一幂等键

**验收标准：**
```bash
npm run test -- --run tests/admin-console.test.tsx tests/admin-review-types.test.tsx
```

**建议提交：** `feat(frontend): implement least privilege admin review console`

---

## Task T17：E2E测试

**目标：** 建立E2E测试覆盖主流程

**文件清单：**
- `backend/app/db/seed_demo.py`（与后端协商）
- `e2e/playwright.config.ts`
- `e2e/fixtures/users.ts`
- `e2e/fixtures/assets.ts`
- `e2e/fixtures/db.ts`
- `e2e/specs/identity-happy-path.spec.ts`
- `e2e/specs/ordinary-item-match.spec.ts`
- `e2e/specs/multiple-claims-admin-review.spec.ts`
- `e2e/specs/owner-review-requests.spec.ts`
- `e2e/assets/`（合成图片）

**测试场景：**
1. 身份证：拾得者发布 → 失主认领 → 联系方式 → 交接 → CLAIMED/CLOSED
2. 普通物品：隐藏问题全匹配 → PENDING_HANDOFF → 交接
3. 多人认领：两条申请 → 管理员确认 → 待交接
4. 主动复核：UNMATCHED/CLAIM_REVIEW → 管理员动作

**验收标准：**
```bash
# 启动完整环境
docker compose up --build -d

# 运行E2E测试
npx playwright test --config e2e/playwright.config.ts

# 预期：4个spec通过
```

**建议提交：** `test(e2e): prove identity other and admin review workflows`

---

## Task T18：边界与安全测试

**目标：** 验证系统拒绝、降级和防泄露

**文件清单：**
- `e2e/specs/failure-cases.spec.ts`
- `e2e/specs/security-boundaries.spec.ts`
- `backend/tests/security/test_sensitive_log_scan.py`（与后端协商）
- `backend/tests/security/test_api_projection_scan.py`（与后端协商）
- `frontend/tests/browser-storage-scan.test.tsx`
- `docs/validation/cases-and-results.md`（更新）
- `docs/validation/risk-and-edge-cases.md`（更新）

**测试场景：**
1. 模型将身份证末位X识别为0：拾得者修改确认前不能发布
2. 同号码两条活动记录：正确号码仍转管理员
3. OTHER隐藏描述只重复公开信息：只能保存草稿
4. 同账号第二次号码失败锁定
5. 模型超时/非法JSON：手工降级或转管理员
6. 脱敏未确认：不生成PUBLIC图片
7. 未授权联系方式、跨用户记录、USER访问admin全部拒绝
8. 同一决定/交接请求重复提交不产生双事件

**验收标准：**
```bash
# 前端测试
npm run lint
npm run typecheck
npm run test -- --run

# E2E测试
npx playwright test --config e2e/playwright.config.ts

# 后端测试（与后端协商）
docker compose exec backend pytest -q
```

**建议提交：** `test(security): cover failure routing privacy and full regression`

---

## Task T19：整理交付包

**目标：** 整理文档、演示脚本和证据

**文件清单：**
- `README.md`（更新）
- `docs/validation/cases-and-results.md`（更新）
- `docs/validation/review-record.md`（更新）
- `docs/ai/ai-collaboration-log.md`（更新）
- `szy-ai-log.md`（更新）
- `docs/reflection/individual-contributions.md`（更新）
- `prototype/screenshots-or-video.md`（更新）
- `docs/defense/defense-outline.md`（更新）
- `demo/demo-script.md`（新建）
- `demo/defense-questions.md`（新建）
- `evidence/development-records/T13.md` 至 `T19.md`

**交付清单：**
1. README：真实安装、启动、seed、测试和演示命令
2. 按模块标明真实实现、mock、手工降级和未实现能力
3. P0需求链接到设计、Task、测试用例和证据
4. AI日志：目的/输入/建议/人工判断/验证
5. 演示脚本：8-10分钟
6. 答辩准备：常见问题回答

**验收标准：**
```bash
# 从全新容器可复现
docker compose down
docker compose up --build -d

# 验证所有测试通过
docker compose exec backend pytest -q
npm run test -- --run
npx playwright test --config e2e/playwright.config.ts
```

**建议提交：** `docs(delivery): finalize reproducible evidence and defense package`

---

## 与后端对接

### 获取后端API

1. **API文档**：`http://localhost:8000/docs`（Swagger UI）
2. **OpenAPI规范**：`http://localhost:8000/openapi.json`

### 生成TypeScript类型

```bash
# 使用openapi-typescript生成类型
npx openapi-typescript http://localhost:8000/openapi.json -o src/api/types.ts
```

### 环境变量

```bash
# .env.local
VITE_API_BASE_URL=http://localhost:8000
```

---

## 前端技术栈

- **框架**：React 18 + TypeScript
- **构建**：Vite
- **路由**：React Router v6
- **状态管理**：TanStack Query
- **UI组件**：Ant Design / Shadcn/ui
- **测试**：Vitest + Testing Library + Playwright

---

## 注意事项

1. **不修改后端代码**：只关注frontend/和e2e/目录
2. **API对接**：使用TypeScript类型确保类型安全
3. **敏感数据**：不在浏览器存储token、完整号码等
4. **测试覆盖**：每个Task都有对应的测试
5. **文档完整**：T19必须完成所有文档
