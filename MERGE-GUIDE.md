# 合并指南

> 本文档说明如何将后端（成员A）和前端（成员B）的代码合并为完整系统

---

## 开发阶段

### 分支策略

```
main
├── feature/backend    # 成员A：后端开发
└── feature/frontend   # 成员B：前端开发
```

### 各自开发

**成员A（后端）：**
```bash
git checkout -b feature/backend
# 开发 T00-T12
# 定期提交：git commit -m "feat(xxx): ..."
```

**成员B（前端）：**
```bash
git checkout -b feature/frontend
# 开发 T13-T19
# 定期提交：git commit -m "feat(xxx): ..."
```

### 同步策略

每天至少同步一次，避免冲突积累：

```bash
# 成员A
git fetch origin
git merge origin/main --no-edit
git push origin feature/backend

# 成员B
git fetch origin
git merge origin/main --no-edit
git push origin feature/frontend
```

---

## 合并阶段

### 步骤1：准备合并

```bash
# 确保main分支是最新的
git checkout main
git pull origin main

# 创建合并分支
git checkout -b merge/integration
```

### 步骤2：合并后端

```bash
# 合并后端分支
git merge feature/backend --no-edit

# 如果有冲突，解决后：
git add .
git commit -m "merge: integrate backend features"
```

### 步骤3：合并前端

```bash
# 合并前端分支
git merge feature/frontend --no-edit

# 如果有冲突，解决后：
git add .
git commit -m "merge: integrate frontend features"
```

### 步骤4：解决常见冲突

#### docker-compose.yml

```yaml
# 合并后的完整配置
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: lostfound
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/lostfound
      AI_MODE: ${AI_MODE:-mock}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - ai-mock

  frontend:
    build: ./frontend
    environment:
      VITE_API_BASE_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend

  ai-mock:
    build: ./ai-mock
    ports:
      - "8001:8000"

volumes:
  postgres_data:
```

#### .env.example

```bash
# 合并后的环境变量
POSTGRES_PASSWORD=your_password_here
AI_MODE=mock  # 或 real
VITE_API_BASE_URL=http://localhost:8000
```

### 步骤5：验证合并

```bash
# 构建所有服务
docker compose build

# 启动数据库
docker compose up -d postgres

# 运行数据库迁移
docker compose run --rm backend alembic upgrade head

# 启动所有服务
docker compose up -d

# 验证后端API
curl http://localhost:8000/api/health/live
# 预期：{"status":"ok"}

# 验证前端
open http://localhost:3000
# 预期：看到登录页面

# 运行所有测试
docker compose exec backend pytest -q
docker compose exec frontend npm run test -- --run
npx playwright test --config e2e/playwright.config.ts
```

---

## 数据库处理

### 迁移脚本

所有数据库迁移脚本由成员A在 `backend/alembic/versions/` 目录下管理。

**合并后只需运行：**
```bash
docker compose run --rm backend alembic upgrade head
```

### 初始数据

成员B的seed脚本 `backend/app/db/seed_demo.py` 需要与成员A协商接口。

**运行seed：**
```bash
docker compose exec backend python -m app.db.seed_demo --reset
```

### 数据库结构

```
PostgreSQL 16 + pgvector
├── users              # 用户表
├── item_records       # 失物/招领记录
├── found_records      # 招领记录详情
├── lost_records       # 失物记录详情
├── candidates         # 候选匹配
├── claims             # 认领申请
├── verification_*     # 核验相关表
├── reviews            # 复核申请
├── review_decisions   # 复核决定
├── audit_events       # 审计日志
└── assets             # 图片资源
```

---

## API对接

### 前端API客户端

成员B在 `frontend/src/api/client.ts` 中配置：

```typescript
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器：添加token
apiClient.interceptors.request.use((config) => {
  const token = getAccessToken(); // 从内存获取
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### 类型定义

成员B使用OpenAPI生成类型：

```bash
# 从后端API生成TypeScript类型
npx openapi-typescript http://localhost:8000/openapi.json -o src/api/types.ts
```

### API文档

后端API文档地址：
- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

---

## 测试策略

### 单元测试

**后端：**
```bash
docker compose exec backend pytest tests/unit -q
```

**前端：**
```bash
docker compose exec frontend npm run test -- --run
```

### 集成测试

```bash
docker compose exec backend pytest tests/integration -q
```

### E2E测试

```bash
# 确保所有服务运行
docker compose up -d

# 运行Playwright测试
npx playwright test --config e2e/playwright.config.ts

# 查看测试报告
npx playwright show-report
```

---

## 部署验证

### 完整验证流程

```bash
# 1. 清理环境
docker compose down -v

# 2. 重新构建
docker compose build

# 3. 启动服务
docker compose up -d

# 4. 等待服务就绪
sleep 10

# 5. 运行迁移
docker compose exec backend alembic upgrade head

# 6. 初始化数据
docker compose exec backend python -m app.db.seed_demo --reset

# 7. 运行所有测试
docker compose exec backend pytest -q
docker compose exec frontend npm run test -- --run
npx playwright test --config e2e/playwright.config.ts

# 8. 验证服务
curl http://localhost:8000/api/health/live
open http://localhost:3000
```

### 验证清单

- [ ] 后端API正常响应
- [ ] 前端页面正常加载
- [ ] 用户注册/登录正常
- [ ] 拾得者发布招领正常
- [ ] 失主发布失物正常
- [ ] 候选匹配正常
- [ ] 身份证认领正常
- [ ] OTHER认领正常
- [ ] 管理员复核正常
- [ ] 交接流程正常
- [ ] 所有测试通过

---

## 常见问题

### Q1: 端口冲突

**问题：** 端口已被占用

**解决：**
```bash
# 查看占用端口的进程
lsof -i :8000
lsof -i :3000
lsof -i :5432

# 修改docker-compose.yml中的端口映射
ports:
  - "8001:8000"  # 改为其他端口
```

### Q2: 数据库连接失败

**问题：** 无法连接PostgreSQL

**解决：**
```bash
# 检查PostgreSQL是否运行
docker compose ps postgres

# 查看日志
docker compose logs postgres

# 重启PostgreSQL
docker compose restart postgres
```

### Q3: 前端无法访问后端API

**问题：** CORS错误或网络不通

**解决：**
```bash
# 检查后端CORS配置
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 检查前端API地址
echo $VITE_API_BASE_URL
```

### Q4: 测试失败

**问题：** 测试环境不一致

**解决：**
```bash
# 清理测试数据库
docker compose down -v
docker compose up -d postgres
docker compose exec backend alembic upgrade head

# 重新运行测试
docker compose exec backend pytest -q
docker compose exec frontend npm run test -- --run
```

---

## 沟通协调

### 每日同步

- **时间**：每天晚上9点
- **内容**：
  - 完成的任务
  - 遇到的问题
  - 明天的计划
  - 需要协调的接口

### 接口协商

如果需要修改API接口：

1. **后端修改**：在task-backend.md中记录
2. **前端适配**：在task-frontend.md中记录
3. **同步通知**：及时告知对方

### 代码审查

合并前互相审查：

```bash
# 成员A审查前端
git diff feature/backend..feature/frontend -- frontend/

# 成员B审查后端
git diff feature/frontend..feature/backend -- backend/
```

---

## 最终交付

### 交付物清单

- [ ] 完整代码（main分支）
- [ ] 数据库迁移脚本
- [ ] 测试全部通过
- [ ] README.md
- [ ] 演示脚本
- [ ] 答辩准备

### 演示流程

1. **启动系统**（2分钟）
2. **拾得者发布**（2分钟）
3. **失主认领**（2分钟）
4. **管理员复核**（2分钟）
5. **交接完成**（1分钟）
6. **Q&A**（1分钟）

---

> **注意：** 合并过程中遇到问题，及时沟通解决。不要各自为战，确保最终系统完整可用。
