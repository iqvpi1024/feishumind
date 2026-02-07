#!/bin/bash
# FeishuMind 部署脚本
#
# 用于快速部署 FeishuMind 到生产环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
DOCKER_COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="/backup/feishumind"
LOG_FILE="/var/log/feishumind/deploy.log"

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# 检查 Docker
check_docker() {
    log "检查 Docker 环境..."
    if ! command -v docker &> /dev/null; then
        error "Docker 未安装，请先安装 Docker"
    fi
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose 未安装，请先安装 Docker Compose"
    fi
    log "✓ Docker 环境正常"
}

# 备份数据
backup_data() {
    log "备份数据..."
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/feishumind_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

    tar -czf "$BACKUP_FILE" \
        data/ \
        logs/ \
        .env \
        deployments/ 2>/dev/null || warning "部分文件备份失败"

    log "✓ 备份完成: $BACKUP_FILE"
}

# 拉取最新镜像
pull_images() {
    log "拉取最新 Docker 镜像..."
    docker-compose pull
    log "✓ 镜像拉取完成"
}

# 停止服务
stop_services() {
    log "停止现有服务..."
    docker-compose down
    log "✓ 服务已停止"
}

# 启动服务
start_services() {
    log "启动服务..."
    docker-compose up -d
    log "✓ 服务启动完成"
}

# 健康检查
health_check() {
    log "执行健康检查..."
    sleep 10  # 等待服务启动

    MAX_RETRIES=30
    RETRY_COUNT=0

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log "✓ 健康检查通过"
            return 0
        fi

        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -n "."
        sleep 2
    done

    error "健康检查失败"
}

# 清理旧镜像
cleanup_images() {
    log "清理旧镜像..."
    docker image prune -f
    log "✓ 清理完成"
}

# 显示服务状态
show_status() {
    log "服务状态:"
    docker-compose ps
}

# 部署主函数
deploy() {
    log "========================================"
    log "开始部署 FeishuMind"
    log "========================================"

    check_docker
    backup_data
    pull_images
    stop_services
    start_services
    health_check
    cleanup_images
    show_status

    log "========================================"
    log "部署完成！"
    log "========================================"
}

# 回滚函数
rollback() {
    log "开始回滚..."

    # 查找最新备份
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/feishumind_backup_*.tar.gz 2>/dev/null | head -1)

    if [ -z "$LATEST_BACKUP" ]; then
        error "未找到备份文件"
    fi

    log "使用备份: $LATEST_BACKUP"

    # 停止服务
    docker-compose down

    # 恢复备份
    log "恢复数据..."
    tar -xzf "$LATEST_BACKUP" -C /

    # 重启服务
    start_services
    health_check

    log "回滚完成"
}

# 显示使用帮助
show_help() {
    cat << EOF
FeishuMind 部署脚本

用法:
  $0 [COMMAND]

命令:
  deploy    部署服务 (默认)
  rollback  回滚到上一个版本
  status    查看服务状态
  logs      查看服务日志
  stop      停止服务
  start     启动服务
  restart   重启服务
  help      显示此帮助信息

示例:
  $0 deploy
  $0 rollback
  $0 status

EOF
}

# 主逻辑
main() {
    case "${1:-deploy}" in
        deploy)
            deploy
            ;;
        rollback)
            rollback
            ;;
        status)
            show_status
            ;;
        logs)
            docker-compose logs -f
            ;;
        stop)
            log "停止服务..."
            docker-compose down
            log "✓ 服务已停止"
            ;;
        start)
            log "启动服务..."
            docker-compose up -d
            log "✓ 服务已启动"
            ;;
        restart)
            log "重启服务..."
            docker-compose restart
            log "✓ 服务已重启"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行
main "$@"
