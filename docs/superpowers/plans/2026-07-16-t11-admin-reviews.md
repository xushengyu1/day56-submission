# T11 管理员复核实施计划

**Goal:** 完成主动复核、最小队列、管理员幂等决定与审计。

## Task 1：主动复核

- [ ] 写 `test_review_requests.py` Red 测试
- [ ] 实现 reviews schemas/service 与 owner routes
- [ ] 运行 focused test

## Task 2：队列投影

- [ ] 写 `test_review_queue.py` Red 测试
- [ ] 实现 admin list/detail/audit 安全 DTO
- [ ] 运行 focused test

## Task 3：管理员决定

- [ ] 写 `test_admin_decision.py` Red 测试
- [ ] 实现 reason、状态机、幂等、审计
- [ ] 运行 focused test

## Task 4：回归、证据、提交

- [ ] 更新 `evidence/development-records/T11.md`
- [ ] 运行 focused、全量 pytest、compileall、diff check
- [ ] 提交 `feat(reviews): add owner requests and focused admin decisions` 并推送
