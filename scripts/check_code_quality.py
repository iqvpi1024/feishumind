#!/usr/bin/env python3
"""代码质量检查脚本。

运行 black, mypy 和 pylint 检查，生成质量报告。
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str) -> int:
    """运行命令并返回退出码。"""
    print(f"\n{'=' * 60}")
    print(f"运行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print('=' * 60)

    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def check_black() -> int:
    """检查代码格式。"""
    print("\n🎨 检查代码格式 (black)...")

    # 检查是否安装了 black
    try:
        subprocess.run(
            ["black", "--version"],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  black 未安装，跳过格式检查")
        print("   安装: pip3 install black")
        return 0

    # 运行 black 检查（不修改文件）
    return run_command(
        ["black", "--check", "--diff", "src/"],
        "black 格式检查",
    )


def check_mypy() -> int:
    """检查类型注解。"""
    print("\n🔍 检查类型注解 (mypy)...")

    # 检查是否安装了 mypy
    try:
        subprocess.run(
            ["mypy", "--version"],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  mypy 未安装，跳过类型检查")
        print("   安装: pip3 install mypy")
        return 0

    # 运行 mypy
    return run_command(
        [
            "mypy",
            "src/",
            "--ignore-missing-imports",
            "--no-strict-optional",
            "--warn-redundant-casts",
            "--warn-unused-ignores",
            "--warn-return-any",
        ],
        "mypy 类型检查",
    )


def check_pylint() -> int:
    """检查代码质量。"""
    print("\n📊 检查代码质量 (pylint)...")

    # 检查是否安装了 pylint
    try:
        subprocess.run(
            ["pylint", "--version"],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  pylint 未安装，跳过质量检查")
        print("   安装: pip3 install pylint")
        return 0

    # 运行 pylint
    return run_command(
        [
            "pylint",
            "src/",
            "--output-format=text",
            "--max-line-length=88",
            "--disable=C0111,C0103,R0903",
        ],
        "pylint 代码检查",
    )


def check_imports() -> int:
    """检查是否可以导入所有模块。"""
    print("\n📦 检查模块导入...")

    modules_to_check = [
        "src.api.main",
        "src.memory.config",
        "src.memory.client",
        "src.agent.graph",
        "src.agent.state",
        "src.agent.tools",
        "src.integrations.feishu.client",
    ]

    failed = []
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except Exception as e:
            print(f"  ✗ {module}: {e}")
            failed.append(module)

    if failed:
        print(f"\n✗ {len(failed)} 个模块导入失败")
        return 1
    else:
        print("\n✓ 所有模块导入成功")
        return 0


def main():
    """主函数。"""
    print("=" * 60)
    print("FeishuMind 代码质量检查")
    print("=" * 60)

    results = {
        "格式检查 (black)": check_black(),
        "类型检查 (mypy)": check_mypy(),
        "质量检查 (pylint)": check_pylint(),
        "模块导入": check_imports(),
    }

    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)

    all_passed = True
    for name, code in results.items():
        status = "✓ 通过" if code == 0 else "✗ 失败"
        print(f"{name:20s}: {status}")
        if code != 0:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("✓ 所有检查通过！")
        return 0
    else:
        print("✗ 部分检查失败，请查看详细信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
