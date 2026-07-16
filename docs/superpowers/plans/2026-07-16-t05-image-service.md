# T05 图片服务实施计划

**Goal:** 完成安全图片校验、本地 PRIVATE/PUBLIC 存储、不可逆区域脱敏和清理。

## Task 1：校验与存储

- [ ] 写 `tests/unit/images/test_validation.py` Red 测试
- [ ] 实现 schemas/storage/service 的最小校验与随机键
- [ ] 运行单元测试

## Task 2：脱敏

- [ ] 写 `tests/unit/images/test_redaction.py` Red 测试
- [ ] 实现 Pillow 区域遮挡和确认状态
- [ ] 运行单元测试

## Task 3：数据库与清理

- [ ] 写 `tests/integration/images/test_storage_access.py`、`test_cleanup.py`
- [ ] 实现 asset 持久化、PRIVATE 删除和 PUBLIC 保护
- [ ] 运行真实 PostgreSQL 集成测试

## Task 4：回归、证据、提交

- [ ] 更新 `evidence/development-records/T05.md`
- [ ] 运行 T05 focused、全量 pytest、compileall、diff check
- [ ] 提交 `feat(images): isolate private assets and create confirmed redactions` 并推送
