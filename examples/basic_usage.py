"""
FeishuMind 基础使用示例

演示如何使用 FeishuMind API 进行对话、事件提醒和韧性辅导。
"""

import asyncio
import httpx
from typing import Dict, Any


class FeishuMindClient:
    """FeishuMind API 客户端。"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """初始化客户端。

        Args:
            base_url: API 基础 URL
        """
        self.base_url = base_url

    async def chat(
        self,
        message: str,
        user_id: str = "test_user",
        session_id: str = "test_session",
    ) -> Dict[str, Any]:
        """发送对话消息。

        Args:
            message: 消息内容
            user_id: 用户 ID
            session_id: 会话 ID

        Returns:
            响应数据
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/agent/chat",
                json={
                    "message": message,
                    "context": {
                        "user_id": user_id,
                        "session_id": session_id,
                    }
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def create_event_reminder(
        self,
        title: str,
        time: str,
        user_id: str = "test_user",
    ) -> Dict[str, Any]:
        """创建事件提醒。

        Args:
            title: 事件标题
            time: 事件时间 (自然语言)
            user_id: 用户 ID

        Returns:
            创建结果
        """
        message = f"提醒我{time}{title}"
        return await self.chat(message, user_id)

    async def analyze_emotion(
        self,
        content: str,
        user_id: str = "test_user",
    ) -> Dict[str, Any]:
        """分析情绪和压力。

        Args:
            content: 文本内容
            user_id: 用户 ID

        Returns:
            情绪分析结果
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/sentiment/analyze",
                json={
                    "content": content,
                    "user_id": user_id,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_resilience_score(
        self,
        user_id: str = "test_user",
    ) -> Dict[str, Any]:
        """获取韧性评分。

        Args:
            user_id: 用户 ID

        Returns:
            韧性评分和建议
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/resilience/score/{user_id}",
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()


async def example_basic_chat():
    """示例 1: 基础对话。"""
    print("\n=== 示例 1: 基础对话 ===\n")

    client = FeishuMindClient()

    response = await client.chat(
        message="你好，我想了解一下今天的工作安排",
        user_id="user_001",
    )

    print(f"Agent 回复: {response['data']['response']}")
    print(f"置信度: {response['data'].get('confidence', 0):.2f}")


async def example_event_reminder():
    """示例 2: 创建事件提醒。"""
    print("\n=== 示例 2: 创建事件提醒 ===\n")

    client = FeishuMindClient()

    response = await client.create_event_reminder(
        title="开会",
        time="明天下午3点",
        user_id="user_002",
    )

    print(f"响应: {response['data']['response']}")

    if response['data'].get('actions'):
        print("执行的操作:")
        for action in response['data']['actions']:
            print(f"  - {action['type']}: {action.get('title', '')}")


async def example_emotion_analysis():
    """示例 3: 情绪分析。"""
    print("\n=== 示例 3: 情绪分析 ===\n")

    client = FeishuMindClient()

    response = await client.analyze_emotion(
        content="这周项目压力很大，经常加班到深夜，感觉有点焦虑",
        user_id="user_003",
    )

    data = response['data']
    print(f"主要情绪: {data['dominant_emotion']}")
    print(f"压力等级: {data['stress_level']}")
    print(f"情绪分数: {data['emotion_score']:.2f}")
    print(f"\n识别的压力因素:")
    for factor in data.get('stress_factors', []):
        print(f"  - {factor}")


async def example_resilience_score():
    """示例 4: 韧性评分。"""
    print("\n=== 示例 4: 韧性评分 ===\n")

    client = FeishuMindClient()

    response = await client.get_resilience_score(user_id="user_004")

    data = response['data']
    print(f"韧性评分: {data['resilience_score']:.2f} / 100")
    print(f"评分等级: {data['score_level']}")

    print(f"\n各维度评分:")
    for dimension, score in data['dimension_scores'].items():
        print(f"  - {dimension}: {score:.2f}")

    print(f"\n个性化建议:")
    for recommendation in data.get('recommendations', []):
        print(f"  - {recommendation}")


async def example_multi_turn_conversation():
    """示例 5: 多轮对话。"""
    print("\n=== 示例 5: 多轮对话 ===\n")

    client = FeishuMindClient()
    session_id = "session_005"

    # 第一轮
    print("用户: 我想安排一个会议")
    response1 = await client.chat(
        message="我想安排一个会议",
        user_id="user_005",
        session_id=session_id,
    )
    print(f"Agent: {response1['data']['response']}\n")

    # 第二轮
    print("用户: 明天下午3点")
    response2 = await client.chat(
        message="明天下午3点",
        user_id="user_005",
        session_id=session_id,
    )
    print(f"Agent: {response2['data']['response']}\n")

    # 第三轮
    print("用户: 关于项目进度汇报")
    response3 = await client.chat(
        message="关于项目进度汇报",
        user_id="user_005",
        session_id=session_id,
    )
    print(f"Agent: {response3['data']['response']}")


async def main():
    """主函数。"""
    print("=" * 60)
    print("FeishuMind 使用示例")
    print("=" * 60)

    # 运行示例
    await example_basic_chat()
    await example_event_reminder()
    await example_emotion_analysis()
    await example_resilience_score()
    await example_multi_turn_conversation()

    print("\n" + "=" * 60)
    print("示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
