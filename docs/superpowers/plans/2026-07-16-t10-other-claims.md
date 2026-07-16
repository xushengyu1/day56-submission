# T10 OTHER 认领实施计划

**Goal:** 完成安全问题投影、开放回答核验和保守人工路由。

## Task 1：问题 API

- [x] 写 `test_other_questions_api.py` Red 测试
- [x] 完善 verification schemas/service 和 questions route
- [x] 运行 focused test

## Task 2：认领路由

- [x] 写 `test_other_claim_routing.py` Red 测试
- [x] 实现全匹配/部分/冲突/多人认领路由
- [x] 运行 focused test

## Task 3：模型失败

- [x] 写 `test_other_model_failure.py` Red 测试
- [x] 实现异常转管理员和安全摘要
- [x] 运行 focused test

## Task 4：回归、证据、提交

- [x] 更新 `evidence/development-records/T10.md`
- [x] 运行 focused、全量 pytest、compileall、diff check
- [x] 提交 `feat(other): add open question claims with conservative routing` 并推送
