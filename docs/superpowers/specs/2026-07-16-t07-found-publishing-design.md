# T07 招领草稿与人工确认发布设计

## 目标

实现 FOUND 记录从草稿、AI 建议、人工确认、类型专属核验信息到原子发布的闭环。AI 输出永远是可编辑草稿；任一发布门槛失败时记录保持 `DRAFT`。

## 服务流程

1. 创建草稿：校验 PRIVATE `FINDER_ORIGINAL` asset 属于当前用户，写 FOUND/DRAFT 的时间地点与图片关联。
2. 提取建议：在事务外调用 T06 端口，再保存 `AIExtraction` 与模型版本；失败只记录失败状态，不丢草稿。
3. 人工确认：按 `expected_version` 更新 `item_type/name_public/description_public/time/location`，版本加一。
4. 身份证分支：要求逐位确认；规范化、校验、HMAC-SHA256、前 3 后 4 掩码，数据库不保存明文。
5. OTHER 分支：隐藏描述非空；T06 生成的问题必须通过 T02 校验；拾得者确认后保存答案键和模型版本。
6. 脱敏：复用 T05 从 PRIVATE 原图生成 `PUBLIC_REDACTED + CONFIRMED`；API 不返回 PRIVATE 路径。
7. 发布：统一策略检查公共字段、原图、类型专属数据与版本；生成公开文本 embedding，更新 `PUBLISHED/published_at` 并追加审计事件。

## 锁定边界

- `IdentityDocumentPolicy` 与 `OtherItemPolicy` 只判断门槛，不访问 HTTP。
- 服务函数接收 `AsyncSession` 与 actor ID；所有 owner/版本检查在服务端执行。
- 完整身份证仅存在于函数栈，HMAC key 来自 `ID_HMAC_KEY_V1`；异常和审计只记录 `ID_INVALID` 等代码。
- 问题文本可在后续认领 API 返回，答案键仅在 VERIFICATION 表和管理员用途 DTO 使用。

## 验证

- 草稿：非 owner、图片不属于 actor、版本冲突和 AI 失败。
- 身份证：有效号码 + 脱敏确认可发布；无 HMAC/未确认脱敏不能发布；数据库/响应/审计无明文号码。
- OTHER：隐藏描述 + 2～3 个有效已确认问题可发布；问题泄漏/维度重复/未确认不能发布。
- 全量回归与 compileall/diff check。
