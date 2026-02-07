# FeishuMind 快速参考手册

**版本**: v1.0.0
**更新日期**: 2026-02-06

---

## 🚀 快速启动

### 1 分钟启动

```bash
# Docker 方式 (推荐)
docker-compose up -d

# 访问健康检查
curl http://localhost:8000/health
```

### 5 分钟本地开发

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境
cp .env.example .env
# 编辑 .env 文件，至少配置 MEM0_API_KEY

# 4. 启动服务
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 5. 访问文档
open http://localhost:8000/docs
```

---

## 📡 核心 API

### 健康检查

```bash
GET /health
```

**响应**:
```json
{
  "status": "healthy",
  "service": "FeishuMind",
  "version": "1.0.0"
}
```

### Agent 对话

```bash
POST /api/v1/agent/chat
```

**请求**:
```json
{
  "message": "提醒我明天下午3点开会",
  "context": {
    "user_id": "user_123",
    "session_id": "session_456"
  }
}
```

**响应**:
```json
{
  "response": "好的，我已经为您创建了明天下午3点的会议提醒",
  "tools_used": ["event_reminder"],
  "memory_updated": true,
  "requires_review": false
}
```

### 记忆管理

**添加记忆**:
```bash
POST /api/v1/memory
{
  "user_id": "user_123",
  "content": "用户偏好 Python 和 Go 语言",
  "memory_type": "preference"
}
```

**搜索记忆**:
```bash
GET /api/v1/memory/search?user_id=user_123&query=编程语言
```

### 飞书 Webhook

```bash
POST /api/v1/webhook/feishu
```

自动处理飞书消息，无需手动调用。

### GitHub 功能

**设置偏好**:
```bash
POST /api/v1/github/preferences
{
  "user_id": "user_123",
  "languages": ["Python", "Go"],
  "min_stars": 500,
  "time_range": "daily"
}
```

**获取热门**:
```bash
GET /api/v1/github/trending?user_id=user_123
```

### 日历管理

**创建事件 (自然语言)**:
```bash
POST /api/v1/calendar/events
{
  "user_id": "user_123",
  "natural_text": "明天下午3点开会讨论项目"
}
```

**创建事件 (结构化)**:
```bash
POST /api/v1/calendar/events
{
  "user_id": "user_123",
  "title": "团队会议",
  "start_time": "2026-02-10T15:00:00",
  "duration_minutes": 60,
  "reminders": [15, 60, 1440]
}
```

### 韧性辅导

**分析情绪**:
```bash
POST /api/v1/resilience/analyze
{
  "user_id": "user_123",
  "text": "最近项目压力很大，经常加班到深夜"
}
```

**响应**:
```json
{
  "sentiment": "negative",
  "stress_level": 0.8,
  "keywords": ["压力", "加班"],
  "suggestions": [
    "建议与团队沟通 workload 分配",
    "可尝试番茄工作法提高效率",
    "关注休息，避免过度疲劳"
  ]
}
```

---

## 🔧 环境变量

### 必需变量

```bash
# Mem0 API Key (必需)
export MEM0_API_KEY="mem0_xxxxx"

# OpenAI API Key (必需)
export OPENAI_API_KEY="sk-xxxxx"

# JWT Secret (必需)
export JWT_SECRET="your_secret_key_here"
```

### 可选变量 (飞书集成)

```bash
# 飞书应用配置
export FEISHU_APP_ID="cli_xxxxx"
export FEISHU_APP_SECRET="xxxxx"
export FEISHU_ENCRYPT_KEY="xxxxx"
export FEISHU_VERIFICATION_TOKEN="xxxxx"
```

### 可选变量 (其他)

```bash
# GitHub Token (用于 GitHub Trending)
export GITHUB_TOKEN="ghp_xxxxx"

# 数据库配置
export DATABASE_URL="postgresql://user:pass@localhost:5432/feishumind"

# Redis 配置
export REDIS_URL="redis://localhost:6379"

# 日志级别
export LOG_LEVEL="INFO"

# 运行环境
export ENVIRONMENT="production"
```

---

## 🧪 测试命令

### 运行所有测试

```bash
pytest
```

### 运行特定测试

```bash
# 单元测试
pytest tests/unit/

# 集成测试
pytest tests/integration/

# 特定文件
pytest tests/unit/test_agent_nodes.py
```

### 查看覆盖率

```bash
pytest --cov=src --cov-report=html
open reports/coverage/index.html
```

### 运行性能测试

```bash
pytest tests/performance/test_performance.py
```

---

## 🐳 Docker 命令

### 构建镜像

```bash
docker build -t feishumind:v1.0.0 .
```

### 启动服务

```bash
docker-compose up -d
```

### 查看日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f fastapi
```

### 停止服务

```bash
docker-compose down
```

### 重启服务

```bash
docker-compose restart
```

### 进入容器

```bash
docker-compose exec fastapi bash
```

---

## 📊 监控

### Prometheus

访问地址: http://localhost:9090

**关键指标**:
- `http_requests_total` - HTTP 请求总数
- `http_request_duration_seconds` - 请求响应时间
- `memory_usage_bytes` - 内存使用量
- `cpu_usage_percent` - CPU 使用率

### Grafana

访问地址: http://localhost:3000

**默认登录**:
- 用户名: `admin`
- 密码: `admin`

**仪表板**:
- FeishuMind Overview - 系统概览
- API Performance - API 性能
- Resource Usage - 资源使用

### 健康检查

```bash
# API 健康检查
curl http://localhost:8000/health

# 数据库连接检查
curl http://localhost:8000/health/db

# Redis 连接检查
curl http://localhost:8000/health/redis
```

---

## 🔍 故障排除

### 常见问题

#### 1. 端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# 查找占用进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或使用其他端口
uvicorn src.api.main:app --port 8001
```

#### 2. 依赖安装失败

**错误**: `Failed to build wheel`

**解决**:
```bash
# 更新 pip
pip install --upgrade pip

# 使用系统包管理器
sudo apt-get install python3-dev build-essential

# 或使用 conda
conda install -c conda-forge <package_name>
```

#### 3. 数据库连接失败

**错误**: `Could not connect to server`

**解决**:
```bash
# 检查 PostgreSQL 是否运行
docker-compose ps postgres

# 重启数据库
docker-compose restart postgres

# 检查连接字符串
echo $DATABASE_URL
```

#### 4. Redis 连接失败

**错误**: `Redis connection refused`

**解决**:
```bash
# 检查 Redis 是否运行
docker-compose ps redis

# 重启 Redis
docker-compose restart redis

# 测试连接
redis-cli ping
```

#### 5. 内存不足

**错误**: `OutOfMemoryError`

**解决**:
```bash
# 清理 Docker 缓存
docker system prune -a

# 限制内存使用
docker-compose up -d --scale fastapi=1

# 或增加系统内存
# (虚拟机设置中增加内存分配)
```

### 日志查看

```bash
# 应用日志
tail -f logs/feishumind.log

# 错误日志
tail -f logs/error.log

# Docker 日志
docker-compose logs -f fastapi
```

---

## 📚 文档链接

| 文档 | 链接 |
|------|------|
| 🚀 快速开始 | [docs/quick-start.md](./docs/quick-start.md) |
| 📖 项目总览 | [docs/spec/00-overview.md](./docs/spec/00-overview.md) |
| 🏗️ 技术架构 | [docs/spec/01-architecture.md](./docs/spec/01-architecture.md) |
| 🔌 API 规范 | [docs/spec/02-api-spec.md](./docs/spec/02-api-spec.md) |
| 📋 开发规范 | [docs/spec/03-coding-standards.md](./docs/spec/03-coding-standards.md) |
| 🐳 部署指南 | [docs/deployment-guide.md](./docs/deployment-guide.md) |
| ⚡ 性能优化 | [docs/performance-optimization.md](./docs/performance-optimization.md) |
| 🧪 用户测试 | [docs/user-testing-guide.md](./docs/user-testing-guide.md) |

---

## 🛠️ 开发工具

### 代码格式化

```bash
# Black 格式化
black src/

# isort 排序
isort src/

# 同时运行
black src/ && isort src/
```

### 代码检查

```bash
# Flake8 检查
flake8 src/

# MyPy 类型检查
mypy src/

# Bandit 安全检查
bandit -r src/
```

### 运行检查脚本

```bash
# 依赖检查
python scripts/check_dependencies.py

# 代码质量检查
python scripts/check_code_quality.py

# 性能基准测试
python scripts/performance_benchmark.py
```

---

## 📞 获取帮助

### 文档

- 📖 [完整文档](https://docs.feishumind.com)
- 🔌 [API 文档](http://localhost:8000/docs)
- 📚 [ReDoc 文档](http://localhost:8000/redoc)

### 社区

- 💬 [飞书社区](https://feishu.cn/join-community)
- 🐛 [GitHub Issues](https://github.com/your-org/feishumind/issues)
- 💡 [GitHub Discussions](https://github.com/your-org/feishumind/discussions)

### 联系方式

- **邮箱**: support@feishumind.com
- **官网**: https://feishumind.com

---

## 🎯 快速任务清单

### 新用户入门

- [ ] 克隆仓库
- [ ] 安装依赖
- [ ] 配置环境变量
- [ ] 启动服务
- [ ] 访问 API 文档
- [ ] 运行健康检查
- [ ] 测试对话功能
- [ ] 阅读项目文档

### 开发者准备

- [ ] 设置虚拟环境
- [ ] 安装开发依赖
- [ ] 配置 pre-commit hooks
- [ ] 运行测试
- [ ] 阅读开发规范
- [ ] 熟悉代码结构
- [ ] 设置 IDE
- [ ] 加入开发社区

### 部署准备

- [ ] 配置生产环境变量
- [ ] 构建 Docker 镜像
- [ ] 配置 Nginx
- [ ] 设置数据库
- [ ] 配置监控
- [ ] 设置 CI/CD
- [ ] 备份数据
- [ ] 测试部署

---

## 📝 常用命令速查

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 运行测试
pytest

# 代码格式化
black src/ && isort src/

# 构建镜像
docker build -t feishumind:v1.0.0 .

# 健康检查
curl http://localhost:8000/health

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 查看覆盖率
pytest --cov=src --cov-report=html
```

---

**版本**: v1.0.0
**最后更新**: 2026-02-06
**维护者**: FeishuMind Team

---

**Made with ❤️ by FeishuMind Team**
