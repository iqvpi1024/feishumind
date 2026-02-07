#!/bin/bash
# FeishuMind 回滚脚本
#
# 用于快速回滚到上一个稳定版本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
BACKUP_DIR="/backup/feishumind"
LOG_FILE="/var/log/feishumind/rollback.log"

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

# 确认回滚
confirm_rollback() {
    echo ""
    echo "⚠️  警告: 即将回滚到上一个版本！"
    echo "此操作将:"
    echo "  - 停止当前服务"
    echo "  - 恢复备份数据"
    echo "  - 重启服务"
    echo ""
    read -p "确认继续? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log "回滚已取消"
        exit 0
    fi
}

# 查找备份
find_backup() {
    log "查找备份文件..."

    if [ ! -d "$BACKUP_DIR" ]; then
        error "备份目录不存在: $BACKUP_DIR"
    fi

    # 列出所有备份
    BACKUPS=($(ls -t "$BACKUP_DIR"/feishumind_backup_*.tar.gz 2>/dev/null))

    if [ ${#BACKUPS[@]} -eq 0 ]; then
        error "未找到备份文件"
    fi

    log "找到 ${#BACKUPS[@]} 个备份:"
    for i in "${!BACKUPS[@]}"; do
        echo "  [$i] $(basename ${BACKUPS[$i]})"
    done

    echo ""
    read -p "选择备份编号 (默认 0): " backup_index

    backup_index=${backup_index:-0}

    if [ $backup_index -lt 0 ] || [ $backup_index -ge ${#BACKUPS[@]} ]; then
        error "无效的备份编号"
    fi

    BACKUP_FILE="${BACKUPS[$backup_index]}"
    log "选择备份: $(basename $BACKUP_FILE)"
}

# 停止服务
stop_services() {
    log "停止服务..."
    docker-compose down
    log "✓ 服务已停止"
}

# 恢复数据
restore_data() {
    log "恢复数据..."
    tar -xzf "$BACKUP_FILE" -C /
    log "✓ 数据恢复完成"
}

# 启动服务
start_services() {
    log "启动服务..."
    docker-compose up -d
    log "✓ 服务已启动"
}

# 健康检查
health_check() {
    log "执行健康检查..."
    sleep 10

    if curl -f http://localhost:8000/health &> /dev/null; then
        log "✓ 健康检查通过"
    else
        error "健康检查失败"
    fi
}

# 主函数
main() {
    log "========================================"
    log "开始回滚 FeishuMind"
    log "========================================"

    confirm_rollback
    find_backup
    stop_services
    restore_data
    start_services
    health_check

    log "========================================"
    log "回滚完成！"
    log "========================================"
}

# 执行
main
