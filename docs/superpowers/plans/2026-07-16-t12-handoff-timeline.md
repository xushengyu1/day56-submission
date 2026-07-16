# T12 交接与时间线实施计划

**Goal:** 完成联系方式授权、幂等交接确认、角色时间线和后端总验收。

## Task 1：联系方式

- [x] 写 `test_contact_access.py` Red 测试
- [x] 实现 handoff contact service/route
- [x] 运行 focused test

## Task 2：交接完成

- [x] 写 `test_handoff_complete.py` Red 测试
- [x] 实现 finder owner、状态机、幂等、审计事务
- [x] 运行 focused test

## Task 3：时间线

- [x] 写 `test_timeline_projection.py` Red 测试
- [x] 完善 audit projection 和 records route
- [x] 运行 focused test

## Task 4：总验收与交付

- [x] 更新 `evidence/development-records/T12.md` 和后端汇总
- [x] 运行 T12 focused、全量 pytest、迁移往返/check、Docker health、compileall、diff/privacy scan
- [x] 提交 `feat(handoff): close claims with scoped contact and audit timelines` 并推送
