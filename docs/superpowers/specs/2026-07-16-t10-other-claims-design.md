# T10 OTHER 开放问题认领设计

## 目标

实现 OTHER 候选的问题安全读取、回答核验和保守路由。问题文本可返回候选对应失主；答案键、隐藏描述和原始回答不进入普通响应或日志。

## 流程

1. `GET questions` 校验 candidate、LOST owner 和 OTHER 类型，查询已确认 VerificationSet，仅返回 question id/text/dimension。
2. `POST answers` 对 candidate 行加锁，校验回答覆盖所有 question id，创建 `SUBMITTED → VERIFYING` claim。
3. 在模型调用前构造内部 QuestionSetDraft；调用 T06 verification port，不把答案键返回路由。
4. `MATCH + confidence >= 0.8 + 无其他活动 claim`：claim 与 LOST/FOUND 进入 `PENDING_HANDOFF`。
5. `PARTIAL_MATCH/UNDETERMINED/CONFLICT`、低置信、多人认领、模型异常：进入 `PENDING_ADMIN_REVIEW`。
6. ClaimAttempt 只保存 question result/confidence/reason code 摘要，不保存原始答案文本；审计记录固定路由码。

## 验证

- questions API 投影不含 `answer_key/hidden_description`。
- 全匹配唯一认领进入待交接；部分/冲突转管理员。
- adapter 抛异常或非法结果时仍创建可追踪 claim 并转管理员，不自动通过。
- 全量回归、compileall、diff check。
