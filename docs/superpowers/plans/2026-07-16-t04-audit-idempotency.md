# T04 审计与幂等实施计划

**Goal:** 完成脱敏审计事件、请求标识、结构化日志、稳定错误和数据库幂等结果。

## Task 1：脱敏与投影

- [ ] 写 `tests/unit/audit/test_redaction.py`、`test_projection.py` Red 测试
- [ ] 实现 schemas/projection/service
- [ ] 运行单元测试

## Task 2：core 基础设施

- [ ] 写 clock/ids/logging/errors/idempotency Red 测试
- [ ] 实现最小公共函数与错误映射
- [ ] 运行 focused tests

## Task 3：真实数据库幂等事务

- [ ] 写 `tests/integration/audit/test_audit_transaction.py`、`test_idempotency.py`
- [ ] 实现 append/store/query 的事务行为
- [ ] 运行 PostgreSQL 集成测试

## Task 4：回归、证据、提交

- [ ] 更新 `evidence/development-records/T04.md`
- [ ] 运行 T04 focused、全量 pytest、compileall、diff check
- [ ] 提交 `feat(audit): add redacted audit projection and idempotency` 并推送
