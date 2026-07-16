# 后端开发任务计划（成员A）

> **负责范围：** T00-T12（后端全部）
> **交付物：** 完整的FastAPI后端API、数据库、AI集成
> **预计工时：** 18-20小时

---

## 开发顺序

```
T00 → T01 → T02 → T03 → T04 → T05/T06（并行） → T07 → T08 → T09/T10（并行） → T11 → T12
```

---

## 环境准备

### 本地环境要求
- Python 3.11+
- PostgreSQL 16 + pgvector扩展
- Docker Desktop
- Git

### 初始化命令
```bash
# 克隆项目
git clone <repo>
cd day6

# 创建后端分支
git checkout -b feature/backend

# 启动PostgreSQL
docker compose up -d postgres

# 创建虚拟环境
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Task T00：建立工程骨架

**目标：** 创建后端、数据库和mock服务骨架

**文件清单：**
- `docker-compose.yml`
- `.env.example`
- `.gitignore`
- `backend/pyproject.toml`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/tests/unit/test_health.py`
- `ai-mock/app.py`

**验收标准：**
```bash
# 运行health测试
pytest tests/unit/test_health.py -q

# 预期：/api/health/live 返回 {"status":"ok"}
# 预期：/ready 在数据库不可用时返回 503
```

**建议提交：** `chore(scaffold): initialize backend postgres and ai mock`

---

## Task T01：建立数据模型与迁移

**目标：** 实现数据库结构

**文件清单：**
- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `backend/app/db/enums.py`
- `backend/app/{auth,items,images,multimodal,matching,verification,reviews,audit}/models.py`
- `backend/alembic/versions/0001_*.py` 至 `0006_*.py`
- `backend/tests/integration/db/test_migrations.py`
- `backend/tests/integration/db/test_model_constraints.py`

**验收标准：**
```bash
# 运行迁移测试
pytest tests/integration/db/ -q

# 验证迁移
alembic downgrade base
alembic upgrade head
```

**建议提交：** `feat(db): add pgvector schema constraints and migrations`

---

## Task T02：实现安全纯函数

**目标：** 实现不依赖数据库的核心规则

**文件清单：**
- `backend/app/verification/identity.py`
- `backend/app/verification/other.py`
- `backend/app/matching/scoring.py`
- `backend/app/items/state_machine.py`
- `backend/tests/unit/verification/test_identity.py`
- `backend/tests/unit/verification/test_other_rules.py`
- `backend/tests/unit/matching/test_scoring.py`
- `backend/tests/unit/items/test_state_machine.py`

**锁定接口：**
```python
normalize_cn_id(value: str) -> str
validate_cn_id(value: str) -> bool
compute_id_hmac(normalized: str, key: bytes) -> str
mask_cn_id(normalized: str) -> str
score_candidate(features: CandidateFeatures) -> CandidateScore
validate_question_set(draft: QuestionSetDraft) -> QuestionSetValidation
can_transition_record(current: RecordStatus, target: RecordStatus) -> bool
can_transition_claim(current: ClaimStatus, target: ClaimStatus) -> bool
```

**验收标准：**
```bash
pytest tests/unit/verification tests/unit/matching tests/unit/items -q
```

**建议提交：** `feat(core): implement deterministic verification scoring and state machines`

---

## Task T03：实现认证与RBAC

**目标：** 建立用户认证和权限控制

**文件清单：**
- `backend/app/auth/schemas.py`
- `backend/app/auth/security.py`
- `backend/app/auth/service.py`
- `backend/app/auth/rbac.py`
- `backend/app/api/deps.py`
- `backend/app/api/routes/auth.py`
- `backend/tests/unit/auth/test_security.py`
- `backend/tests/integration/api/test_auth.py`
- `backend/tests/integration/api/test_rbac.py`

**API接口：**
```
POST /api/auth/register
POST /api/auth/login
POST /api/auth/refresh
```

**验收标准：**
```bash
pytest tests/unit/auth tests/integration/api/test_auth.py tests/integration/api/test_rbac.py -q
```

**建议提交：** `feat(auth): add jwt sessions and resource level authorization`

---

## Task T04：实现审计与幂等

**目标：** 实现操作日志和幂等性

**文件清单：**
- `backend/app/audit/schemas.py`
- `backend/app/audit/service.py`
- `backend/app/audit/projection.py`
- `backend/app/core/logging.py`
- `backend/app/core/idempotency.py`
- `backend/app/core/clock.py`
- `backend/app/core/ids.py`
- `backend/app/api/errors.py`
- `backend/tests/unit/audit/test_redaction.py`
- `backend/tests/unit/audit/test_projection.py`
- `backend/tests/integration/audit/test_audit_transaction.py`
- `backend/tests/integration/audit/test_idempotency.py`

**验收标准：**
```bash
pytest tests/unit/audit tests/integration/audit -q
```

**建议提交：** `feat(audit): add redacted audit projection and idempotency`

---

## Task T05：实现图片服务

**目标：** 实现图片上传、存储和脱敏

**文件清单：**
- `backend/app/images/schemas.py`
- `backend/app/images/storage.py`
- `backend/app/images/redaction.py`
- `backend/app/images/service.py`
- `backend/app/api/routes/uploads.py`
- `backend/tests/unit/images/test_validation.py`
- `backend/tests/unit/images/test_redaction.py`
- `backend/tests/integration/images/test_storage_access.py`
- `backend/tests/integration/images/test_cleanup.py`

**验收标准：**
```bash
pytest tests/unit/images tests/integration/images -q
```

**建议提交：** `feat(images): isolate private assets and create confirmed redactions`

---

## Task T06：实现AI适配器

**目标：** 隔离AI供应商细节

**文件清单：**
- `backend/app/multimodal/ports.py`
- `backend/app/multimodal/schemas.py`
- `backend/app/multimodal/openai_compatible.py`
- `backend/app/multimodal/mock.py`
- `backend/app/matching/embedding.py`
- `ai-mock/fixtures/*.json`
- `backend/tests/contract/test_extraction_contract.py`
- `backend/tests/contract/test_question_contract.py`
- `backend/tests/contract/test_verification_contract.py`
- `backend/tests/contract/test_embedding_contract.py`

**锁定接口：**
```python
extract_found_item(image_ref, context) -> ExtractionDraft
generate_questions(hidden_description) -> QuestionSetDraft
verify_answers(question_set, answers) -> VerificationResult
embed_public_text(texts: list[str]) -> list[list[float]]
```

**验收标准：**
```bash
docker compose up -d ai-mock
pytest tests/contract -q
```

**建议提交：** `feat(ai): add validated openai compatible ports and deterministic mock`

---

## Task T07：实现招领发布

**目标：** 实现拾得者发布招领信息

**文件清单：**
- `backend/app/items/schemas.py`
- `backend/app/items/policies.py`
- `backend/app/items/service.py`
- `backend/app/api/routes/found_records.py`
- `backend/tests/integration/items/test_found_draft.py`
- `backend/tests/integration/items/test_found_identity_publish.py`
- `backend/tests/integration/items/test_found_other_publish.py`

**API接口：**
```
POST /api/uploads
POST /api/found-records
POST /api/found-records/{id}/extract
PUT  /api/found-records/{id}/confirmation
POST /api/found-records/{id}/identity-confirmation
POST /api/found-records/{id}/redaction
POST /api/found-records/{id}/questions
POST /api/found-records/{id}/publish
```

**验收标准：**
```bash
pytest tests/integration/items/test_found_draft.py tests/integration/items/test_found_identity_publish.py tests/integration/items/test_found_other_publish.py -q
```

**建议提交：** `feat(found): add human confirmed multimodal publishing workflows`

---

## Task T08：实现失物与候选

**目标：** 实现失物发布和候选匹配

**文件清单：**
- `backend/app/matching/schemas.py`
- `backend/app/matching/service.py`
- `backend/app/api/routes/lost_records.py`
- `backend/app/api/routes/candidates.py`
- `backend/tests/integration/matching/test_candidate_query.py`
- `backend/tests/integration/matching/test_candidate_scoring.py`
- `backend/tests/integration/matching/test_candidate_dto_privacy.py`

**API接口：**
```
POST /api/lost-records
GET  /api/lost-records/{id}/candidates
GET  /api/candidates/{id}
```

**验收标准：**
```bash
pytest tests/integration/matching -q
```

**建议提交：** `feat(matching): add public text vector candidates and safe projections`

---

## Task T09：实现身份证认领

**目标：** 实现身份证核验认领

**文件清单：**
- `backend/app/verification/service.py`
- `backend/app/api/routes/claims.py`
- `backend/tests/integration/verification/test_identity_claim.py`
- `backend/tests/integration/verification/test_identity_attempt_concurrency.py`
- `backend/tests/integration/verification/test_duplicate_identity_routing.py`

**API接口：**
```
POST /api/candidates/{id}/claims/identity
```

**验收标准：**
```bash
pytest tests/integration/verification/test_identity_claim.py tests/integration/verification/test_identity_attempt_concurrency.py tests/integration/verification/test_duplicate_identity_routing.py -q
```

**建议提交：** `feat(identity): enforce hmac verification attempts and duplicate routing`

---

## Task T10：实现OTHER认领

**目标：** 实现普通物品隐藏问题认领

**文件清单：**
- `backend/app/verification/other.py`（完善）
- `backend/app/verification/service.py`（完善）
- `backend/app/verification/schemas.py`（完善）
- `backend/app/api/routes/claims.py`（修改）
- `backend/tests/integration/verification/test_other_questions_api.py`
- `backend/tests/integration/verification/test_other_claim_routing.py`
- `backend/tests/integration/verification/test_other_model_failure.py`

**API接口：**
```
GET  /api/candidates/{id}/questions
POST /api/candidates/{id}/claims/answers
```

**验收标准：**
```bash
pytest tests/integration/verification/test_other_questions_api.py tests/integration/verification/test_other_claim_routing.py tests/integration/verification/test_other_model_failure.py -q
```

**建议提交：** `feat(other): add open question claims with conservative routing`

---

## Task T11：实现管理员复核

**目标：** 实现复核队列和管理员决定

**文件清单：**
- `backend/app/reviews/schemas.py`
- `backend/app/reviews/service.py`
- `backend/app/api/routes/admin.py`
- `backend/tests/integration/reviews/test_review_requests.py`
- `backend/tests/integration/reviews/test_review_queue.py`
- `backend/tests/integration/reviews/test_admin_decision.py`

**API接口：**
```
GET  /api/admin/reviews
GET  /api/admin/reviews/{id}
POST /api/admin/reviews/{id}/decision
GET  /api/admin/audit-events
POST /api/lost-records/{id}/review-requests
POST /api/claims/{id}/review-requests
```

**验收标准：**
```bash
pytest tests/integration/reviews -q
```

**建议提交：** `feat(reviews): add owner requests and focused admin decisions`

---

## Task T12：实现交接与时间线

**目标：** 完成交接闭环

**文件清单：**
- `backend/app/api/routes/handoffs.py`
- `backend/app/api/routes/records.py`
- `backend/app/items/service.py`（完善）
- `backend/app/audit/projection.py`（完善）
- `backend/tests/integration/handoffs/test_contact_access.py`
- `backend/tests/integration/handoffs/test_handoff_complete.py`
- `backend/tests/integration/handoffs/test_timeline_projection.py`

**API接口：**
```
GET  /api/claims/{id}/contact
POST /api/claims/{id}/handoff-complete
GET  /api/records/{id}/timeline
```

**验收标准：**
```bash
pytest tests/integration/handoffs -q
```

**建议提交：** `feat(handoff): close claims with scoped contact and audit timelines`

---

## 后端完整验证

完成T12后，运行完整验证：

```bash
# 运行所有测试
pytest -q

# 检查代码质量
ruff check .
mypy .

# 验证API文档
# 访问 http://localhost:8000/docs 查看Swagger UI
```

---

## 与前端对接准备

完成后端后，提供给前端开发者：

1. **API文档**：`http://localhost:8000/docs`（Swagger UI）
2. **OpenAPI规范**：`http://localhost:8000/openapi.json`
3. **环境变量**：`.env.example` 文件
4. **启动命令**：`docker compose up -d`
5. **测试账号**：在seed脚本中创建

---

## 注意事项

1. **不修改前端代码**：只关注backend/目录
2. **数据库迁移**：所有迁移脚本放在 `backend/alembic/versions/`
3. **接口规范**：严格按照task.md定义的接口实现
4. **测试覆盖**：每个Task都有对应的测试
5. **敏感数据**：确保不泄露完整身份证号、隐藏答案等
