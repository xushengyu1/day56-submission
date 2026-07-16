# T05 图片服务实施计划

**Goal:** 完成安全图片校验、本地 PRIVATE/PUBLIC 存储、不可逆区域脱敏和清理。

## Task 1：校验与存储

- [x] 写 `tests/unit/images/test_validation.py` Red 测试
- [x] 实现 schemas/storage/service 的最小校验与随机键
- [x] 运行单元测试

## Task 2：脱敏

- [x] 写 `tests/unit/images/test_redaction.py` Red 测试
- [x] 实现 Pillow 区域遮挡和确认状态
- [x] 运行单元测试

## Task 3：数据库与清理

- [x] 写 `tests/integration/images/test_storage_access.py`、`test_cleanup.py`
- [x] 实现 asset 持久化、PRIVATE 删除和 PUBLIC 保护
- [x] 运行真实 PostgreSQL 集成测试

## Task 4：回归、证据、提交

- [x] 更新 `evidence/development-records/T05.md`
- [x] 运行 T05 focused、全量 pytest、compileall、diff check
- [x] 提交 `feat(images): isolate private assets and create confirmed redactions` 并推送
