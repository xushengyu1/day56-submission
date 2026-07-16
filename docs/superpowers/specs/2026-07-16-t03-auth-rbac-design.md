# T03 认证与 RBAC 设计

## 目标

在现有 FastAPI/T01 数据模型上建立最小可用的注册、登录、refresh 和权限依赖。密码只保存 Argon2 哈希，refresh token 只保存不可逆摘要；普通注册始终创建 `USER`，管理员不通过公开接口产生。

## 方案

- `auth/schemas.py`：Pydantic 请求/响应 DTO，统一校验邮箱、密码和 refresh token 输入。
- `auth/security.py`：`pwdlib` 的 Argon2 哈希、PyJWT HS256 签发/解析、refresh token 随机生成与 SHA-256 摘要；JWT payload 只放 `sub`、`role`、`type`、`iat`、`exp`、`jti`。
- `auth/service.py`：异步事务服务。注册先规范化 email 并检查唯一性；登录使用常量时间的密码校验路径；refresh 校验 JWT 后用摘要查询未撤销且未过期的数据库记录，并轮换旧 token。
- `auth/rbac.py`：集中提供 `require_role`、`ensure_owner` 和 `ensure_owner_or_admin`，不把 `ADMIN` 角色等价为可以读取所有 PRIVATE 数据。
- `api/deps.py`：Bearer access token 解析和当前用户依赖；refresh 只允许 auth 路由显式调用，不混入普通业务依赖。
- `api/routes/auth.py`：`POST /api/auth/register`、`/login`、`/refresh`，统一返回 access token、refresh token 和用户公开信息。

## 关键决策与取舍

1. 采用 HS256 而非引入 RSA/JWK：单体 MVP 只有一个签发服务，减少密钥管理代码；通过环境变量 `JWT_SECRET` 注入，生产不得使用默认值。
2. refresh token 使用 JWT 外壳加数据库摘要：JWT 提供用户和过期信息，数据库撤销记录提供服务端可控失效；每次 refresh 轮换旧记录，降低重放窗口。
3. email 规范化只做 NFKC、去两端空白和 casefold；不改变用户联系方式原文。数据库唯一约束仍是最终并发保障。
4. 认证失败统一返回 `INVALID_CREDENTIALS`，不区分用户不存在、密码错误、token 不存在或已撤销，避免账号枚举。

## 锁定接口

```python
hash_password(password: str) -> str
verify_password(password: str, password_hash: str) -> bool
create_access_token(user_id: UUID, role: UserRole, now: datetime | None = None) -> str
decode_access_token(token: str, now: datetime | None = None) -> TokenClaims
create_refresh_token(user_id: UUID, role: UserRole, now: datetime | None = None) -> tuple[str, TokenClaims]
hash_refresh_token(token: str) -> str
```

服务层使用异步 `AsyncSession`；路由通过依赖注入 session。所有异常对外暴露稳定错误码，不返回密码哈希、完整 token 或数据库异常文本。

## 验证范围

- 单元：密码哈希不可逆且错误密码失败；access/refresh 的 type、过期、签名、subject 和 role 校验；refresh 摘要不可逆；RBAC 角色和资源归属边界。
- 集成：注册成功/重复邮箱、登录成功/错误凭据、refresh 轮换/撤销；路由返回状态码和不泄漏敏感字段。
- 全量：保留 T00–T02 回归，运行 compileall 与 `git diff --check`。
