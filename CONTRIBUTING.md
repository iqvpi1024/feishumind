# 贡献指南

感谢你对 FeishuMind 的关注！我们欢迎所有形式的贡献。

---

## 🤝 如何贡献

### 报告问题

如果你发现了 Bug 或有功能建议：

1. 检查 [Issues](https://github.com/your-org/feishumind/issues) 是否已有类似问题
2. 如果没有，创建新 Issue
3. 使用清晰的标题和详细的描述
4. 提供复现步骤（针对 Bug）

### 提交代码

1. **Fork 项目**
   ```bash
   # 点击 GitHub 页面上的 "Fork" 按钮
   ```

2. **克隆到本地**
   ```bash
   git clone https://github.com/YOUR_USERNAME/feishumind.git
   cd feishumind
   ```

3. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

4. **进行修改**
   - 遵循代码规范（见下文）
   - 添加测试
   - 更新文档

5. **提交修改**
   ```bash
   git add .
   git commit -m "feat: 添加新功能"
   ```

6. **推送到 GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **创建 Pull Request**
   - 访问 GitHub 页面
   - 点击 "New Pull Request"
   - 填写 PR 描述模板

---

## 📋 代码规范

### Python 代码

遵循 **PEP 8** 标准：

- 使用 Black 格式化
- 使用 isort 排序导入
- 添加类型注解
- 编写 Docstring

**示例**:
```python
from typing import List, Optional

def greet(name: str, enthusiasm: int = 1) -> str:
    """向用户问好。

    Args:
        name: 用户名
        enthusiasm: 热情程度（1-3）

    Returns:
        问候语
    """
    exclamations = "!" * enthusiasm
    return f"你好, {name}{exclamations}"
```

### 提交信息

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具

**示例**:
```
feat(agent): 添加 GitHub Trending 技能

- 实现每日 GitHub Trending 抓取
- 支持语言和 star 数过滤
- 集成飞书卡片推送

Closes #123
```

---

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
python -m pytest

# 运行单元测试
python -m pytest tests/unit/

# 运行集成测试
python -m pytest tests/integration/

# 生成覆盖率报告
python -m pytest --cov=src --cov-report=html
```

### 测试要求

- **覆盖率**: > 80%
- **所有测试必须通过**
- **新功能必须有测试**

---

## 📝 文档

### 文档结构

```
docs/
├── spec/           # 规范文档
│   ├── 00-overview.md
│   ├── 01-architecture.md
│   ├── 02-api-spec.md
│   └── 03-coding-standards.md
├── todo/           # 任务追踪
│   ├── roadmap.md
│   └── weekly-sprint.md
├── deployment-guide.md
├── performance-optimization.md
├── quick-start.md
└── user-testing-guide.md
```

### 更新文档

- 新功能需要更新 API 文档
- 重大变更需要更新 CHANGELOG
- 示例代码需要测试

---

## 🎯 开发流程

### 功能开发

1. 在 `docs/todo/weekly-sprint.md` 中创建任务
2. 创建功能分支
3. 实现功能 + 测试
4. 更新文档
5. 提交 PR
6. Code Review
7. 合并到主分支

### Bug 修复

1. 在 Issues 中报告 Bug
2. 指派给维护者
3. 创建修复分支
4. 修复 Bug + 添加回归测试
5. 提交 PR
6. Code Review
7. 合并到主分支

---

## 📨 Pull Request 模板

```markdown
## 描述
简要描述此 PR 的目的和内容。

## 类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 重构
- [ ] 文档更新
- [ ] 测试
- [ ] 其他

## 变更内容
- 列出主要变更

## 测试
- [ ] 单元测试已通过
- [ ] 集成测试已通过
- [ ] 添加了新测试

## 文档
- [ ] 代码已注释
- [ ] API 文档已更新
- [ ] README 已更新（如需要）

## 相关 Issue
Closes #issue_number

## 截图/演示
（如果适用）
```

---

## 🏷️ 行为准则

### 我们的承诺

为了营造开放和友好的环境，我们承诺：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

### 不可接受的行为

- 使用性化语言或图像
- 人身攻击或侮辱性评论
- 骚扰
- 未经许可发布他人的私人信息
- 其他不道德或不专业的行为

---

## 📞 联系方式

- **GitHub Issues**: [提交问题](https://github.com/your-org/feishumind/issues)
- **邮件**: support@feishumind.com
- **飞书群**: [加入讨论](https://feishu.cn/join-community)

---

## 🙏 致谢

感谢所有贡献者！

**核心贡献者**:
- Claude Code Agent (架构和开发)
- [你的名字] (测试和反馈)

---

**再次感谢你的贡献！** 🎉
