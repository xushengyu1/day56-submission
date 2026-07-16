# T09 身份证认领设计

## 目标

实现身份证候选的确定性 HMAC 核验、每用户/候选最多 2 次尝试、并发安全计数和重复证件人工路由。服务不保存或返回完整号码，也不说明具体哪一位错误。

## 事务流程

1. 校验 candidate 存在、LOST 属于 requester、FOUND 类型为 `IDENTITY_DOCUMENT`。
2. 对 candidate 行 `FOR UPDATE`，串行化同候选的尝试创建；查询该用户/候选已有尝试数。
3. 若已 2 次，返回 `ATTEMPT_LOCKED`；否则规范化号码并计算当前 key version HMAC。
4. 创建/复用 claim，追加 `ClaimAttempt`，只保存 HMAC、attempt_no 和稳定 result code。
5. HMAC 不匹配：第 1 次保持 `VERIFYING`，第 2 次置 `LOCKED`。
6. HMAC 匹配且只有一条活动 FOUND：claim 与 LOST/FOUND 进入 `PENDING_HANDOFF`。
7. 同 HMAC 对应多条活动 FOUND 或存在其他活动认领：claim 进入 `PENDING_ADMIN_REVIEW`，risk flag 记录固定代码。
8. 状态、attempt 和审计事件同事务提交。

## 并发与隐私

- candidate 行锁是本任务的串行化点；并发两次错误提交只能产生 attempt 1/2，不会出现 attempt 3 或重复编号。
- 错误响应只使用 `IDENTITY_NOT_VERIFIED` / `ATTEMPT_LOCKED`；不返回 HMAC、掩码差异或重复记录细节。
- audit metadata 只记录 attempt_no、result_code 和 route_source。

## 验证

- 正确唯一号码进入待交接，错误号码不泄漏差异。
- 并发两次失败恰好产生两个连续 attempt 并锁定。
- 重复 HMAC 进入管理员复核，不自动待交接。
- 全量回归、compileall、diff check。
