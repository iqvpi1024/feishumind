# FeishuMind 开发规范

**版本**: 1.0.0
**最后更新**: 2026-02-06
**适用范围**: 全部代码仓库

## 🐍 Python 代码规范

### 基础规范

遵循 **PEP 8** 标准，使用 **Black** 格式化，**isort** 排序导入。

```python
# ✅ 正确示例
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from langchain.agents import AgentExecutor

from src.memory.config import MemoryConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MemoryManager:
    """记忆管理器类。

    负责用户记忆的增删改查，支持精确和模糊检索。

    Attributes:
        config: Mem0 配置对象
    """

    def __init__(self, config: MemoryConfig) -> None:
        """初始化记忆管理器。

        Args:
            config: 记忆配置对象
        """
        self.config = config
        self._client = None

    async def add_memory(
        self,
        content: str,
        category: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """添加记忆。

        Args:
            content: 记忆内容
            category: 记忆类别 (preference|emotion|event)
            metadata: 额外元数据

        Returns:
            记忆ID

        Raises:
            ValueError: 内容为空或类别无效
        """
        if not content.strip():
            raise ValueError("Memory content cannot be empty")

        if category not in ["preference", "emotion", "event"]:
            raise ValueError(f"Invalid category: {category}")

        # 实现逻辑...
        return "mem_xxx"
```

### 类型注解

**强制要求**: 所有公开接口必须使用类型注解。

```python
from typing import List, Dict, Optional, Union

# ✅ 使用类型注解
def search_memories(
    query: str,
    limit: int = 10,
    filters: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Union[str, float]]]:
    """检索记忆。"""
    pass

# ❌ 避免
def search_memories(query, limit=10, filters=None):
    pass
```

### 异常处理

```python
# ✅ 明确捕获异常
try:
    result = await api_call()
except APIError as e:
    logger.error(f"API call failed: {e}")
    raise
except Exception as e:
    logger.critical(f"Unexpected error: {e}")
    raise

# ❌ 避免裸 except
try:
    result = api_call()
except:
    pass
```

### 异步编程

- **I/O 密集型操作** 必须使用 `async/await`
- **CPU 密集型操作** 使用线程池 `run_in_executor`

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AgentService:
    async def process_message(self, message: str) -> dict:
        """异步处理消息。"""
        # I/O 操作
        memories = await self.memory.search(message)

        # CPU 密集型
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                self.heavy_computation,
                memories,
            )

        return result
```

## 🧪 测试规范

### 单元测试

使用 **pytest**，覆盖率目标 **>80%**。

```python
# tests/unit/test_memory.py
import pytest
from src.memory import MemoryManager

@pytest.fixture
def memory_manager():
    """测试夹具：记忆管理器实例。"""
    return MemoryManager(test_config)

@pytest.mark.asyncio
async def test_add_memory(memory_manager):
    """测试添加记忆。"""
    memory_id = await memory_manager.add_memory(
        content="测试记忆",
        category="preference",
    )

    assert memory_id is not None
    assert memory_id.startswith("mem_")

@pytest.mark.asyncio
async def test_add_empty_memory(memory_manager):
    """测试添加空记忆应抛出异常。"""
    with pytest.raises(ValueError):
        await memory_manager.add_memory(
            content="",
            category="preference",
        )
```

### 集成测试

```python
# tests/integration/test_agent_flow.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_chat_flow(client: AsyncClient):
    """测试完整对话流程。"""
    response = await client.post(
        "/agent/chat",
        json={"message": "提醒我明天开会"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "actions" in data["data"]
```

### 测试命名

- 文件名: `test_<module>.py`
- 类名: `Test<ClassName>`
- 方法名: `test_<specific_behavior>`

## 📝 文档规范

### Docstring 格式

使用 **Google Style** Docstring。

```python
def generate_weekly_report(
    user_id: str,
    week_start: str,
    include_metrics: bool = True,
) -> dict:
    """生成周报。

    根据用户一周的活动记录和情绪曲线，生成结构化周报。

    Args:
        user_id: 飞书用户ID
        week_start: 周开始日期 (YYYY-MM-DD)
        include_metrics: 是否包含量化指标

    Returns:
        包含周报内容的字典:
        {
            "summary": "本周概要",
            "highlights": ["重点1", "重点2"],
            "emotion_curve": [...],
            "recommendations": [...]
        }

    Raises:
        ValueError: 日期格式错误
        APIError: 飞书API调用失败

    Examples:
        >>> report = generate_weekly_report(
        ...     user_id="ou_xxx",
        ...     week_start="2026-02-01"
        ... )
        >>> print(report["summary"])
    """
    pass
```

### 注释规范

```python
# ✅ 好的注释：解释"为什么"
# 使用 FAISS 而非 Pinecone，因为本地隐私要求
vector_store = FAISSIndex(embeddings)

# ❌ 差的注释：重复代码
# 初始化向量存储
vector_store = FAISSIndex(embeddings)

# ✅ TODO 注释
# TODO: 实现 Token 池避免单用户消耗过多
# 跟踪 Issue: #123

# ✅ FIXME 注释
# FIXME: 临时禁用反馈闭环，待 Mem0 升级后恢复
# score_threshold = 0.8  # 恢复为 0.8
score_threshold = 1.0
```

## 🔐 安全规范

### 敏感数据处理

```python
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ 使用环境变量
api_key = os.getenv("FEISHU_API_KEY")
if not api_key:
    raise ValueError("FEISHU_API_KEY not set")

# ❌ 禁止硬编码
# api_key = "cli_xxxx"

# ✅ 脱敏日志
logger.info(f"API call for user {user_id[:4]}***")
# 而非
logger.info(f"API call for user {user_id}")
```

### 输入验证

```python
from pydantic import BaseModel, validator

class CreateMemoryRequest(BaseModel):
    """创建记忆请求模型。"""

    content: str
    category: str

    @validator('content')
    def content_not_empty(cls, v):
        """验证内容非空。"""
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v

    @validator('category')
    def category_valid(cls, v):
        """验证类别有效。"""
        allowed = ['preference', 'emotion', 'event']
        if v not in allowed:
            raise ValueError(f'Category must be one of {allowed}')
        return v
```

## 🏗️ 项目结构规范

### 模块导入顺序

```python
# 1. 标准库
import os
from datetime import datetime

# 2. 第三方库
from fastapi import FastAPI
from langchain import PromptTemplate

# 3. 本地模块
from src.memory import MemoryManager
from src.utils import config
```

### 配置管理

```python
# src/utils/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    """应用配置。"""

    # 应用基础配置
    APP_NAME: str = "FeishuMind"
    DEBUG: bool = False
    VERSION: str = "1.0.0"

    # 飞书配置
    FEISHU_APP_ID: str
    FEISHU_APP_SECRET: str

    # AI 模型配置
    CLAUDE_API_KEY: str
    MAX_TOKENS_PER_USER: int = 5000

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./feishumind.db"

    class Config:
        """配置加载。"""
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## 🚀 Git 提交规范

### Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响逻辑）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 示例

```bash
# ✅ 好的提交
feat(agent): add GitHub trending skill

- Implement daily GitHub trending fetch
- Add user preference filtering
- Integrate with n8n workflow

Closes #123

# ❌ 差的提交
update code
fix bugs
```

## 📦 依赖管理

使用 **Poetry** 管理依赖。

```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.12"
fastapi = "^0.104.0"
langchain = "^0.1.0"
mem0ai = "^0.1.0"

[tool.poetry.dev-dependencies]
pytest = "^7.4.0"
black = "^23.12.0"
isort = "^5.13.0"
mypy = "^1.7.0"

[tool.black]
line-length = 88
target-version = ['py312']

[tool.isort]
profile = "black"
line_length = 88
```

## 🎯 Claude Code 使用规范

### Prompt 模板

```markdown
You are a senior Python engineer building FeishuMind.

Context:
- We are using FastAPI + LangGraph + Mem0
- Follow PEP 8 and type hints
- Add docstrings in Google Style
- Include error handling and logging

Task: {具体任务}

Requirements:
{具体要求}

Output:
- Code with file paths
- Brief explanation of changes
- Testing suggestions
```

### 审查清单

提交代码前检查：
- [ ] 代码通过 Black 格式化
- [ ] 类型注解完整（mypy 检查）
- [ ] 单元测试覆盖率 >80%
- [ ] Docstring 完整
- [ ] 敏感信息已移除
- [ ] 日志级别适当
- [ ] 异常处理完善

---

**参考资源**:
- [PEP 8 官方文档](https://peps.python.org/pep-0008/)
- [FastAPI 最佳实践](https://fastapi.tiangolo.com/tutorial/)
- [Pytest 文档](https://docs.pytest.org/)
