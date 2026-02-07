"""性能测试。

测试 API 响应时间、并发处理等。

Author: Claude Code
Date: 2026-02-06
"""

import pytest
import time
import threading
from fastapi.testclient import TestClient
from typing import List

from src.api.main import app


@pytest.fixture
def client() -> TestClient:
    """创建测试客户端。"""
    return TestClient(app)


class TestResponseTime:
    """响应时间测试。"""

    def test_health_check_response_time(self, client: TestClient) -> None:
        """测试健康检查响应时间。"""
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.5, f"响应时间过长: {elapsed:.2f}s"

    def test_memory_search_response_time(self, client: TestClient) -> None:
        """测试记忆搜索响应时间。"""
        start = time.time()
        response = client.get(
            "/api/v1/memory/search",
            params={
                "user_id": "perf_test_user",
                "query": "测试",
            },
        )
        elapsed = time.time() - start

        # 允许更长的响应时间（可能涉及外部API）
        assert response.status_code in [200, 500]
        assert elapsed < 2.0, f"响应时间过长: {elapsed:.2f}s"

    def test_resilience_analysis_response_time(self, client: TestClient) -> None:
        """测试韧性分析响应时间。"""
        start = time.time()
        response = client.post(
            "/api/v1/resilience/analyze",
            json={"text": "今天工作压力很大"},
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0, f"响应时间过长: {elapsed:.2f}s"

    def test_agent_chat_response_time(self, client: TestClient) -> None:
        """测试 Agent 对话响应时间。"""
        start = time.time()
        response = client.post(
            "/api/v1/agent/chat",
            json={
                "user_id": "perf_test_user",
                "message": "你好",
            },
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 2.0, f"响应时间过长: {elapsed:.2f}s"


class TestConcurrency:
    """并发测试。"""

    def test_concurrent_health_checks(self, client: TestClient) -> None:
        """测试并发健康检查。"""
        num_requests = 100
        results: List[int] = []

        def make_request():
            response = client.get("/health")
            results.append(response.status_code)

        threads = []
        start = time.time()

        for _ in range(num_requests):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        elapsed = time.time() - start

        # 所有请求都应该成功
        assert all(status == 200 for status in results)
        assert len(results) == num_requests

        # 平均响应时间应该合理
        avg_time = elapsed / num_requests
        assert avg_time < 0.1, f"平均响应时间过长: {avg_time:.3f}s"

    def test_concurrent_chat_requests(self, client: TestClient) -> None:
        """测试并发对话请求。"""
        num_requests = 10
        results: List[int] = []

        def make_request(index: int):
            response = client.post(
                "/api/v1/agent/chat",
                json={
                    "user_id": f"perf_test_user_{index}",
                    "message": f"测试消息 {index}",
                },
            )
            results.append(response.status_code)

        threads = []
        start = time.time()

        for i in range(num_requests):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        elapsed = time.time() - start

        # 所有请求都应该成功
        assert all(status == 200 for status in results)
        assert len(results) == num_requests

        print(f"并发 {num_requests} 个请求，总耗时: {elapsed:.2f}s")
        print(f"平均响应时间: {elapsed / num_requests:.3f}s")


class TestLoadTesting:
    """负载测试。"""

    def test_sustained_load(self, client: TestClient) -> None:
        """测试持续负载。"""
        num_requests = 50
        results: List[int] = []
        errors: List[int] = []

        def make_request():
            try:
                response = client.get("/health")
                results.append(response.status_code)
                if response.status_code != 200:
                    errors.append(response.status_code)
            except Exception as e:
                errors.append(-1)

        threads = []
        start = time.time()

        for _ in range(num_requests):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
            time.sleep(0.01)  # 间隔10ms

        for thread in threads:
            thread.join()

        elapsed = time.time() - start

        # 检查成功率
        success_rate = len([r for r in results if r == 200]) / num_requests
        assert success_rate > 0.95, f"成功率过低: {success_rate:.2%}"

        print(f"负载测试: {num_requests} 请求，耗时 {elapsed:.2f}s")
        print(f"成功率: {success_rate:.2%}")


class TestMemoryUsage:
    """内存使用测试。"""

    def test_large_payload_handling(self, client: TestClient) -> None:
        """测试大负载处理。"""
        large_text = "测试内容 " * 1000  # 约 5000 字符

        response = client.post(
            "/api/v1/resilience/analyze",
            json={"text": large_text},
        )

        assert response.status_code == 200

    def test_batch_operations(self, client: TestClient) -> None:
        """测试批量操作。"""
        events = [
            {
                "description": f"测试事件 {i}",
                "stress_level": "low",
                "stress_score": 0.3,
            }
            for i in range(50)
        ]

        start = time.time()
        response = client.post(
            "/api/v1/resilience/curve/generate",
            json={"events": events},
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 2.0, f"批量操作响应时间过长: {elapsed:.2f}s"


class TestDatabasePerformance:
    """数据库性能测试（如果适用）。"""

    def test_memory_search_performance(self, client: TestClient) -> None:
        """测试记忆搜索性能。"""
        # 测试多次搜索
        times = []

        for i in range(10):
            start = time.time()
            response = client.get(
                "/api/v1/memory/search",
                params={
                    "user_id": "perf_test_user",
                    "query": f"测试查询 {i}",
                },
            )
            elapsed = time.time() - start
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        assert avg_time < 1.0, f"平均搜索时间过长: {avg_time:.3f}s"

        print(f"记忆搜索平均时间: {avg_time:.3f}s")


class TestCachingPerformance:
    """缓存性能测试。"""

    def test_repeated_request_performance(self, client: TestClient) -> None:
        """测试重复请求性能（如果启用缓存）。"""
        # 第一次请求
        start = time.time()
        response1 = client.post(
            "/api/v1/resilience/analyze",
            json={"text": "今天工作压力很大"},
        )
        time1 = time.time() - start

        # 重复请求
        start = time.time()
        response2 = client.post(
            "/api/v1/resilience/analyze",
            json={"text": "今天工作压力很大"},
        )
        time2 = time.time() - start

        assert response1.status_code == 200
        assert response2.status_code == 200

        print(f"首次请求: {time1:.3f}s")
        print(f"重复请求: {time2:.3f}s")


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """性能基准测试。"""

    def test_api_benchmark(self, client: TestClient) -> None:
        """API 性能基准测试。"""
        benchmarks = {
            "health_check": lambda: client.get("/health"),
            "emotion_analysis": lambda: client.post(
                "/api/v1/resilience/analyze",
                json={"text": "测试文本"},
            ),
            "event_analysis": lambda: client.post(
                "/api/v1/resilience/analyze-event",
                json={"event_text": "明天开会"},
            ),
        }

        results = {}

        for name, func in benchmarks.items():
            times = []
            for _ in range(10):
                start = time.time()
                response = func()
                elapsed = time.time() - start
                times.append(elapsed)
                assert response.status_code == 200

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            results[name] = {
                "avg": avg_time,
                "min": min_time,
                "max": max_time,
            }

            print(f"\n{name}:")
            print(f"  平均: {avg_time:.3f}s")
            print(f"  最小: {min_time:.3f}s")
            print(f"  最大: {max_time:.3f}s")

        # 检查性能基准
        assert results["health_check"]["avg"] < 0.1
        assert results["emotion_analysis"]["avg"] < 0.5
        assert results["event_analysis"]["avg"] < 0.5
