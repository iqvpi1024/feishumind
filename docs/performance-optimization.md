# 性能优化指南

本文档介绍 FeishuMind 项目的性能优化策略和最佳实践。

## 目录

1. [性能目标](#性能目标)
2. [优化策略](#优化策略)
3. [缓存机制](#缓存机制)
4. [数据库优化](#数据库优化)
5. [API优化](#api优化)
6. [监控和追踪](#监控和追踪)
7. [最佳实践](#最佳实践)

---

## 性能目标

### 响应时间

| 端点类型 | 目标响应时间 | 最大响应时间 |
|---------|-------------|-------------|
| 健康检查 | < 50ms | < 100ms |
| 情绪分析 | < 200ms | < 500ms |
| 记忆搜索 | < 300ms | < 1000ms |
| Agent对话 | < 500ms | < 2000ms |
| 韧性评分 | < 300ms | < 1000ms |

### 吞吐量

- **目标 QPS**: 100+ queries per second
- **并发支持**: 50+ concurrent requests
- **成功率**: > 99%

### 资源使用

- **内存**: < 500MB (正常运行)
- **CPU**: < 50% (平均负载)
- **数据库连接**: < 20 connections

---

## 优化策略

### 1. 缓存优化

#### 内存缓存

使用 `SimpleCache` 实现内存缓存：

```python
from src.utils.cache import cached

@cached(ttl=300, key_prefix="user_info")
def get_user_info(user_id: str):
    # ... 数据库查询 ...
    return user_data
```

#### 缓存策略

- **TTL（Time To Live）**: 默认 5 分钟
- **LRU（Least Recently Used）**: 自动清理最旧条目
- **容量限制**: 默认 1000 条目

#### 缓存使用场景

| 数据类型 | TTL | 理由 |
|---------|-----|------|
| 用户偏好 | 1小时 | 很少改变 |
| GitHub Trending | 1小时 | 每小时更新 |
| 记忆搜索结果 | 5分钟 | 中等频率变化 |
| 情绪分析结果 | 10分钟 | 短期有效 |

### 2. 异步优化

#### 异步I/O

所有I/O操作使用异步：

```python
async def fetch_data(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

#### 并发处理

使用 `asyncio.gather` 并发执行：

```python
results = await asyncio.gather(
    fetch_data(url1),
    fetch_data(url2),
    fetch_data(url3),
)
```

### 3. 代码优化

#### 减少重复计算

```python
# 不好的做法
for item in items:
    result = expensive_function(item)  # 每次都计算

# 好的做法
cached_result = expensive_function(item)
for item in items:
    result = cached_result
```

#### 使用生成器

```python
# 不好的做法（占用大量内存）
def get_all_items():
    return [item for item in database.query()]

# 好的做法（节省内存）
def get_all_items():
    for item in database.query():
        yield item
```

#### 避免过早优化

- 先实现清晰逻辑
- 使用性能分析工具识别瓶颈
- 针对性优化热点代码

---

## 缓存机制

### SimpleCache 使用

#### 基本用法

```python
from src.utils.cache import get_cache

cache = get_cache()

# 设置缓存
cache.set("key", "value", ttl=60)

# 获取缓存
value = cache.get("key")

# 删除缓存
cache.delete("key")

# 清空缓存
cache.clear()
```

#### 装饰器用法

```python
from src.utils.cache import cached

@cached(ttl=300, key_prefix="expensive_operation")
def expensive_operation(param1, param2):
    # ... 昂贵的计算 ...
    return result
```

### 缓存监控

```python
# 获取缓存统计
stats = cache.get_stats()
print(f"缓存命中率: {stats['hit_rate']:.2%}")
print(f"缓存大小: {stats['size']}/{stats['max_size']}")
```

### 缓存清理

```python
# 定期清理过期条目
expired_count = cache.cleanup_expired()
print(f"清理了 {expired_count} 个过期条目")
```

---

## 数据库优化

### 查询优化

#### 使用索引

```python
# 确保查询字段有索引
# CREATE INDEX idx_user_id ON memories(user_id);
```

#### 限制返回字段

```python
# 不好的做法
memories = db.query("SELECT * FROM memories WHERE user_id = ?", user_id)

# 好的做法
memories = db.query(
    "SELECT id, content, timestamp FROM memories WHERE user_id = ?",
    user_id
)
```

#### 分页查询

```python
def get_memories(user_id: str, page: int, page_size: int = 20):
    offset = page * page_size
    return db.query(
        "SELECT * FROM memories WHERE user_id = ? LIMIT ? OFFSET ?",
        user_id, page_size, offset
    )
```

### 连接池

```python
# 使用连接池避免频繁建立连接
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
)
```

---

## API优化

### 响应优化

#### 压缩响应

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

#### 流式响应

```python
from fastapi.responses import StreamingResponse

async def generate_large_response():
    for item in large_dataset:
        yield json.dumps(item) + "\n"

return StreamingResponse(
    generate_large_response(),
    media_type="application/json",
)
```

### 批量操作

```python
# 不好的做法（多次API调用）
for item in items:
    response = await api.create_item(item)

# 好的做法（批量创建）
response = await api.create_items_batch(items)
```

---

## 监控和追踪

### 请求追踪

#### 使用 RequestContext

```python
from src.utils.monitoring import track_request

with track_request("/api/endpoint", "POST"):
    # ... 处理请求 ...
    pass
```

#### 自动追踪装饰器

```python
from src.utils.monitoring import tracked

@tracked("/api/my_func", "POST")
def my_function():
    return {"success": True}
```

### 性能计时

```python
from src.utils.monitoring import PerformanceTimer

with PerformanceTimer("database_query"):
    # ... 执行查询 ...
    pass
# 自动打印耗时
```

### 慢查询检测

```python
from src.utils.monitoring import slow_query_threshold

@slow_query_threshold(threshold_ms=200)
def query_function():
    # ... 查询操作 ...
    pass
# 如果超过200ms会记录警告
```

### 指标收集

```python
from src.utils.monitoring import get_metrics_collector

collector = get_metrics_collector()

# 获取统计信息
stats = collector.get_stats(endpoint="/api/health", minutes=60)
print(f"平均响应时间: {stats['avg_duration_ms']:.2f}ms")
print(f"P95响应时间: {stats['p95_duration_ms']:.2f}ms")
print(f"错误率: {stats['error_rate']:.2%}")
```

---

## 最佳实践

### 1. 代码层面

#### 使用类型注解

```python
def process_data(user_id: str, data: List[Dict]) -> Dict[str, Any]:
    # ... 处理逻辑 ...
    return result
```

#### 编写文档字符串

```python
def calculate_resilience_score(events: List[Event]) -> float:
    """计算韧性评分。

    Args:
        events: 事件列表

    Returns:
        韧性评分（0-100）

    Raises:
        ValueError: 如果事件列表为空
    """
    # ... 实现 ...
    pass
```

#### 错误处理

```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"操作失败: {e}")
    raise
except Exception as e:
    logger.exception("未知错误")
    raise
```

### 2. 性能测试

#### 使用 pytest-benchmark

```python
import pytest

@pytest.mark.benchmark
def test_memory_search_performance(benchmark):
    result = benchmark(memory_search, query="test")
    assert result is not None
```

#### 负载测试

```python
def test_concurrent_requests():
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(make_request, i)
            for i in range(100)
        ]
        results = [f.result() for f in futures]

    assert all(r.status_code == 200 for r in results)
```

### 3. 监控告警

#### 设置性能阈值

```python
# 响应时间告警
if response_time > 2000:
    send_alert(f"响应时间过长: {response_time}ms")

# 错误率告警
if error_rate > 0.05:
    send_alert(f"错误率过高: {error_rate:.2%}")
```

#### 资源监控

```python
# 内存使用
import psutil
memory_usage = psutil.virtual_memory().percent
if memory_usage > 80:
    send_alert(f"内存使用率过高: {memory_usage}%")

# CPU使用
cpu_usage = psutil.cpu_percent(interval=1)
if cpu_usage > 80:
    send_alert(f"CPU使用率过高: {cpu_usage}%")
```

---

## 性能优化检查清单

### 代码审查

- [ ] 所有I/O操作都是异步的
- [ ] 避免在循环中进行数据库查询
- [ ] 使用缓存减少重复计算
- [ ] 避免过早优化
- [ ] 使用性能分析工具识别瓶颈

### 数据库

- [ ] 查询字段有索引
- [ ] 使用连接池
- [ ] 限制返回字段
- [ ] 使用分页查询
- [ ] 避免N+1查询

### API

- [ ] 响应时间 < 目标值
- [ ] 使用压缩
- [ ] 实现批量操作
- [ ] 合理使用缓存
- [ ] 错误处理完善

### 监控

- [ ] 启用请求追踪
- [ ] 收集性能指标
- [ ] 设置告警阈值
- [ ] 定期检查日志
- [ ] 分析慢查询

---

## 性能分析工具

### cProfile

```bash
python -m cProfile -o profile.stats src/api/main.py
python -m pstats profile.stats
```

### memory_profiler

```bash
pip install memory_profiler
python -m memory_profiler src/api/main.py
```

### pytest-benchmark

```bash
pip install pytest-benchmark
pytest --benchmark-only
```

---

## 总结

性能优化是一个持续的过程：

1. **测量**: 使用工具识别瓶颈
2. **分析**: 找出根本原因
3. **优化**: 实施改进措施
4. **验证**: 确认优化效果
5. **监控**: 持续跟踪性能

记住："过早优化是万恶之源" —— 先确保代码正确，再优化性能。

---

**文档版本**: 1.0
**最后更新**: 2026-02-06
**维护者**: FeishuMind Team
