# FeishuMind 部署指南

本文档介绍如何部署 FeishuMind 项目到生产环境。

## 目录

1. [环境要求](#环境要求)
2. [本地部署](#本地部署)
3. [Docker部署](#docker部署)
4. [云服务部署](#云服务部署)
5. [配置管理](#配置管理)
6. [监控和日志](#监控和日志)
7. [故障排查](#故障排查)

---

## 环境要求

### 系统要求

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 8+)
- **Python**: 3.12+
- **内存**: 最低 512MB，推荐 1GB+
- **CPU**: 最低 1 核，推荐 2 核+
- **磁盘**: 最低 5GB，推荐 20GB+

### 依赖服务

- **Mem0 API**: 记忆存储服务
- **飞书开放平台**: Webhook和消息推送
- **GLM API**: 可选，LLM服务

---

## 本地部署

### 1. 克隆代码

```bash
git clone https://github.com/your-org/feishumind.git
cd feishumind
```

### 2. 创建虚拟环境

```bash
python3.12 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发环境
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写必要配置
nano .env
```

### 5. 初始化数据库

```bash
# 如果使用 SQLite（默认）
# 数据库会自动创建在 data/mem0.db

# 如果使用 PostgreSQL
createdb feishumind
python -m src.utils.init_db
```

### 6. 启动服务

```bash
# 开发模式
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 7. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# 访问 API 文档
open http://localhost:8000/docs
```

---

## Docker部署

### 1. 构建镜像

```bash
docker build -t feishumind:latest .
```

### 2. 运行容器

```bash
docker run -d \
  --name feishumind \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  feishumind:latest
```

### 3. 使用 Docker Compose

```bash
docker-compose up -d
```

### 4. 查看日志

```bash
docker logs -f feishumind
```

### 5. 停止服务

```bash
docker stop feishumind
docker rm feishumind
```

---

## 云服务部署

### AWS 部署

#### 使用 EC2

1. **启动 EC2 实例**

```bash
# 选择 Ubuntu 20.04 AMI
# 实例类型: t3.medium (2 vCPU, 4GB RAM)
```

2. **配置安全组**

```bash
# 允许入站规则
- SSH (22)
- HTTP (80)
- HTTPS (443)
- 自定义 TCP (8000)
```

3. **部署应用**

```bash
# SSH 登录
ssh -i your-key.pem ubuntu@ec2-xxx.amazonaws.com

# 安装依赖
sudo apt update
sudo apt install -y python3.12 python3.12-venv

# 克隆代码
git clone https://github.com/your-org/feishumind.git
cd feishumind

# 配置和启动（参考本地部署步骤）
```

4. **使用 Nginx 反向代理**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 使用 ECS

1. **创建任务定义**

```json
{
  "family": "feishumind",
  "containerDefinitions": [
    {
      "name": "feishumind",
      "image": "your-ecr-repo/feishumind:latest",
      "memory": 512,
      "cpu": 256,
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/feishumind",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

2. **创建服务**

```bash
aws ecs create-service \
  --cluster feishumind-cluster \
  --service-name feishumind-service \
  --task-definition feishumind \
  --desired-count 2 \
  --launch-type FARGATE
```

### Azure 部署

#### 使用 Azure Container Instances

```bash
az container create \
  --resource-group feishumind-rg \
  --name feishumind \
  --image your-registry/feishumind:latest \
  --cpu 1 \
  --memory 1 \
  --ports 8000 \
  --environment-variables \
    ENVIRONMENT=production \
    MEM0_API_KEY=$MEM0_API_KEY
```

### Google Cloud 部署

####使用 Cloud Run

```bash
# 构建并推送镜像
gcloud builds submit --tag gcr.io/PROJECT_ID/feishumind

# 部署
gcloud run deploy feishumind \
  --image gcr.io/PROJECT_ID/feishumind \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1
```

---

## 配置管理

### 环境变量

#### 必需配置

```bash
# Mem0 配置
MEM0_API_KEY=your_mem0_api_key
MEM0_BASE_URL=https://api.mem0.ai/v1

# 飞书配置
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_VERIFICATION_TOKEN=your_verification_token
FEISHU_ENCRYPT_KEY=your_encrypt_key

# 应用配置
ENVIRONMENT=production
LOG_LEVEL=INFO
```

#### 可选配置

```bash
# GLM 配置
GLM_API_KEY=your_glm_api_key
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/feishumind

# 缓存配置
CACHE_ENABLED=true
CACHE_TTL=300
CACHE_MAX_SIZE=1000

# 调度器配置
SCHEDULER_ENABLED=true
GITHUB_TRENDING_TIME="09:00"
```

### 配置文件

#### 使用配置文件

```bash
# 创建配置目录
mkdir -p /etc/feishumind

# 复制配置文件
cp config/production.yaml /etc/feishumind/config.yaml

# 修改配置
nano /etc/feishumind/config.yaml
```

#### 配置文件示例

```yaml
# config/production.yaml
app:
  name: feishumind
  version: 1.0.0
  environment: production
  debug: false

server:
  host: 0.0.0.0
  port: 8000
  workers: 4

logging:
  level: INFO
  file: /var/log/feishumind/app.log
  rotation: daily

memory:
  api_key: ${MEM0_API_KEY}
  base_url: ${MEM0_BASE_URL}

feishu:
  app_id: ${FEISHU_APP_ID}
  app_secret: ${FEISHU_APP_SECRET}
  verification_token: ${FEISHU_VERIFICATION_TOKEN}
  encrypt_key: ${FEISHU_ENCRYPT_KEY}

cache:
  enabled: true
  ttl: 300
  max_size: 1000

scheduler:
  enabled: true
  github_trending_time: "09:00"
```

---

## 监控和日志

### 日志管理

#### 日志位置

```bash
# 应用日志
/var/log/feishumind/app.log

# 访问日志
/var/log/nginx/access.log

# 错误日志
/var/log/nginx/error.log
```

#### 日志轮转

```bash
# /etc/logrotate.d/feishumind
/var/log/feishumind/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload feishumind
    endscript
}
```

### 性能监控

#### 使用 Prometheus

```python
# 安装依赖
pip install prometheus-fastapi-instrumentator

# 在 main.py 中添加
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

#### 使用 Grafana

```bash
# 安装 Grafana
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

### 健康检查

```bash
# 创建健康检查脚本
cat > /usr/local/bin/check_feishumind.sh << 'EOF'
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ $response -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy: HTTP $response"
    exit 1
fi
EOF

chmod +x /usr/local/bin/check_feishumind.sh

# 配置 cron 监控
*/5 * * * * /usr/local/bin/check_feishumind.sh >> /var/log/feishumind/health.log 2>&1
```

---

## 故障排查

### 常见问题

#### 1. 服务无法启动

```bash
# 检查端口是否被占用
sudo lsof -i :8000

# 检查日志
sudo journalctl -u feishumind -n 50

# 检查配置
python -m src.utils.config
```

#### 2. 数据库连接失败

```bash
# 检查数据库服务
sudo systemctl status postgresql

# 测试连接
psql -h localhost -U feishumind -d feishumind

# 检查防火墙
sudo ufw status
```

#### 3. 内存不足

```bash
# 检查内存使用
free -h

# 检查进程内存
ps aux --sort=-%mem | head

# 清理缓存
sudo sync && sudo sysctl -w vm.drop_caches=3
```

#### 4. API 响应慢

```bash
# 检查系统负载
top

# 检查数据库查询
# 启用慢查询日志

# 检查网络延迟
ping api.mem0.ai
```

### 日志分析

```bash
# 查看错误日志
grep ERROR /var/log/feishumind/app.log

# 查看访问统计
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10

# 查看慢请求
awk '$NF > 1000' /var/log/feishumind/app.log
```

### 性能优化

```bash
# 增加 worker 数量
uvicorn src.api.main:app --workers 8

# 启用 gzip 压缩
# 在 Nginx 配置中添加
gzip on;
gzip_types text/plain application/json;

# 启用缓存
# 在应用配置中设置
CACHE_ENABLED=true
```

---

## 备份和恢复

### 数据库备份

```bash
# PostgreSQL
pg_dump -U feishumind feishumind > backup_$(date +%Y%m%d).sql

# SQLite
cp data/mem0.db backup/mem0_$(date +%Y%m%d).db
```

### 自动备份

```bash
# 创建备份脚本
cat > /usr/local/bin/backup_feishumind.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/backup/feishumind
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
pg_dump -U feishumind feishumind | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 备份配置文件
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /etc/feishumind

# 删除30天前的备份
find $BACKUP_DIR -mtime +30 -delete
EOF

chmod +x /usr/local/bin/backup_feishumind.sh

# 配置 cron
0 2 * * * /usr/local/bin/backup_feishumind.sh
```

---

## 安全建议

### 1. 使用 HTTPS

```bash
# 使用 Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 2. 配置防火墙

```bash
# UFW
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
```

### 3. 限制 API 访问

```python
# 在 main.py 中添加 rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/v1/agent/chat")
@limiter.limit("10/minute")
async def chat(request: Request):
    ...
```

### 4. 定期更新

```bash
# 定期更新依赖
pip list --outdated
pip install --upgrade package_name

# 更新系统
sudo apt update && sudo apt upgrade
```

---

## 总结

部署 FeishuMind 的关键步骤：

1. ✅ 准备环境和依赖
2. ✅ 配置环境变量
3. ✅ 安装依赖并启动服务
4. ✅ 配置反向代理（Nginx）
5. ✅ 设置监控和日志
6. ✅ 配置备份策略
7. ✅ 测试和验证

保持系统安全、稳定、高性能！

---

**文档版本**: 1.0
**最后更新**: 2026-02-06
**维护者**: FeishuMind Team
