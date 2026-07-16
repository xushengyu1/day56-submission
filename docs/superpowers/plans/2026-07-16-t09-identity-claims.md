# T09 身份证认领实施计划

**Goal:** 完成 HMAC 精确核验、2 次限制、并发锁和重复证件人工路由。

## Task 1：唯一匹配

- [ ] 写 `test_identity_claim.py` Red 测试
- [ ] 实现 verification schemas/service 和 identity route
- [ ] 运行 focused test

## Task 2：并发尝试

- [ ] 写 `test_identity_attempt_concurrency.py` Red 测试
- [ ] 实现 candidate 行锁与原子 attempt 编号
- [ ] 运行 focused test

## Task 3：重复路由

- [ ] 写 `test_duplicate_identity_routing.py` Red 测试
- [ ] 实现重复 HMAC/活动 claim 的人工路由
- [ ] 运行 focused test

## Task 4：回归、证据、提交

- [ ] 更新 `evidence/development-records/T09.md`
- [ ] 运行 focused、全量 pytest、compileall、diff check
- [ ] 提交 `feat(identity): enforce hmac verification attempts and duplicate routing` 并推送
