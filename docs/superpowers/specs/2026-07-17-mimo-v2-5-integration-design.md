# MiMo V2.5 真实模型接入设计

## 目标

将现有只走 mock 的图片提取、核验问题生成、认领答案核验三项能力真实接入小米 `mimo-v2.5`。生产模式使用 OpenAI 兼容 API，开发与自动化测试继续使用确定性 mock。API Key 只从运行环境读取，不进入 Git、日志、错误响应或测试数据。

小米官方将 `mimo-v2.5` 定义为支持图像、视频、音频和文本的全模态模型，并提供 OpenAI 兼容 API。本次接入使用用户指定的 `https://api.xiaomimimo.com/v1` 与 Chat Completions 协议。

## 范围

- 使用 `AsyncOpenAI` 实现真实 MiMo adapter。
- 将多模态端口及三条业务调用链改为异步，避免阻塞 FastAPI 事件循环。
- 根据 `AI_MODE` 选择 mock 或真实 adapter，替换路由中硬编码的 mock。
- 从本地私有存储读取图片，按 MIME 类型转换为 Base64 Data URL 后发送给 MiMo。
- 为提取、出题、核验定义独立提示词，并把响应转换为现有领域 DTO。
- 更新依赖、环境变量示例、单元测试、集成测试和真实 API smoke test。

不在本次范围内：公开或签名图片 URL、视频和音频接入、流式响应、联网搜索、工具调用、任务队列、供应商自动切换。

## 方案选择

### 方案一：继续使用同步 `httpx`

只把现有自定义 `operation/input` 请求改成标准 OpenAI 消息体，改动最少。但当前业务服务和路由均为异步，同步网络请求会阻塞事件循环，因此不采用。

### 方案二：使用 `AsyncOpenAI`（采用）

使用 OpenAI Python SDK 的异步客户端，端口、mock 和业务调用统一改为 `async`。该方案符合当前 FastAPI 架构，并直接使用用户提供的兼容调用方式。

### 方案三：引入任务队列

模型请求放入后台任务，适合长时间、可异步回收结果的工作流，但会改变当前同步 API 语义并增加基础设施，超出本次需求，因此不采用。

## 配置与 adapter 选择

配置调整为：

- `AI_MODE`：保留 `mock` 与 `real`，默认 `mock`。
- `MIMO_BASE_URL`：默认 `https://api.xiaomimimo.com/v1`。
- `MIMO_API_KEY`：默认空值，仅在 `real` 模式从环境变量读取。
- `MIMO_MULTIMODAL_MODEL`：默认 `mimo-v2.5`。
- `MIMO_TEXT_MODEL`：默认 `mimo-v2.5`；三项能力使用同一个已确认模型。
- `MODEL_TIMEOUT_SECONDS`：保留现有超时配置。

新增最小 adapter 工厂：`mock` 返回 `MockMultimodalAdapter`；`real` 返回 `OpenAICompatibleAdapter`。真实模式缺少 Key 时快速失败，错误中不包含环境变量值。路由通过同一依赖获取 adapter，不再各自创建硬编码 mock。

`.env.example` 只记录变量名和非敏感默认值，`MIMO_API_KEY` 保持为空。用户提供的 Key 已出现在对话中，交付时明确提醒轮换。

## 异步端口

`MultimodalPort` 保留现有三个方法和领域 DTO，但方法改为异步：

- `extract_found_item(image_data_url, context)`
- `generate_questions(hidden_description)`
- `verify_answers(question_set, answers)`

业务服务统一 `await` 端口调用。mock 同样声明为异步，以保证测试和真实模式遵守同一契约。除必要的调用方式变化外，不修改现有领域规则。

## 图片数据流

图片提取链路为：

1. 路由校验图片确属当前失物记录与当前用户。
2. 使用 `LocalStorage` 按受控 `object_key` 读取私有图片字节。
3. 根据已允许的 `jpg/jpeg/png/webp` 后缀确定 MIME 类型。
4. 生成 `data:<mime>;base64,<payload>`，作为 OpenAI 消息中的 `image_url.url`。
5. 同一用户消息中同时发送图片和提取指令。
6. 请求结束后不持久化 Data URL，也不把它写入日志、异常或审计元数据。

本次不生成外部可访问链接，因此不会扩大私有图片的公开范围。无效 object key、文件不存在或 MIME 类型不支持时，不调用 MiMo，并返回稳定业务错误。

## 三类请求与响应

### 失物图片提取

请求包含固定 system 指令、Base64 图片和必要的记录上下文。模型被要求只返回 JSON object，字段保持现有契约：

- `item_type`
- `name_public`
- `description_public`
- `confidence`

提示词要求公开描述避免主动输出证件完整号码等敏感细节。响应经本地枚举、Pydantic schema 和置信度范围校验后，才生成 `ExtractionDraft`。数据库中的 `raw_result_redacted` 只记录结构校验成功等非敏感元数据，不保存模型原文。

### 核验问题生成

请求只发送已由失主确认的隐藏描述。模型返回 `questions`，每题包含：

- `question_text`
- `answer_key`
- `dimension`
- `is_open_ended`

结果继续通过现有 `validate_question_set` 校验；题目数量、开放题要求或维度不符合规则时整体失败，不落入半成品问题集。参考答案只保存在私有服务端数据中，不通过公开问题接口返回。

### 认领答案核验

请求发送已确认问题、服务端参考答案和认领人提交的答案。参考答案只进入本次 MiMo 请求，不返回客户端。模型返回：

- `result`
- `confidence`
- `reason_code`

结果经领域 schema 校验；`MATCH` 置信度低于现有阈值 `0.8` 时仍降级为 `UNDETERMINED`，不自动放行。

## 响应解析与失败策略

不假定供应商一定支持额外的结构化输出扩展。提示词要求纯 JSON，本地解析同时容忍常见 Markdown JSON 代码围栏，但最终只接受单个 JSON object，并严格校验领域字段。

SDK 超时、连接失败、限流和服务端错误映射为 `MODEL_UNAVAILABLE`；鉴权或其他非重试 HTTP 错误映射为稳定的模型 HTTP 错误；空响应、非 JSON 或 schema 不合法映射为 `MODEL_RESPONSE_INVALID`。业务层继续转换为现有领域错误和 HTTP 响应，不暴露 Key、Data URL、隐藏描述、参考答案或供应商原始响应。

客户端设置固定超时和最多一次重试。三类调用使用 `max_completion_tokens=1024`，暂不增加未要求的动态参数。

## 测试策略

严格执行 Red → Green：

1. adapter 请求测试：确认 URL、模型名、异步调用和标准 OpenAI messages 结构。
2. 图片测试：确认私有图片生成正确 MIME Data URL，且 Data URL 不进入持久化结果或异常。
3. 响应测试：三类合法 JSON 均转换为现有 DTO；JSON 围栏可解析。
4. 失败测试：超时、429、5xx、鉴权失败、空响应、非法 JSON、非法枚举和非法置信度均映射为稳定错误。
5. 工厂测试：`mock` 无需 Key，`real` 缺少 Key 快速失败，真实配置选择 `mimo-v2.5`。
6. 服务与路由测试：三条调用链均 `await` adapter，`AI_MODE=real` 不再落到 mock，模型失败不产生半成品数据。
7. 聚焦测试通过后运行全量 pytest、Ruff、Mypy、compileall 与 `git diff --check`。

自动化测试使用 fake client，不访问外网、不消耗额度。最后使用隐藏终端输入 Key，分别执行一次最小文本调用和一次图片调用；只输出请求成功状态、实际模型名和结构校验结果，不输出 Key、图片 Data URL、完整模型响应或业务隐私数据。

## 验收标准

- `AI_MODE=real` 时三项能力均调用 `https://api.xiaomimimo.com/v1` 的 `mimo-v2.5`，不再使用 mock。
- 私有图片仅在请求期间转换为 Base64 Data URL，不公开、不落库、不记日志。
- 异步模型请求不阻塞 FastAPI 事件循环。
- 三类响应全部经过严格领域校验，低置信或非法响应不会自动通过核验。
- 缺失 Key、接口失败和响应异常均返回稳定错误，且无敏感信息泄漏。
- `AI_MODE=mock` 仍能离线、确定地运行自动化测试。
- 全量测试与静态检查通过，真实文本与图片 smoke test 均成功。
