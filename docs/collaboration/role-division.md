# 团队分工

## 团队信息

- 团队名称：待团队确认
- 项目名称：AI 失物招领匹配与认领复核系统
- 成员：待用户提供；当前不虚构成员姓名或个人贡献。

## 角色分工

| 成员 | 角色 | 负责模块 | 今日交付物 | 证据位置 |
|---|---|---|---|---|
| 待确认 | Product Owner | 问题诊断、澄清、方案取舍 | 待分配 | `docs/diagnosis/`、`docs/options/` |
| 待确认 | UX / Client Owner | Web 前端主路径和状态 | 待分配 | `src/`、`prototype/` |
| 待确认 | Backend / Tech Lead | 服务端、规则、数据与接口 | 待分配 | `src/`、`docs/design/` |
| 待确认 | AI Workflow Owner | AI 输入输出边界与协作日志 | 待分配 | `docs/ai/` |
| 待确认 | QA / Delivery Owner | TDD、E2E、边界、证据和提交 | 待分配 | `docs/validation/`、`docs/defense/` |

角色可以合并，但职责不能消失。成员确认后必须把“待确认”替换为真实姓名，并由各成员复核自己的证据。

## 端到端责任映射

| 模块 | 负责人 | 备份人 | 验收证据 |
|---|---|---|---|
| 问题诊断、澄清、方案对比 | 待确认 | 待确认 | 对应 docs + 会议/决策记录 |
| Web 前端与管理员角色视图 | 待确认 | 待确认 | 代码、E2E、截图 |
| 服务端/规则/数据流 | 待确认 | 待确认 | 代码、单元/集成测试 |
| AI 协作日志 | 待确认 | 待确认 | 至少五类真实日志、两条拒绝/修改 |
| 测试、Review 与提交包 | 待确认 | 待确认 | 测试结果、Review、README |

## 工作规则

1. 每次真实会议/同步必须有纪要。
2. 每个任务必须有真实负责人。
3. 每个负责人必须留下代码、文档、测试或 Review 证据。
4. AI 关键建议必须记录采纳、修改或拒绝原因。
5. 不提前填写尚未执行的测试结果、提交记录或个人贡献。

## 个人贡献证据要求

每个人至少留下三类证据：文件/模块负责人记录、会议行动项或决策、AI/测试/Review/提交记录中的至少一类。

## 追加确认：当前已知成员贡献映射

> 确认日期：2026-07-16。本节只记录已经由宋子仪确认的真实贡献，不推断其他尚未说明的团队职责；上方“待确认”模板作为历史记录保留。

| 成员 | 已确认贡献 | 证据位置 |
|---|---|---|
| 宋姿毅（SZY） | 角色功能与身份证件分流；其余产品/架构决策主导；PRD、方案、详细设计、dev 与过程文档记录；UI 设计和 React 前端独立实现 | `docs/reflection/szy-personal-contribution.md`、`szy-ai-log.md`、`prototype/ui/`、`frontend/`、`evidence/development-records/T13.md`～`T16.md` |
| 徐胜宇 | 提出四级数据分类；与宋姿毅共同执行和决定图片识别方案 | `docs/collaboration/decision-log.md` 的 `D-ATTR-001`、`docs/reflection/szy-personal-contribution.md` |
| 黄孝梁 | 提出图片识别/多模态提取想法 | `docs/collaboration/decision-log.md` 的 `D-ATTR-001`、`docs/reflection/szy-personal-contribution.md` |

该表仅用于贡献归属，不等同于完整任务分工表；其他成员的代码、测试和交付职责仍需各成员以真实证据补充。
