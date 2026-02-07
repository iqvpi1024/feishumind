# 快速开始指南

欢迎使用 FeishuMind！本指南将帮助你在 10 分钟内完成从安装到第一个对话的完整流程。

---

## 📋 前置准备

### 必需条件

- ✅ Python 3.12+
- ✅ 飞书开发者账号
- ✅ Mem0 API Key ([获取](https://app.mem0.ai/))

### 可选条件

- ✅ Docker & Docker Compose (用于容器化部署)
- ✅ GitHub Token (用于 GitHub Trending 功能)

---

## 🚀 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/feishumind.git
cd feishumind
```

### 2. 创建虚拟环境

```bash
# 使用 Python 3.12
python3.12 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入必要配置
nano .env  # 或使用你喜欢的编辑器
```

**必须配置的环境变量**:

```bash
# Mem0 配置
MEM0_API_KEY=your_mem0_api_key_here

# 飞书配置
FEISHU_APP_ID=your_feishu_app_id
FEISHU_APP_SECRET=your_feishu_app_secret
FEISHU_VERIFICATION_TOKEN=your_verification_token
FEISHU_ENCRYPT_KEY=your_encrypt_key
```

### 5. 初始化数据库

```bash
# SQLite 会自动创建在 data/mem0.db
mkdir -p data
```

### 6. 启动服务

```bash
# 开发模式
python3.12 -m uvicorn src.api.main:app --reload --port 8000

# 生产模式
python3.12 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 7. 验证安装

```bash
# 健康检查
curl http://localhost:8000/health

# 预期响应
# {
#   "status": "healthy",
#   "service": "FeishuMind",
#   "version": "1.0.0"
# }
```

---

## 💬 第一个对话

### 方法 1: 使用 API

```python
import httpx

async def chat_with_feishumind():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/agent/chat",
            json={
                "message": "你好，我想了解今天的工作安排",
                "context": {
                    "user_id": "test_user_123",
                    "session_id": "session_456"
                }
            }
        )
        print(response.json())

# 运行
import asyncio
asyncio.run(chat_with_feishumind())
```

### 方法 2: 使用 Swagger UI

1. 打开浏览器访问: `http://localhost:8000/docs`
2. 找到 `POST /api/v1/agent/chat` 接口
3. 点击 "Try it out"
4. 输入测试消息
5. 点击 "Execute"

---

## 🎯 常见使用场景

### 场景 1: 创建事件提醒

```python
response = await client.post(
    "http://localhost:8000/api/v1/agent/chat",
    json={
        "message": "提醒我明天下午3点开会",
        "context": {"user_id": "user_123"}
    }
)
```

**预期行为**:
- Agent 解析时间: 明天下午3点
- 创建飞书日历事件
- 设置提醒: 提前15分钟、1小时、1天

### 场景 2: GitHub 热门推送

```python
# 配置定时任务 (每天9点推送)
from src.utils.scheduler import TaskScheduler

scheduler = TaskScheduler()
scheduler.add_github_trending_job(
    hour=9,
    languages=["Python", "JavaScript"],
    min_stars=100
)
```

### 场景 3: 韧性辅导

```python
response = await client.post(
    "http://localhost:8000/api/v1/resilience/analyze",
    json={
        "content": "这周项目压力很大，经常加班",
        "user_id": "user_123"
    }
)

# 返回压力分析和建议
# {
#   "stress_level": "high",
#   "factors": ["项目截止", "加班频繁"],
#   "recommendations": ["建议拆分任务", "安排休息时间"]
# }
```

---

## 🔧 配置飞书 Bot

### 1. 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 获取 App ID 和 App Secret

### 2. 配置权限

在飞书开放平台，开启以下权限:

- ✅ `im:message` (接收消息)
- ✅ `im:message:send_as_bot` (发送消息)
- ✅ `calendar:calendar` (日历读写)
- ✅ `contact:user.base:readonly` (读取用户信息)

### 3. 配置事件订阅

1. 在飞书开放平台，选择 "事件订阅"
2. 填入请求 URL: `https://your-domain.com/webhook/feishu`
3. 订阅事件: `im.message.receive_v1`

### 4. 配置加密

```bash
# 在飞书开放平台获取
FEISHU_VERIFICATION_TOKEN=your_verification_token
FEISHU_ENCRYPT_KEY=your_encrypt_key
```

---

## 🧪 运行测试

```bash
# 运行所有测试
python3.12 -m pytest

# 运行单元测试
python3.12 -m pytest tests/unit/

# 运行集成测试
python3.12 -m pytest tests/integration/

# 生成覆盖率报告
python3.12 -m pytest --cov=src --cov-report=html
```

---

## 🐛 常见问题

### Q1: 依赖安装失败

**问题**: `pip install` 报错

**解决**:
```bash
# 升级 pip
python3.12 -m pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q2: 服务无法启动

**问题**: `uvicorn` 启动失败

**解决**:
```bash
# 检查端口是否被占用
lsof -i :8000

# 使用其他端口
uvicorn src.api.main:app --port 8001
```

### Q3: 飞书 Webhook 验证失败

**问题**: 飞书无法连接到 Webhook

**解决**:
1. 确保服务器有公网 IP
2. 使用 ngrok 做本地测试:
   ```bash
   ngrok http 8000
   ```
3. 检查防火墙设置

### Q4: Mem0 API 错误

**问题**: `MEM0_API_KEY` 无效

**解决**:
1. 访问 https://app.mem0.ai/
2. 登录/注册账号
3. 在 Settings 中获取 API Key
4. 确保余额充足

---

## 📚 下一步

- 📖 阅读 [完整文档](./spec/00-overview.md)
- 🚀 查看 [API 文档](./spec/02-api-spec.md)
- 🤝 参与 [社区贡献](./CONTRIBUTING.md)
- 💡 查看 [使用示例](../examples/)

---

## 🆘 获取帮助

- 📧 邮箱: support@feishumind.com
- 💬 飞书社区: [加入讨论](https://feishu.cn/join-community)
- 🐛 问题反馈: [GitHub Issues](https://github.com/your-repo/feishumind/issues)

---

**祝你使用愉快！** 🎉
