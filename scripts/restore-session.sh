#!/bin/bash
# FeishuMind 会话恢复辅助脚本
# 用途：快速查看当前项目状态，帮助新会话快速恢复工作

echo "=========================================="
echo "  FeishuMind 会话恢复"
echo "=========================================="
echo ""

# 检查当前状态文件
STATUS_FILE="docs/current-status.md"

if [ ! -f "$STATUS_FILE" ]; then
    echo "❌ 错误：找不到状态文件 $STATUS_FILE"
    echo "建议：阅读 docs/README.md 了解项目结构"
    exit 1
fi

# 提取最后更新时间
LAST_UPDATE=$(grep "最后更新" "$STATUS_FILE" | head -1 | sed 's/.*: //')

echo "📅 最后更新: $LAST_UPDATE"
echo ""

# 提取当前阶段
echo "📍 当前阶段："
grep -A 1 "当前阶段" "$STATUS_FILE" | tail -1
echo ""

# 提取当前任务
echo "🔄 当前任务："
grep -A 1 "当前任务" "$STATUS_FILE" | tail -1
echo ""

# 提取进度
echo "📊 进度："
grep -A 2 "### W1-01:" "$STATUS_FILE" | grep "完成度" || \
grep "完成度" "$STATUS_FILE" | head -1
echo ""

# 显示下一步
echo "➡️  下一步："
grep "下一步行动" -A 10 "$STATUS_FILE" | grep "立即执行" -A 5 | tail -4
echo ""

# 显示快速命令
echo "=========================================="
echo "  快速命令（复制粘贴给 Claude Code）"
echo "=========================================="
echo ""
echo "🔄 继续当前任务："
echo "   继续任务"
echo ""
echo "📋 查看详细进度："
echo "   查看进度"
echo ""
echo "🎯 跳到特定任务："
echo "   跳到 W1-02"
echo ""
echo "📖 阅读所有文档并开始："
echo "   阅读所有文档，继续任务"
echo ""
echo "=========================================="
echo ""
