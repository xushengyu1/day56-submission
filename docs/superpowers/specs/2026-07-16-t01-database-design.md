# T01 数据模型与分步迁移设计

## 目标

为后续认证、发布、匹配、核验、复核和审计任务提供与 PRD V0.9/详细设计 V1.4 一致的 PostgreSQL 数据基础。实现稳定枚举、核心表、pgvector 扩展以及可验证的数据不变量。

代码使用当前仓库实际目录 `src/backend`。旧分支 `codex/t001-health-scaffold` 只作为 `VectorType`、异步 SQLAlchemy 会话和迁移组织的参考，不复制其旧版状态或旧表定义。

## 迁移顺序

六段迁移严格按 `dev.md`：

1. `0001_enable_vector_and_enums`：启用 `vector`，创建数据库枚举。
2. `0002_users_and_refresh_tokens`：`users`、`refresh_tokens`。
3. `0003_item_records_and_images`：`item_records`、`image_assets`、`ai_extractions`，并加入公开 embedding 列。
4. `0004_identity_and_verification`：身份证秘密、问题集和问题。
5. `0005_candidates_claims_reviews`：候选、认领、尝试、两类主动复核和管理员决定。
6. `0006_audit_and_idempotency`：只追加审计事件和幂等结果。

每段 migration 都有可逆 downgrade；空库 upgrade、完整 downgrade/upgrade 和 metadata 对齐均纳入证据。

## 枚举与表边界

`app/db/enums.py` 定义并导出 `UserRole`、`ItemType`、`RecordKind`、`RecordStatus`、`ClaimStatus`、`DataClass`、`ActorType`、`ImagePurpose`、`RedactionStatus`、`ExtractionStatus`、`QuestionResult`、`DocumentType`、`AdminDecision`、`ReviewRequestType`。数据库保存英文值，API 后续使用同一枚举。

模型按职责拆分：

- `auth/models.py`：`users`、`refresh_tokens`。
- `items/models.py`：`item_records`，包括 `version`、公开字段、精确时间/地点和 embedding。
- `images/models.py`：`image_assets`。
- `multimodal/models.py`：`ai_extractions`。
- `verification/models.py`：`identity_document_secrets`、`verification_sets`、`verification_questions`。
- `matching/models.py`：`candidate_matches`。
- `reviews/models.py`：`claims`、`claim_attempts`、`review_requests`、`admin_reviews`。
- `audit/models.py`：`audit_events`、`idempotency_results`。
- `db/models.py`：集中导入所有模型，保证 Alembic metadata 完整。

身份证秘密和 OTHER 问题集通过 `item_type` 复合外键分别锁定 `IDENTITY_DOCUMENT` 与 `OTHER`，避免同一 FOUND 记录同时持有两类核验材料。身份证 HMAC 不建立唯一约束，以允许重复招领检测。

## 关键数据库不变量

- `image_assets` 为 `PUBLIC_REDACTED` 时必须同时是 `PUBLIC` 且 `CONFIRMED`；PRIVATE 原图不能走公开数据类。
- `review_requests` 的 `UNMATCHED` 只能有 `lost_record_id`，`CLAIM_REVIEW` 只能有 `claim_id`；两个目标列不能同时存在。
- 同一用户与同一目标最多一条活动复核请求，使用 PostgreSQL 部分唯一索引。
- `item_records.version >= 1`；embedding 只存公开确认文本，使用自定义 `VectorType` 编译为 PostgreSQL `vector`。
- 所有跨表外键使用明确的删除策略；不在 migration、seed 或日志中写入完整身份证号码或隐藏答案。

## 测试与环境

先写 `tests/integration/db/test_migrations.py` 和 `test_model_constraints.py`，在模块/迁移不存在时观察 Red。Green 阶段使用 Docker pgvector PostgreSQL 执行真实迁移；本机目前可用镜像为 `pgvector/pgvector:0.8.1-pg17`，若无法取得 PostgreSQL 16 镜像，则在证据中记录环境差异，不伪称为 16.x。

集成测试通过 `DATABASE_URL` 连接测试库；迁移命令单独执行 `alembic downgrade base`、`alembic upgrade head`，测试再验证表、扩展、列、约束和索引。测试数据全部使用 UUID、合成邮箱和非敏感占位文本。

## 非目标

T01 不实现认证 API、密码策略、图片上传、AI 调用、候选评分、认领服务或管理员业务逻辑；这些由 T03～T11 逐任务实现。
