# T04 审计与幂等设计

## 目标

补齐所有业务模块共用的审计、请求标识、错误映射和幂等基础设施。审计事件只追加不更新/删除；普通日志与审计 metadata 均不能包含完整身份证、隐藏答案、密码、token、联系方式或私有文件路径。

## 模块边界

- `audit/schemas.py`：审计事件输入和脱敏投影 DTO。
- `audit/projection.py`：递归按字段名和值模式脱敏，输出 JSON-safe 的最小事件视图。
- `audit/service.py`：在调用方事务中追加 `AuditEvent`；不自行提交，保证业务状态与事件同事务。
- `core/clock.py`：可注入的 UTC 时钟函数，测试不依赖系统时间。
- `core/ids.py`：请求 ID 和幂等键的 UUID 格式生成/校验。
- `core/logging.py`：结构化 logger adapter，只写脱敏字段。
- `core/idempotency.py`：请求哈希、同主体同键查询、结果保存；同键不同 hash 返回稳定冲突错误。
- `api/errors.py`：稳定 `APIError` 与 FastAPI 异常响应映射。

## 关键决策

1. 脱敏采用“键名优先、值模式兜底”：键名命中 password/token/secret/answer/phone/identity 等字段时统一替换 `[REDACTED]`；字符串中的身份证格式、JWT 三段 token 和私有路径也替换。未知结构递归处理，避免只过滤第一层。
2. `append_audit_event` 只 `session.add` 并返回实体，不 commit；由业务事务统一提交，失败时事件和业务状态一起回滚。
3. 幂等结果保存完整响应 JSON（已脱敏）与请求哈希。重复请求返回原状态/响应；同 actor 同 key 不同请求哈希返回 `IDEMPOTENCY_KEY_REUSED`。
4. 不做全局中间件猜测请求体，幂等由需要的业务 endpoint 显式调用；避免读取上传流或敏感请求体造成副作用。

## 锁定接口

```python
redact_metadata(value: object) -> object
append_audit_event(session, event: AuditEventInput) -> AuditEvent
hash_request(value: object) -> str
get_idempotent_result(session, actor_id, key, request_hash) -> IdempotentResponse | None
store_idempotent_result(session, actor_id, key, request_hash, status, body) -> IdempotencyResult
```

## 验证

- 单元：递归脱敏、投影字段、稳定 request/hash/id、错误映射和同键冲突。
- 集成：审计与业务事务同提交/同回滚；同主体同键重复返回原响应；不同主体可复用相同键；同主体不同请求被拒绝。
- 全量：T00–T03 回归、compileall、diff check，并扫描测试输出不得出现敏感值。
