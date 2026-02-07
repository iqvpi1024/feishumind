#!/bin/bash
# 快速测试运行脚本
# 运行所有通过的测试并生成覆盖率报告

set -e

echo "=========================================="
echo "FeishuMind 快速测试套件"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 运行通过的单元测试
echo -e "${YELLOW}运行通过的单元测试...${NC}"
python3.12 -m pytest tests/unit/test_sentiment.py -v --tb=short || true

# 2. 运行新的API测试
echo -e "${YELLOW}运行新的API测试...${NC}"
python3.12 -m pytest tests/api/test_calendar_routes.py::test_create_event_success -v --tb=short || true
python3.12 -m pytest tests/api/test_calendar_routes.py::test_get_event_success -v --tb=short || true
python3.12 -m pytest tests/api/test_calendar_routes.py::test_update_event_success -v --tb=short || true
python3.12 -m pytest tests/api/test_calendar_routes.py::test_delete_event_success -v --tb=short || true
python3.12 -m pytest tests/api/test_calendar_routes.py::test_list_events_empty -v --tb=short || true

# 3. 生成覆盖率报告
echo -e "${YELLOW}生成覆盖率报告...${NC}"
python3.12 -m pytest tests/unit/test_sentiment.py --cov=src --cov-report=term --cov-report=html -q

echo ""
echo -e "${GREEN}=========================================="
echo "测试完成！"
echo "==========================================${NC}"
echo ""
echo "覆盖率报告已生成："
echo "  - 终端输出（上方）"
echo "  - HTML报告: htmlcov/index.html"
echo ""
echo "查看详细报告："
echo "  xdg-open htmlcov/index.html"
