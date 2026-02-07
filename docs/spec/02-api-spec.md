# FeishuMind API 接口规范

**版本**: 1.0.0
**最后更新**: 2026-02-06
**Base URL**: `https://api.feishumind.com/v1`
**认证方式**: JWT Bearer Token

## 🔐 认证

### 获取 Token

```http
POST /auth/token
Content-Type: application/json

{
  "user_id": "feishu_user_id",
  "signature": "feishu_request_signature"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### 使用 Token

```http
Authorization: Bearer <access_token>
```

## 📡 飞书 Webhook

### 接收消息

```http
POST /webhook/feishu
X-Feishu-Timestamp: 1641234567
X-Feishu-Signature: sha256=...

{
  "type": "event",
  "event_id": "event_123",
  "timestamp": 1641234567,
  "user_id": "ou_xxxx",
  "message": {
    "content": "提醒我明天下午3点开会",
    "message_type": "text"
  }
}
```

**响应**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "message_id": "msg_xxx",
    "status": "processed"
  }
}
```

## 🤖 Agent 交互

### 对话接口

```http
POST /agent/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "我这周工作压力很大",
  "context": {
    "user_id": "ou_xxx",
    "session_id": "session_xxx"
  },
  "options": {
    "enable_memory": true,
    "enable_proactive": true
  }
}
```

**响应**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "response": "理解你的感受。根据你本周的提交记录和情绪曲线，我建议...",
    "actions": [
      {
        "type": "calendar_block",
        "title": "专注时段建议",
        "params": {
          "start": "2026-02-07T14:00:00Z",
          "duration": 60
        }
      }
    ],
    "memory_updated": true,
    "confidence": 0.85
  }
}
```

### 技能生成建议

```http
GET /agent/skills/suggestions
Authorization: Bearer <token>
```

**响应**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "suggestions": [
      {
        "id": "skill_opt_weekly_report",
        "name": "优化周报格式",
        "description": "基于你的历史周报，我可以帮你自动生成结构化周报模板",
        "estimated_impact": "节省每周30分钟",
        "requires_approval": true
      }
    ]
  }
}
```

### 批准技能执行

```http
POST /agent/skills/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "skill_id": "skill_opt_weekly_report",
  "approved": true,
  "parameters": {
    "format": "markdown"
  }
}
```

## 💾 记忆管理

### 添加记忆

```http
POST /memory
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "preference",
  "content": "我喜欢在早上处理高难度任务",
  "category": "work_habit",
  "metadata": {
    "source": "user_explicit",
    "confidence": 1.0
  }
}
```

**响应**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "memory_id": "mem_xxx",
    "created_at": "2026-02-06T10:00:00Z"
  }
}
```

### 检索记忆

```http
POST /memory/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "工作压力",
  "limit": 10,
  "filters": {
    "category": ["emotion", "event"]
  }
}
```

**响应**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "memories": [
      {
        "id": "mem_xxx",
        "type": "emotion",
        "content": "周二焦虑高峰",
        "score": 0.92,
        "timestamp": "2026-02-05T15:30:00Z"
      }
    ],
    "total": 1
  }
}
```

### 反馈评分

```http
POST /memory/{memory_id}/feedback
Authorization: Bearer <token>
Content-Type: application/json

{
  "score": 0.6,
  "reason": "不够具体，需要更多上下文"
}
```

## 📅 自动化任务

### GitHub 热门推送

```http
POST /tasks/github-trending
Authorization: Bearer <token>
Content-Type: application/json

{
  "schedule": "0 9 * * *",
  "filters": {
    "languages": ["Python", "JavaScript"],
    "min_stars": 100
  },
  "template": "daily_report"
}
```

### 事件提醒

```http
POST /tasks/reminder
Authorization: Bearer <token>
Content-Type: application/json

{
  "event": {
    "title": "项目周会",
    "time": "2026-02-07T15:00:00Z",
    "remind_before": "1d"
  },
  "message": "记得准备周报数据"
}
```

### 周报情绪复盘

```http
POST /tasks/weekly-review
Authorization: Bearer <token>
Content-Type: application/json

{
  "week_start": "2026-02-01",
  "include_metrics": true,
  "format": "card"
}
```

## 📊 统计分析

### 用户洞察

```http
GET /analytics/insights
Authorization: Bearer <token>
Query: ?period=7d
```

**响应**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "emotion_curve": [
      {"date": "2026-02-01", "score": 0.6},
      {"date": "2026-02-02", "score": 0.5}
    ],
    "top_stressors": ["项目截止", "会议过多"],
    "productivity_score": 0.72,
    "recommendations": [
      "建议减少周二下午会议"
    ]
  }
}
```

### Token 使用统计

```http
GET /analytics/usage
Authorization: Bearer <token>
Query: ?start=2026-02-01&end=2026-02-06
```

**响应**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "total_tokens": 15430,
    "daily_average": 2571,
    "cost_estimate": 0.31,
    "breakdown": {
      "chat": 12000,
      "memory": 2430,
      "skills": 1000
    }
  }
}
```

## 🔧 系统管理

### 健康检查

```http
GET /health
```

**响应**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dependencies": {
    "redis": "ok",
    "postgres": "ok",
    "mem0": "ok"
  }
}
```

### 配置更新

```http
POST /admin/config
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "update": {
    "max_tokens_per_user": 5000,
    "enable_proactive_mode": true
  }
}
```

## ❌ 错误码

| Code | 说明 | 处理建议 |
|------|------|---------|
| 0 | 成功 | - |
| 400 | 请求参数错误 | 检查请求格式 |
| 401 | 认证失败 | 重新获取 Token |
| 403 | 权限不足 | 联系管理员 |
| 429 | 请求频率限制 | 降级重试 |
| 500 | 服务器内部错误 | 提交工单 |
| 503 | 服务不可用 | 稍后重试 |

**错误响应示例**:
```json
{
  "code": 400,
  "msg": "Invalid request parameter",
  "error": {
    "field": "message",
    "reason": "Cannot be empty"
  }
}
```

## 📝 速率限制

| 接口类型 | 限制 |
|---------|------|
| Webhook | 100 req/min |
| Agent Chat | 30 req/min/user |
| Memory Search | 60 req/min/user |
| Analytics | 10 req/min/user |

超限返回 `429` 状态码，响应头包含:
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1641234667
```

---

**下一步**: 阅读 [开发规范](./03-coding-standards.md) 了解代码规范。
