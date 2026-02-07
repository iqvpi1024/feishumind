# 部署检查清单

**文档版本**: 1.0
**最后更新**: 2026-02-06
**适用环境**: 生产环境

---

## 📋 部署前检查

### 1. 环境准备

- [ ] 服务器准备
  - [ ] CPU: 最低 2 核，推荐 4 核+
  - [ ] 内存: 最低 4GB，推荐 8GB+
  - [ ] 磁盘: 最低 20GB，推荐 50GB+
  - [ ] 操作系统: Ubuntu 20.04+ 或 CentOS 8+

- [ ] 网络配置
  - [ ] 公网 IP
  - [ ] 域名已配置
  - [ ] DNS 已解析
  - [ ] 防火墙规则已设置 (80, 443, 22)

- [ ] Docker 环境
  - [ ] Docker 已安装 (版本 20.10+)
  - [ ] Docker Compose 已安装 (版本 2.0+)
  - [ ] Docker 服务运行正常

---

### 2. 配置文件检查

- [ ] `.env` 文件
  ```bash
  # 必需配置
  MEM0_API_KEY=your_mem0_api_key
  FEISHU_APP_ID=your_feishu_app_id
  FEISHU_APP_SECRET=your_feishu_app_secret
  FEISHU_VERIFICATION_TOKEN=your_verification_token
  FEISHU_ENCRYPT_KEY=your_encrypt_key

  # 可选配置
  ENVIRONMENT=production
  LOG_LEVEL=INFO
  ```

- [ ] `docker-compose.yml`
  - [ ] 端口映射正确
  - [ ] 卷挂载正确
  - [ ] 环境变量已配置

- [ ] Nginx 配置
  - [ ] SSL 证书已准备
  - [ ] 反向代理配置正确
  - [ ] 限流规则已设置

---

### 3. 服务依赖检查

- [ ] 外部 API
  - [ ] Mem0 API 可访问
  - [ ] 飞书开放平台 API 可访问
  - [ ] GitHub API 可访问 (如需要)

- [ ] 数据库
  - [ ] PostgreSQL 已部署 (或使用云服务)
  - [ ] 数据库已创建
  - [ ] 用户权限已设置
  - [ ] 备份策略已配置

- [ ] 缓存
  - [ ] Redis 已部署
  - [ ] 持久化已启用
  - [ ] 内存限制已设置

---

### 4. 安全检查

- [ ] 密钥管理
  - [ ] 所有密钥已更新
  - [ ] 密钥未提交到代码仓库
  - [ ] 密钥轮换策略已制定

- [ ] SSL/TLS
  - [ ] SSL 证书已安装
  - [ ] HTTPS 已启用
  - [ ] HTTP 自动重定向到 HTTPS

- [ ] 防火墙
  - [ ] 仅开放必要端口
  - [ ] SSH 密钥认证已启用
  - [ ] root 登录已禁用

- [ ] 服务安全
  - [ ] 运行在非 root 用户下
  - [ ] 文件权限正确
  - [ ] 敏感文件已加密

---

## 🚀 部署步骤

### 1. 准备部署文件

```bash
# 克隆代码
git clone https://github.com/your-repo/feishumind.git
cd feishumind

# 创建必要目录
mkdir -p data logs deployments/nginx/ssl

# 复制配置文件
cp .env.example .env
nano .env  # 填入配置
```

---

### 2. 配置 SSL 证书

**方法 1: 使用 Let's Encrypt (推荐)**

```bash
# 安装 certbot
sudo apt install certbot

# 获取证书
sudo certbot certonly --standalone -d your-domain.com

# 证书位置
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem

# 复制证书
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem \
        deployments/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem \
        deployments/nginx/ssl/key.pem
```

**方法 2: 使用自签名证书 (测试)**

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deployments/nginx/ssl/key.pem \
  -out deployments/nginx/ssl/cert.pem
```

---

### 3. 启动服务

```bash
# 拉取镜像
docker-compose pull

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f feishumind
```

---

### 4. 验证部署

```bash
# 健康检查
curl https://your-domain.com/health

# 预期响应
# {
#   "status": "healthy",
#   "service": "FeishuMind",
#   "version": "1.0.0"
# }

# 访问 API 文档
open https://your-domain.com/docs
```

---

## 📊 部署后验证

### 1. 功能验证

- [ ] 健康检查端点
- [ ] API 文档可访问
- [ ] 对话功能正常
- [ ] 事件提醒功能正常
- [ ] 飞书 Webhook 正常

---

### 2. 性能验证

- [ ] 响应时间 < 2s
- [ ] 并发支持 > 50 用户
- [ ] 内存使用 < 4GB
- [ ] CPU 使用 < 50%

---

### 3. 监控配置

- [ ] Prometheus 已配置
- [ ] Grafana 已配置
- [ ] 告警规则已设置
- [ ] 日志收集已配置

---

## 🔄 日常运维

### 备份策略

- [ ] 数据库每日备份
- [ ] 配置文件版本控制
- [ ] 日志定期归档
- [ ] 备份异地存储

### 监控指标

- [ ] 系统资源监控
- [ ] API 响应时间
- [ ] 错误率监控
- [ ] 用户活跃度

### 更新策略

- [ ] 定期安全更新
- [ ] 功能迭代计划
- [ ] 灰度发布流程
- [ ] 回滚方案

---

## 🐛 故障处理

### 常见问题

**问题 1: 服务无法启动**

```bash
# 检查日志
docker-compose logs feishumind

# 检查端口占用
sudo lsof -i :8000

# 重启服务
docker-compose restart feishumind
```

**问题 2: 数据库连接失败**

```bash
# 检查数据库状态
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 测试连接
psql -h localhost -U feishumind -d feishumind
```

**问题 3: 内存不足**

```bash
# 检查内存使用
free -h

# 清理 Docker 资源
docker system prune -a

# 增加 swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📞 紧急联系

- **技术负责人**: ________________
- **运维负责人**: ________________
- **飞书群**: ________________

---

## ✅ 部署完成确认

- [ ] 所有服务运行正常
- [ ] 健康检查通过
- [ ] 功能验证通过
- [ ] 性能指标达标
- [ ] 监控配置完成
- [ ] 备份策略已启用
- [ ] 文档已更新

---

**部署完成时间**: ____-____-____
**部署人员**: ________________
**审核人员**: ________________

---

**祝你部署顺利！** 🎉
