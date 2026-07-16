# T05 图片上传、私有存储与脱敏设计

## 目标

实现本地文件存储的最小安全闭环：校验 JPEG/PNG/WebP 的 MIME、魔数、大小和像素上限；PRIVATE 与 PUBLIC 目录隔离；生成随机对象键；身份证图片按确认区域绘制不可逆遮挡；记录关闭后可安全删除 PRIVATE 文件。

## 方案

- `images/schemas.py`：上传元数据、红action 区域和校验结果 DTO。
- `images/storage.py`：`StoragePort` 与本地实现，路径只由随机对象键生成，不把文件系统路径返回 API。
- `images/redaction.py`：Pillow 读取图片并对给定区域填充不透明黑色；区域越界/空区域拒绝；输出始终写入 PUBLIC 目录并返回新对象键。
- `images/service.py`：组合校验、存储和 `ImageAsset` 持久化；原图目的只能落 PRIVATE，PUBLIC_REDACTED 必须由确认后的脱敏结果创建。
- `api/routes/uploads.py`：USER 上传接口，先保存 PRIVATE asset，再由后续 T07 绑定记录；P0 不提供原图直出接口。

## 约束

- 允许 `image/jpeg`、`image/png`、`image/webp`，并用 Pillow `verify()` 与格式映射双重检查，不能只信客户端 MIME。
- 单文件默认最大 10 MiB，最大像素 20 MP；PNG/JPEG/WebP 魔数必须匹配。
- object key 形如 `private/<uuid>.<ext>` 或 `public/<uuid>.png`，禁止 `..`、绝对路径和用户输入文件名。
- 删除只接受受控 object key，使用 `Path.resolve()` 确认仍在对应根目录内。
- 脱敏副本只有 `CONFIRMED` 才能成为 PUBLIC；P0 允许失败后选择不公开图片，不返回 PRIVATE 路径。

## 验证

- 单元：MIME/魔数/大小/像素边界、路径穿越、目录隔离、随机键和区域遮挡像素。
- 集成：上传落盘与数据库 asset 同事务语义、PUBLIC 约束、关闭清理 PRIVATE 文件且不删除 PUBLIC 文件。
- 全量：T00–T04 回归、compileall、diff check。
