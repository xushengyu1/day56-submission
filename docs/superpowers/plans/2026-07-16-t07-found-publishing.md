# T07 招领发布实施计划

**Goal:** 完成 FOUND 草稿、AI 建议、人工确认、身份证/OTHER 专属门槛和原子发布。

## Task 1：草稿与版本确认

- [x] 写 `test_found_draft.py` Red 测试
- [x] 实现 schemas、owner/version 校验和草稿服务
- [x] 运行 focused test

## Task 2：身份证发布

- [x] 写 `test_found_identity_publish.py` Red 测试
- [x] 实现 HMAC/掩码、脱敏与发布策略
- [x] 运行 focused test

## Task 3：OTHER 发布

- [x] 写 `test_found_other_publish.py` Red 测试
- [x] 实现问题生成/确认与发布策略
- [x] 运行 focused test

## Task 4：路由、回归、证据

- [x] 实现 found_records 路由并注册
- [x] 更新 `evidence/development-records/T07.md`
- [x] 运行 focused、全量 pytest、compileall、diff check
- [x] 提交 `feat(found): add human confirmed multimodal publishing workflows` 并推送
