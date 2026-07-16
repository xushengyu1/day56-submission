# T12 联系授权、交接与时间线设计

## 目标

完成待交接后的最小联系方式授权、拾得者确认线下交接和角色化审计时间线，形成发布到完成的闭环。

## 规则

- 联系方式：仅 claim requester 且 claim 为 `PENDING_HANDOFF` 时返回对应 FOUND owner 的最小联系字段；候选页和其他状态不渲染/不返回。
- 交接完成：仅 FOUND owner 可提交，必须 `confirmation=true` 和 `Idempotency-Key`；claim 从 PENDING_HANDOFF 到 CLAIMED，相关 LOST/FOUND 记录进入 CLAIMED。
- 决定、记录状态、幂等结果和 `HANDOFF_COMPLETED` audit 同事务提交；重复相同请求重放原结果。
- 时间线：record owner、相关 claim requester 或 ADMIN 可读；普通用户只看事件类型/时间/result code 和安全 metadata，移除 admin/private/internal 字段。
- 联系授权使用账号 email 作为 MVP 最小联系方式；不返回密码、token、phone_encrypted 原值或其它账号字段。

## 验证

- 联系访问：待交接 requester 成功，其它用户/状态拒绝。
- 交接：只有 finder 可确认；重复键不重复写事件；最终 claim/记录状态一致。
- 时间线：相关角色可读、无关用户拒绝、普通用户投影不含管理员内部字段。
- 完成后执行所有 task-backend 验收命令、全量 pytest、迁移往返、Docker health 和隐私扫描。
