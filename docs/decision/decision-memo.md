# 决策备忘

> 状态：技术方案尚未选择，本文件不能伪造最终结论。当前只记录已确认的方向性决策。

- 最终选择：待 `design_option.md` 比较与用户确认。
- 已确认的选择：聚焦“候选 + 冲突转人工 + 认领复核 + 追溯”的最小闭环。
- 选择原因：符合题面核心判断和两天提交重点；避免用功能数量替代验证证据。
- 已放弃的方案：九页面完整产品化 MVP、把复杂多申请并发作为 P0。
- 当前关键证据：`docs/diagnosis/problem-diagnosis.md`、`docs/prd.md`、`docs/ai/accepted-and-rejected-ai-advice.md`、第二次需求同步纪要。
- 最大风险：前端、PostgreSQL 数据访问、认证、embedding/AI 模型和团队分工未确认；虽然 Python + FastAPI + PostgreSQL + pgvector 已确定，仍不能证明完整向量与 AI 路线可交付。
- 失败场景：黑色折叠伞隐藏特征冲突、信息不足、AI 不可用、普通用户越权。
- 如果再给一天，优先验证什么：待 MVP 实测后根据最大残留风险填写。

## 决策链路

```text
问题诊断 -> 澄清问题 -> PRD Review -> 方案对比（未开始）
-> MVP 选择（未开始） -> 验证结果（未开始） -> 最终建议（未开始）
```
