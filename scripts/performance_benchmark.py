#!/usr/bin/env python3
"""性能基准测试脚本。

测试各个API端点的响应时间和吞吐量。
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import httpx
from loguru import logger


class PerformanceBenchmark:
    """性能基准测试类。

    测试API端点的响应时间、吞吐量和并发性能。
    """

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        """初始化基准测试。

        Args:
            base_url: API基础URL
        """
        self.base_url = base_url
        self.results: Dict[str, List[float]] = {}

    async def test_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Dict[str, Any] = None,
        iterations: int = 10,
    ) -> Dict[str, Any]:
        """测试单个端点的性能。

        Args:
            endpoint: API端点路径
            method: HTTP方法
            payload: 请求负载
            iterations: 测试迭代次数

        Returns:
            性能统计信息
        """
        url = f"{self.base_url}{endpoint}"
        response_times: List[float] = []
        errors: int = 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(iterations):
                try:
                    start_time = time.time()

                    if method == "GET":
                        response = await client.get(url)
                    elif method == "POST":
                        response = await client.post(url, json=payload)
                    else:
                        raise ValueError(f"不支持的HTTP方法: {method}")

                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # 转换为毫秒

                    response_times.append(response_time)

                    logger.info(f"{method} {endpoint} - {response_time:.2f}ms - 状态码:{response.status_code}")

                except Exception as e:
                    errors += 1
                    logger.error(f"请求失败: {method} {endpoint} - 错误: {e}")

        # 计算统计数据
        if response_times:
            stats = {
                "endpoint": endpoint,
                "method": method,
                "iterations": iterations,
                "errors": errors,
                "min_ms": round(min(response_times), 2),
                "max_ms": round(max(response_times), 2),
                "mean_ms": round(statistics.mean(response_times), 2),
                "median_ms": round(statistics.median(response_times), 2),
                "stdev_ms": round(statistics.stdev(response_times), 2) if len(response_times) > 1 else 0,
                "p95_ms": round(statistics.quantiles(response_times, n=20)[18], 2) if len(response_times) > 1 else response_times[0],
                "p99_ms": round(statistics.quantiles(response_times, n=100)[98], 2) if len(response_times) > 1 else response_times[0],
                "success_rate": round((iterations - errors) / iterations * 100, 2),
            }
        else:
            stats = {
                "endpoint": endpoint,
                "method": method,
                "iterations": iterations,
                "errors": errors,
                "success_rate": 0,
            }

        self.results[f"{method} {endpoint}"] = stats
        return stats

    async def test_concurrent_requests(
        self,
        endpoint: str,
        method: str = "GET",
        concurrent_users: int = 10,
        requests_per_user: int = 10,
    ) -> Dict[str, Any]:
        """测试并发请求性能。

        Args:
            endpoint: API端点路径
            method: HTTP方法
            concurrent_users: 并发用户数
            requests_per_user: 每个用户的请求数

        Returns:
            并发性能统计
        """
        url = f"{self.base_url}{endpoint}"
        total_requests = concurrent_users * requests_per_user
        response_times: List[float] = []
        errors: int = 0

        async def make_requests(user_id: int) -> List[float]:
            """单个用户的请求序列。"""
            user_response_times: List[float] = []
            async with httpx.AsyncClient(timeout=30.0) as client:
                for i in range(requests_per_user):
                    try:
                        start_time = time.time()

                        if method == "GET":
                            response = await client.get(url)
                        elif method == "POST":
                            response = await client.post(url, json={})
                        else:
                            raise ValueError(f"不支持的HTTP方法: {method}")

                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000
                        user_response_times.append(response_time)

                        logger.debug(f"用户{user_id} 请求{i+1}/{requests_per_user} - {response_time:.2f}ms")

                    except Exception as e:
                        nonlocal errors
                        errors += 1
                        logger.error(f"用户{user_id} 请求失败: {e}")

            return user_response_times

        # 并发执行
        start_time = time.time()
        tasks = [make_requests(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # 合并结果
        for user_times in results:
            response_times.extend(user_times)

        # 计算统计数据
        total_duration = end_time - start_time
        throughput = total_requests / total_duration if total_duration > 0 else 0

        if response_times:
            stats = {
                "endpoint": endpoint,
                "method": method,
                "concurrent_users": concurrent_users,
                "requests_per_user": requests_per_user,
                "total_requests": total_requests,
                "total_duration_s": round(total_duration, 2),
                "throughput_rps": round(throughput, 2),
                "errors": errors,
                "min_ms": round(min(response_times), 2),
                "max_ms": round(max(response_times), 2),
                "mean_ms": round(statistics.mean(response_times), 2),
                "median_ms": round(statistics.median(response_times), 2),
                "p95_ms": round(statistics.quantiles(response_times, n=20)[18], 2),
                "success_rate": round((total_requests - errors) / total_requests * 100, 2),
            }
        else:
            stats = {
                "endpoint": endpoint,
                "total_requests": total_requests,
                "errors": errors,
                "success_rate": 0,
            }

        logger.info(f"并发测试完成: {concurrent_users}用户 x {requests_per_user}请求")
        logger.info(f"总耗时: {total_duration:.2f}秒, 吞吐量: {throughput:.2f} RPS")

        return stats

    def print_report(self) -> None:
        """打印性能测试报告。"""
        print("\n" + "=" * 80)
        print("性能基准测试报告")
        print("=" * 80)

        for test_name, stats in self.results.items():
            print(f"\n测试: {test_name}")
            print("-" * 80)

            if "mean_ms" in stats:
                print(f"  平均响应时间: {stats['mean_ms']:.2f}ms")
                print(f"  中位数响应时间: {stats['median_ms']:.2f}ms")
                print(f"  P95响应时间: {stats['p95_ms']:.2f}ms")
                print(f"  P99响应时间: {stats['p99_ms']:.2f}ms")
                print(f"  最小/最大: {stats['min_ms']:.2f}ms / {stats['max_ms']:.2f}ms")
                print(f"  标准差: {stats['stdev_ms']:.2f}ms")

            if "throughput_rps" in stats:
                print(f"  吞吐量: {stats['throughput_rps']:.2f} RPS")
                print(f"  并发用户: {stats['concurrent_users']}")
                print(f"  总请求数: {stats['total_requests']}")

            print(f"  成功率: {stats['success_rate']:.2f}%")
            print(f"  错误数: {stats['errors']}")

        print("\n" + "=" * 80)


async def main():
    """主函数：运行所有性能测试。"""
    benchmark = PerformanceBenchmark()

    print("开始性能基准测试...")
    print("确保服务已启动: uvicorn src.api.main:app")

    # 测试健康检查端点
    print("\n[1/5] 测试健康检查端点...")
    await benchmark.test_endpoint("/health", iterations=20)

    # 测试GitHub Trending端点
    print("\n[2/5] 测试GitHub Trending端点...")
    await benchmark.test_endpoint("/api/v1/github/trending?language=Python&limit=5", iterations=10)

    # 测试记忆搜索端点
    print("\n[3/5] 测试记忆搜索端点...")
    await benchmark.test_endpoint(
        "/memory/search",
        method="POST",
        payload={"query": "工作", "limit": 10},
        iterations=10,
    )

    # 测试并发性能
    print("\n[4/5] 测试健康检查并发性能...")
    await benchmark.test_concurrent_requests(
        "/health",
        concurrent_users=50,
        requests_per_user=10,
    )

    # 测试Agent对话并发性能
    print("\n[5/5] 测试Agent对话并发性能...")
    await benchmark.test_concurrent_requests(
        "/api/v1/agent/chat",
        method="POST",
        concurrent_users=10,
        requests_per_user=5,
    )

    # 打印报告
    benchmark.print_report()

    print("\n测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
