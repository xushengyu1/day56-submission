# T11 主动复核与管理员决定设计

## 目标

把 `UNMATCHED`、`CLAIM_REVIEW` 和异常 claim 汇入统一管理员队列，提供最小化证据 DTO、带理由的通过/拒绝、幂等结果和审计事件。

## 规则

- LOST owner 可为无合适候选提交一条活动 `UNMATCHED`；claim requester 可提交一条活动 `CLAIM_REVIEW`，数据库部分唯一索引兜底。
- 队列同时包含活动 ReviewRequest 与 `PENDING_ADMIN_REVIEW` claim；列表只显示掩码/类型/风险/result code/时间，不返回 HMAC、答案键、原始回答或 PRIVATE 路径。
- 详情按用途加载最小 VERIFICATION 摘要；OTHER 可显示 result/confidence/reason code，不显示原始回答；身份类仅显示 mask 和风险代码。
- 管理员决定必须 `ADMIN + 非空 reason + Idempotency-Key`。`APPROVE_TO_HANDOFF` 只把 claim/相关记录改为 `PENDING_HANDOFF`；`REJECT` 改为 `REJECTED`。
- 同 actor/key/body 返回原响应；同 key 不同 body 返回 `IDEMPOTENCY_KEY_REUSED`。决定、AdminReview、ReviewRequest 关闭、幂等结果和 audit 同事务提交。

## 验证

- 主动复核 owner/claim requester 权限与活动重复约束。
- 普通用户不能读取管理员队列；DTO 隐私扫描通过。
- 通过/拒绝状态正确、理由必填、重复决定不重复写 AdminReview/audit。
- 全量回归、compileall、diff check。
