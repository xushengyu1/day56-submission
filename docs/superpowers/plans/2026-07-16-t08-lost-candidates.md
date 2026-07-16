# T08 失物与候选实施计划

**Goal:** 完成 LOST 发布、候选评分快照、Top 5 查询和安全 DTO。

## Task 1：LOST 与候选生成

- [x] 写 candidate query/scoring Red 集成测试
- [x] 实现 matching schemas/service 与 lost route
- [x] 运行 focused tests

## Task 2：安全投影

- [x] 写 candidate DTO privacy Red 测试
- [x] 实现 candidates route 和 PUBLIC projection
- [x] 运行 focused tests

## Task 3：回归、证据、提交

- [x] 更新 `evidence/development-records/T08.md`
- [x] 运行 T08 focused、全量 pytest、compileall、diff check
- [x] 提交 `feat(matching): add public text vector candidates and safe projections` 并推送
