# T08 失物发布与候选设计

## 目标

实现 LOST 记录发布、同类型 FOUND 候选生成、Top 5 快照和 PUBLIC DTO。候选接口不得返回 embedding、精确时间、标准化地点、隐藏答案、HMAC、PRIVATE object key 或联系方式。

## 流程

1. 创建 LOST：校验 item type、时间、地点、名称与公开描述，生成公开文本 embedding，直接进入 `PUBLISHED`。
2. SQL 硬过滤：只查询 `FOUND + PUBLISHED + 同 item_type`。
3. 服务计算 embedding 余弦相似度、时间差、地点关系和公开字段完整度，调用 T02 `score_candidate`。
4. 丢弃 `EXCLUDED`，按总分倒序/candidate id 稳定取 Top 5，写 `candidate_matches` 快照与 rule/model version。
5. 列表/详情只投影 FOUND 的 PUBLIC 字段、总分/分档、固定 reason/conflict codes；owner 检查失败返回统一错误。

## 取舍

- MVP 地点关系先使用确认后的 `location_public` 规范化字符串：完全相同为 `SAME_LOCATION`，否则为 `UNKNOWN`，不伪造地理距离。
- mock embedding 明确标记 `mock-hash-v1`；替换真实 embedding 时接口和维度校验不变。
- 候选重新计算先删除该 LOST 的未进入 claim 的旧快照；T09 开始后改为保留被 claim 引用的历史版本。

## 验证

- query：非 owner 不可读取，只返回本人的 Top 5。
- scoring：同类型/相反方向硬门槛，分项与总分持久化一致。
- privacy：DTO/JSON 扫描无 embedding、exact/normalized location、HMAC、答案键、object key、联系方式。
- 全量回归、compileall、diff check。
