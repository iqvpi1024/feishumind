#!/bin/bash
# FeishuMind cURL 示例
#
# 演示如何使用 cURL 调用 FeishuMind API

BASE_URL="http://localhost:8000"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}FeishuMind cURL 示例${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 健康检查
echo -e "${GREEN}1. 健康检查${NC}"
echo "GET /health"
curl -s "${BASE_URL}/health" | jq '.'
echo ""
echo ""

# 2. 基础对话
echo -e "${GREEN}2. 基础对话${NC}"
echo "POST /api/v1/agent/chat"
curl -s -X POST "${BASE_URL}/api/v1/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，我想了解一下今天的工作安排",
    "context": {
      "user_id": "test_user_001",
      "session_id": "test_session_001"
    }
  }' | jq '.'
echo ""
echo ""

# 3. 创建事件提醒
echo -e "${GREEN}3. 创建事件提醒${NC}"
echo "POST /api/v1/agent/chat"
curl -s -X POST "${BASE_URL}/api/v1/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "提醒我明天下午3点开会",
    "context": {
      "user_id": "test_user_002",
      "session_id": "test_session_002"
    }
  }' | jq '.'
echo ""
echo ""

# 4. 情绪分析
echo -e "${GREEN}4. 情绪分析${NC}"
echo "POST /api/v1/sentiment/analyze"
curl -s -X POST "${BASE_URL}/api/v1/sentiment/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "这周项目压力很大，经常加班到深夜",
    "user_id": "test_user_003"
  }' | jq '.'
echo ""
echo ""

# 5. 获取韧性评分
echo -e "${GREEN}5. 获取韧性评分${NC}"
echo "GET /api/v1/resilience/score/{user_id}"
curl -s -X GET "${BASE_URL}/api/v1/resilience/score/test_user_004" | jq '.'
echo ""
echo ""

# 6. 添加记忆
echo -e "${GREEN}6. 添加记忆${NC}"
echo "POST /memory"
curl -s -X POST "${BASE_URL}/memory" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "preference",
    "content": "我喜欢在早上处理高难度任务",
    "category": "work_habit",
    "metadata": {
      "source": "user_explicit"
    }
  }' | jq '.'
echo ""
echo ""

# 7. 搜索记忆
echo -e "${GREEN}7. 搜索记忆${NC}"
echo "POST /memory/search"
curl -s -X POST "${BASE_URL}/memory/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "工作习惯",
    "limit": 5
  }' | jq '.'
echo ""
echo ""

# 8. GitHub Trending (如果已配置)
echo -e "${GREEN}8. GitHub Trending 推送${NC}"
echo "POST /tasks/github-trending"
curl -s -X POST "${BASE_URL}/tasks/github-trending" \
  -H "Content-Type: application/json" \
  -d '{
    "languages": ["Python", "JavaScript"],
    "min_stars": 100
  }' | jq '.'
echo ""
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}示例完成！${NC}"
echo -e "${BLUE}========================================${NC}"
