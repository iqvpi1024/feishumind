"""
GitHub API 客户端

提供 GitHub Trending 数据获取功能。
使用 httpx 进行异步 HTTP 请求。

Author: FeishuMind Team
Created: 2026-02-06
"""

import asyncio
from datetime import datetime
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup

from src.integrations.github.models import GitHubRepo
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GitHubClient:
    """
    GitHub API 客户端

    获取 GitHub Trending 数据，支持语言和时间段过滤。

    Attributes:
        timeout: 请求超时时间
        max_retries: 最大重试次数
    """

    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """初始化 GitHub 客户端

        Args:
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = "https://github.com"
        self.trending_url = f"{self.base_url}/trending"

    async def get_trending_repos(
        self,
        language: Optional[str] = None,
        period: str = "daily",
        limit: int = 10,
    ) -> List[GitHubRepo]:
        """获取 GitHub Trending 仓库

        通过爬取 GitHub Trending 页面获取热门仓库。

        Args:
            language: 编程语言过滤 (如: Python, JavaScript)
            period: 时间周期 (daily, weekly, monthly)
            limit: 返回数量限制

        Returns:
            仓库列表

        Raises:
            ValueError: 参数无效
            httpx.HTTPError: HTTP 请求失败
        """
        # 参数验证
        if period not in ["daily", "weekly", "monthly"]:
            raise ValueError(f"Invalid period: {period}. Must be one of: daily, weekly, monthly")

        if not (1 <= limit <= 50):
            raise ValueError("Limit must be between 1 and 50")

        # 构建 URL
        url = self._build_trending_url(language, period)

        logger.info(f"Fetching GitHub Trending: {url}")

        # 重试机制
        for attempt in range(self.max_retries):
            try:
                repos = await self._fetch_trending_page(url, limit)
                logger.info(f"Successfully fetched {len(repos)} trending repos")
                return repos

            except httpx.HTTPError as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指数退避

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise

        return []

    def _build_trending_url(self, language: Optional[str], period: str) -> str:
        """构建 Trending URL

        Args:
            language: 编程语言
            period: 时间周期

        Returns:
            完整 URL
        """
        url = self.trending_url

        # 添加语言过滤
        if language:
            # 将语言转换为 URL 格式 (如: C++ -> cplusplus)
            lang_map = {
                "C++": "cplusplus",
                "C#": "csharp",
                "F#": "fsharp",
                "Objective-C": "objective-c",
                "Common Lisp": "common-lisp",
            }
            lang = lang_map.get(language, language.lower().replace(" ", "-"))
            url = f"{url}/{lang}"

        # 添加时间周期
        since_map = {
            "daily": "daily",
            "weekly": "weekly",
            "monthly": "monthly",
        }
        since = since_map.get(period, "daily")
        url = f"{url}?since={since}"

        return url

    async def _fetch_trending_page(self, url: str, limit: int) -> List[GitHubRepo]:
        """爬取 Trending 页面

        Args:
            url: Trending 页面 URL
            limit: 返回数量限制

        Returns:
            仓库列表

        Raises:
            httpx.HTTPError: HTTP 请求失败
        """
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

            # 解析 HTML
            soup = BeautifulSoup(response.text, "html.parser")
            repos = []

            # 查找所有仓库条目
            articles = soup.find_all("article", class_="Box-row")
            if not articles:
                logger.warning("No repositories found on trending page")
                return []

            for article in articles[:limit]:
                try:
                    repo = self._parse_repo_article(article)
                    if repo:
                        repos.append(repo)
                except Exception as e:
                    logger.warning(f"Failed to parse repo: {e}")
                    continue

            return repos

    def _parse_repo_article(self, article) -> Optional[GitHubRepo]:
        """解析单个仓库条目

        Args:
            article: BeautifulSoup 元素

        Returns:
            GitHubRepo 对象，解析失败返回 None
        """
        try:
            # 获取仓库链接
            repo_link = article.find("a", class_="")
            if not repo_link:
                return None

            full_name = repo_link.get("href", "").lstrip("/")
            if "/" not in full_name:
                return None

            owner, name = full_name.split("/", 1)

            # 获取描述
            desc_elem = article.find("p", class_="col-9")
            description = desc_elem.get_text(strip=True) if desc_elem else None

            # 获取编程语言
            lang_elem = article.find("span", itemprop="programmingLanguage")
            language = lang_elem.get_text(strip=True) if lang_elem else None

            # 获取星标数和分支数
            stars_elem = article.find("a", href=lambda x: x and "/stargazers" in x)
            forks_elem = article.find("a", href=lambda x: x and "/forks" in x)

            stars = self._parse_number(stars_elem.get_text(strip=True)) if stars_elem else 0
            forks = self._parse_number(forks_elem.get_text(strip=True)) if forks_elem else 0

            # 获取头像
            avatar_elem = article.find("img", class_="avatar")
            avatar_url = avatar_elem.get("src") if avatar_elem else None

            # 构建仓库对象
            repo = GitHubRepo(
                repo_id=full_name,
                name=name,
                full_name=full_name,
                description=description,
                language=language,
                stars=stars,
                forks=forks,
                url=f"https://github.com/{full_name}",
                owner=owner,
                avatar_url=avatar_url,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            return repo

        except Exception as e:
            logger.warning(f"Failed to parse repo article: {e}")
            return None

    def _parse_number(self, text: str) -> int:
        """解析数字文本

        将 "1.2k" 转换为 1200

        Args:
            text: 数字文本

        Returns:
            整数
        """
        text = text.strip().replace(",", "")

        if text.endswith("k"):
            return int(float(text[:-1]) * 1000)
        elif text.endswith("m"):
            return int(float(text[:-1]) * 1000000)
        else:
            return int(text)

    async def get_repo_details(self, owner: str, repo_name: str) -> Optional[GitHubRepo]:
        """获取仓库详细信息

        Args:
            owner: 所有者名称
            repo_name: 仓库名称

        Returns:
            GitHubRepo 对象，不存在返回 None
        """
        url = f"{self.base_url}/{owner}/{repo_name}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # 解析仓库详情 (简化版)
                stars_elem = soup.find("a", href=lambda x: x and "/stargazers" in x)
                forks_elem = soup.find("a", href=lambda x: x and "/forks" in x)

                stars = self._parse_number(stars_elem.get_text(strip=True)) if stars_elem else 0
                forks = self._parse_number(forks_elem.get_text(strip=True)) if forks_elem else 0

                repo = GitHubRepo(
                    repo_id=f"{owner}/{repo_name}",
                    name=repo_name,
                    full_name=f"{owner}/{repo_name}",
                    url=url,
                    owner=owner,
                    stars=stars,
                    forks=forks,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )

                return repo

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch repo details: {e}")
            return None
