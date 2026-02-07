#!/bin/bash
# 测试环境设置脚本
#
# 用于快速搭建 FeishuMind 测试环境

set -e

echo "======================================================================"
echo "FeishuMind 测试环境设置"
echo "======================================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 Python 版本
echo -e "${BLUE}1. 检查 Python 版本...${NC}"
if ! command -v python3.12 &> /dev/null; then
    echo "❌ Python 3.12 未安装"
    echo "请先安装 Python 3.12"
    exit 1
fi
echo "✓ Python 3.12 已安装"
python3.12 --version
echo ""

# 检查并创建虚拟环境
echo -e "${BLUE}2. 设置虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3.12 -m venv venv
fi
echo "✓ 虚拟环境已创建"
echo ""

# 激活虚拟环境
echo -e "${BLUE}3. 激活虚拟环境...${NC}"
source venv/bin/activate
echo "✓ 虚拟环境已激活"
echo ""

# 安装依赖
echo -e "${BLUE}4. 安装依赖...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ 依赖安装完成"
echo ""

# 创建必要的目录
echo -e "${BLUE}5. 创建测试目录...${NC}"
mkdir -p test_data/memory
mkdir -p logs
mkdir -p reports
echo "✓ 测试目录已创建"
echo ""

# 复制示例配置
echo -e "${BLUE}6. 配置环境变量...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ 已创建 .env 文件"
    echo "⚠️  请编辑 .env 文件，填入必要的配置"
else
    echo "✓ .env 文件已存在"
fi
echo ""

# 初始化数据库
echo -e "${BLUE}7. 初始化测试数据库...${NC}"
if [ ! -f "test_data/memory/test.db" ]; then
    echo "创建测试数据库..."
    # 数据库会在首次使用时自动创建
    echo "✓ 测试数据库准备完成"
else
    echo "✓ 测试数据库已存在"
fi
echo ""

# 运行测试
echo -e "${BLUE}8. 运行测试套件...${NC}"
read -p "是否运行测试？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3.12 -m pytest tests/unit/ -v --tb=short
    echo "✓ 测试完成"
else
    echo "跳过测试"
fi
echo ""

# 启动服务
echo -e "${BLUE}9. 启动服务...${NC}"
read -p "是否启动服务？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "启动 FeishuMind 服务..."
    echo "服务地址: http://localhost:8000"
    echo "API 文档: http://localhost:8000/docs"
    echo ""
    echo "按 Ctrl+C 停止服务"
    echo ""
    python3.12 -m uvicorn src.api.main:app --reload --port 8000
else
    echo "跳过启动服务"
    echo ""
    echo "手动启动命令:"
    echo "  python3.12 -m uvicorn src.api.main:app --reload --port 8000"
fi
echo ""

# 完成
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}✓ 测试环境设置完成！${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo "下一步:"
echo "  1. 编辑 .env 文件，配置必要的 API Keys"
echo "  2. 运行: python3.12 scripts/run_all_tests.sh"
echo "  3. 启动服务并访问 http://localhost:8000/docs"
echo ""
echo "文档:"
echo "  - 快速开始: docs/quick-start.md"
echo "  - API 文档: docs/spec/02-api-spec.md"
echo ""
