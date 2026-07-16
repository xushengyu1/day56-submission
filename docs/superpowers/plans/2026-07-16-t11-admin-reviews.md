# T11 管理员复核实施计划

**Goal:** 完成主动复核、最小队列、管理员幂等决定与审计。

## Task 1：主动复核

- [x] 写 `test_review_requests.py` Red 测试
- [x] 实现 reviews schemas/service 与 owner routes
- [x] 运行 focused test

## Task 2：队列投影

- [x] 写 `test_review_queue.py` Red 测试
- [x] 实现 admin list/detail/audit 安全 DTO
- [x] 运行 focused test

## Task 3：管理员决定

- [x] 写 `test_admin_decision.py` Red 测试
- [x] 实现 reason、状态机、幂等、审计
- [x] 运行 focused test

## Task 4：回归、证据、提交

- [x] 更新 `evidence/development-records/T11.md`
- [x] 运行 focused、全量 pytest、compileall、diff check
- [x] 提交 `feat(reviews): add owner requests and focused admin decisions` 并推送
