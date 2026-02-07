#!/usr/bin/env python3
"""依赖检查脚本。

验证所有必需的Python包是否正确安装，并检查版本兼容性。
"""

import sys
from typing import List, Tuple, Dict
import importlib


def check_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """检查单个包是否可导入。

    Args:
        package_name: 包名（用于显示）
        import_name: 导入名（如果与包名不同）

    Returns:
        (是否成功, 版本信息或错误消息)
    """
    if import_name is None:
        import_name = package_name

    try:
        module = importlib.import_module(import_name)
        version = getattr(module, "__version__", "unknown")
        return True, version
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {e}"


def main():
    """主函数。"""
    # 定义所有必需的包
    required_packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
        ("langgraph", "langgraph"),
        ("langchain", "langchain"),
        ("httpx", "httpx"),
        ("python-jose", "jose"),
        ("passlib", "passlib"),
        ("dotenv", "dotenv"),
        ("loguru", "loguru"),
        ("tenacity", "tenacity"),
        ("apscheduler", "apscheduler"),
        ("python-dateutil", "dateutil"),
        ("jieba", "jieba"),
        ("beautifulsoup4", "bs4"),
        ("lxml", "lxml"),
    ]

    print("=" * 60)
    print("FeishuMind 依赖检查")
    print("=" * 60)
    print()

    all_passed = True
    results = []

    for package_name, import_name in required_packages:
        success, info = check_package(package_name, import_name)
        status = "✓" if success else "✗"
        results.append((package_name, success, info))

        if success:
            print(f"{status} {package_name:25s} - 版本: {info}")
        else:
            print(f"{status} {package_name:25s} - 失败: {info}")
            all_passed = False

    print()
    print("=" * 60)

    if all_passed:
        print("✓ 所有依赖检查通过！")
        return 0
    else:
        failed_count = sum(1 for _, success, _ in results if not success)
        print(f"✗ {failed_count} 个依赖检查失败")
        print("\n请运行: pip3 install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
