#!/bin/bash
# 运行所有测试套件
#
# 此脚本运行单元测试、集成测试和性能测试，并生成覆盖率报告。

set -e  # 遇到错误立即退出

echo "======================================================================"
echo "FeishuMind 测试套件"
echo "======================================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 pytest 是否安装
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}✗ pytest 未安装${NC}"
    echo "请运行: pip3 install -r requirements-dev.txt"
    exit 1
fi

# 创建报告目录
mkdir -p reports

echo -e "${GREEN}1. 运行单元测试...${NC}"
pytest tests/unit/ \
    -v \
    --tb=short \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-report=xml:coverage.xml \
    --junitxml=reports/unit-tests.xml

echo ""
echo -e "${GREEN}2. 运行集成测试...${NC}"
pytest tests/integration/ \
    -v \
    --tb=short \
    --junitxml=reports/integration-tests.xml

echo ""
echo -e "${GREEN}3. 运行性能测试...${NC}"
pytest tests/performance/ \
    -v \
    --tb=short \
    --junitxml=reports/performance-tests.xml

echo ""
echo -e "${GREEN}4. 生成测试报告...${NC}"

# 统计测试结果
echo "======================================================================"
echo "测试报告摘要"
echo "======================================================================"

# 提取测试统计
if [ -f reports/unit-tests.xml ]; then
    echo "单元测试: 已生成报告 reports/unit-tests.xml"
fi

if [ -f reports/integration-tests.xml ]; then
    echo "集成测试: 已生成报告 reports/integration-tests.xml"
fi

if [ -f reports/performance-tests.xml ]; then
    echo "性能测试: 已生成报告 reports/performance-tests.xml"
fi

if [ -f coverage.xml ]; then
    echo "覆盖率报告: 已生成 coverage.xml 和 htmlcov/"
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}✓ 所有测试完成！${NC}"
echo "======================================================================"
echo ""
echo "查看覆盖率报告:"
echo "  - HTML: open htmlcov/index.html"
echo "  - XML: cat coverage.xml"
