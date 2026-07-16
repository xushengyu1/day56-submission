# 决策：AI 失物招领系统技术方案选型

- **日期**：2026-07-16
- **状态**：✅ 已接受（用户已确认）
- **决策者**：项目团队
- **PRD 基线**：V0.6 + 用户确认的技术选型覆盖

---

## 背景

本项目为校园场景的 AI 失物招领匹配与认领复核 Web 系统，两天三人 MVP。PRD V0.6 已确认以下技术约束：

- **后端**：Python + FastAPI
- **数据库**：PostgreSQL + pgvector 扩展
- **AI 边界**：只用文本 AI，不训练模型，不做图像识别
- **数据分类**：PUBLIC / MATCH_ONLY / VERIFICATION / PRIVATE 四级

用户确认了以下技术选型，覆盖 PRD 中"待确认"的部分：

| 组件 | 用户确认选择 |
|---|---|
| 前端框架 | React 18 + Vite |
| Embedding 模型 | text-embedding-v4 |
| 核验 AI | mimoV2.5-pro |
| 匹配流程 | 双方向量化 → pgvector 相似度 → TOP-5 |
| 隐藏问题 | 拾得者上传隐藏特征 → LLM 自动生成问题 |

---

## 决策

**选择方案 A：向量匹配 + LLM 核验**

| 组件 | 选择 | 决策状态 |
|---|---|---|
| Web 框架 | FastAPI | ✅ PRD 已确认 |
| 前端 | React 18 + Vite | ✅ 用户确认 |
| 数据库 | PostgreSQL + pgvector | ✅ PRD 已确认 |
| ORM | SQLAlchemy + raw SQL for pgvector | ✅ 方案确认 |
| 认证 | JWT (access + refresh) | ✅ 方案确认 |
| Embedding | text-embedding-v4 | ✅ 用户确认 |
| 匹配引擎 | pgvector 余弦相似度 → TOP-5 | ✅ 用户确认 |
| 问题生成 | mimoV2.5-pro | ✅ 用户确认 |
| 回答核验 | mimoV2.5-pro | ✅ 用户确认 |

---

## 方案对比

### 三个方案的加权评分

| 方案 | 总分 | 核心优势 | 核心劣势 |
|---|---:|---|---|
| **A：向量匹配 + LLM 核验** | **4.15** | 语义匹配最强；LLM 自动生成问题；React 体验最佳 | 外部 API 依赖 |
| B：规则优先 + 最小 AI | 3.60 | 2 天可交付性最高 | 前端体验差；问题质量参差不齐 |
| C：LLM 驱动全流程 | 3.55 | 语义理解最深 | 2 天交付风险最高 |

详细评分见 `docs/options/tradeoff-matrix.md`。

---

## 后果

### 正面影响

1. **匹配质量最高**：text-embedding-v4 双方信息均向量化，语义召回能力强
2. **拾得者门槛最低**：只需上传隐藏特征，LLM 自动生成规范问题
3. **核验准确**：mimoV2.5-pro 能识别同义表达和模糊描述
4. **前端体验最佳**：React SPA 组件化交互
5. **架构清晰**：前后端分离，各层职责明确

### 负面影响 / 代价与风险

1. **外部 API 依赖**：text-embedding-v4 + mimoV2.5-pro 均需网络可达
2. **React 开发成本**：Vite + JWT + CORS 联调高于 SSR
3. **LLM 问题生成不稳定**：同一特征可能生成不同问题
4. **拾得者控制力降低**：问题由 LLM 生成而非手动编写

### 风险缓解措施

| 风险 | 缓解措施 |
|---|---|
| API 不可用 | 预置 fallback 结果 + 降级为关键词/规则匹配 |
| LLM 问题质量差 | 标准 prompt 模板 + 拾得者确认机制 |
| React 联调时间不足 | 核心页面优先；管理员页面可简化 |
| 阈值不合理 | 边界样例验证；答辩时说明 Demo 局限 |

---

## 与 PRD V0.6 的差异

| PRD 原设计 | 当前方案 | 差异原因 |
|---|---|---|
| 拾得者手动设置隐藏问题和标准答案（FR-21） | 拾得者只上传隐藏特征，LLM 自动生成问题 | 降低拾得者门槛 |
| AI 只引导和检查问题质量（FR-22） | AI 直接生成问题 | 简化流程 |
| 至少两组有效问答才可发布（FR-23） | 拾得者上传隐藏特征即可发布 | 简化发布 |
| 前端待确认 | React SPA | 用户确认 |
| Embedding 待确认 | text-embedding-v4 | 用户确认 |
| 核验 AI 待确认 | mimoV2.5-pro | 用户确认 |

---

## 关联文件

| 文件 | 路径 | 说明 |
|---|---|---|
| PRD 基线 | `xiaomi/2/day6/prd.md` | 需求基线 V0.6 |
| 问题诊断 | `docs/diagnosis/problem-diagnosis.md` | 问题全貌、核心冲突、约束条件 |
| 澄清问题 | `docs/diagnosis/clarifying-questions.md` | 澄清问题及回答 |
| 方案选项 | `docs/options/solution-options.md` | 3 个本质不同的方案详细描述 |
| 取舍矩阵 | `docs/options/tradeoff-matrix.md` | 多维度加权评分 |
| 拒绝方案 | `docs/options/rejected-options.md` | 被拒绝方案及原因 |
| 验证案例 | `docs/validation/cases-and-results.md` | 验证场景（待执行） |
| 最终建议 | `docs/decision/final-recommendation.md` | 最终选择与实施计划 |

---

## 决策链路状态

```text
问题诊断 ✅ → 澄清问题 ✅ → PRD Review ✅ → 方案对比 ✅
→ MVP 选择 ✅ → 验证计划 ✅ → 最终建议 ✅ → 本决策备忘 ✅
```
