# T02 安全纯函数、评分与状态机设计

## 目标

实现不依赖数据库或外部模型的确定性规则，作为后续认证、候选和认领服务的唯一规则入口。所有异常信息不得包含完整身份证号码、隐藏答案或原始敏感值。

## 模块边界

- `app/verification/identity.py`：居民身份证 NFKC/空白规范化、18 位格式与校验位、HMAC-SHA256 和前 3 后 4 掩码。
- `app/verification/other.py`：2～3 个开放式问题、唯一维度、问题不包含答案/隐藏事实的安全校验。
- `app/matching/scoring.py`：记录方向和物品类型硬门槛；语义/时间/地点/完整度按 50/20/20/10 计算；稳定 Top 5 排序。
- `app/items/state_machine.py`：集中定义记录和认领的允许状态迁移。

T02 不实现密码、JWT、数据库服务、AI 调用或 HTTP 路由。

## 锁定接口与类型

保留任务表接口：

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

输入/输出使用 frozen dataclass；评分额外提供 `rank_top_candidates`，方便后续服务复用。

## 规则细节

- 身份证：NFKC、去除所有 Unicode 空白、末位统一大写 `X`；校验长度、前 17 位数字、日期和国家标准校验位。非法输入只抛出稳定错误，不把原值插入消息。
- HMAC：要求非空 key，返回 SHA-256 hex；掩码固定前 3 后 4，中间全部 `*`。
- OTHER：问题数量必须为 2～3；每题必须开放式、文本非空、维度不重复；规范化后的答案不能出现在问题文本或题组公开文本中。
- 评分：记录方向必须 LOST↔FOUND，物品类型必须相同，分类文本必须相等（大小写/空白不敏感）；语义分最多 50，时间最多 20，地点最多 20，完整度最多 10。并列总分按 `candidate_id` 升序稳定排序，最多返回 5 条。
- 状态机：终态 `CLOSED/CANCELLED/CLAIMED/REJECTED/LOCKED` 不允许任意回退；特别禁止 `DRAFT → CLAIMED` 和 `PENDING_ADMIN_REVIEW → CLAIMED`。

## 验证

先运行单元 Red，再运行 T02 目录和全量后端 pytest。测试覆盖身份证边界、HMAC 等价性/异常脱敏、问题质量、评分权重/硬门槛/Top 5 tie-break，以及所有状态迁移。证据写入 `evidence/development-records/T02.md`，T02 通过后单独提交并推送。
