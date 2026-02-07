# GitHub Projects 看板配置

## 📋 看板列设置

创建项目看板后，设置以下列：

1. **Backlog** - 待办事项池
2. **To Do** - 计划内任务
3. **In Progress** - 进行中
4. **In Review** - 审核中
5. **Done** - 已完成

## 🏷️ 标签系统

### 优先级标签
- `priority: critical` - 🔴 紧急
- `priority: high` - 🟠 高
- `priority: medium` - 🟡 中
- `priority: low` - 🟢 低

### 类型标签
- `bug` - 🐛 Bug 修复
- `enhancement` - ✨ 功能增强
- `documentation` - 📖 文档
- `performance` - ⚡ 性能优化
- `security` - 🔒 安全
- `refactoring` - ♻️ 重构

### 状态标签
- `good first issue` - 👶 适合新手
- `help wanted` - 🙋 需要帮助
- `blocked` - 🚫 阻塞
- `wip` - 🚧 进行中

### 模块标签
- `agent` - 🤖 Agent 核心模块
- `memory` - 💾 记忆系统
- `feishu` - 🔗 飞书集成
- `github` - 📊 GitHub 集成
- `ui` - 🎨 用户界面
- `api` - 🔌 API 层

## 📝 初始 Issues 模板

### Issue 1: 欢迎贡献
**标题**: Welcome to FeishuMind! 🎉
**标签**: good first issue, documentation
**描述**:
感谢关注 FeishuMind！这是一个开源的半自主 AI 职场参谋。

## 🚀 快速开始
1. Star ⭐ 这个仓库
2. 阅读 [贡献指南](CONTRIBUTING.md)
3. 查看 [good first issue](https://github.com/iqvpi1024/feishumind/labels/good%20first%20issue)

## 📋 我们需要帮助
- 测试和 Bug 报告
- 文档改进
- 新功能建议
- 代码贡献

欢迎加入我们！

---

### Issue 2: v1.1.0 功能征集
**标题**: v1.1.0 功能征集 - 我们需要你的意见！
**标签**: enhancement, discussion
**Milestone**: v1.1.0
**描述**:
我们正在规划 v1.1.0 版本，欢迎提出建议！

## 🎯 已计划的功能
- [ ] 语音输入支持
- [ ] 多语言支持（英文、日文）
- [ ] 性能优化
- [ ] 更多 Skill Packs

## 💡 你想要什么功能？
请在评论中分享：
1. 最想要的功能
2. 使用场景
3. 优先级

---

### Issue 3: 文档改进反馈
**标题**: 📖 文档改进 - 哪里需要优化？
**标签**: documentation, good first issue, help wanted
**描述**:
帮助我们改进文档！

## 当前文档
- [快速开始](docs/quick-start.md)
- [项目总览](docs/spec/00-overview.md)
- [技术架构](docs/spec/01-architecture.md)
- [API 文档](docs/spec/02-api-spec.md)
- [贡献指南](CONTRIBUTING.md)

## 反馈方向
- 哪些地方不清楚？
- 缺少什么内容？
- 代码示例够不够？
- 需要视频教程吗？

请提 Issue 或 PR！

---

## 🎯 Roadmap Items

### Milestone: v1.1.0
**目标日期**: 2026-03-01
**主题**: 语音和多语言支持

**Issues**:
- [ ] 添加语音输入 API
- [ ] 支持英文界面和响应
- [ ] 支持日文界面和响应
- [ ] 性能优化（减少 Token 消耗）
- [ ] 添加更多 Skill Packs

### Milestone: v1.2.0
**目标日期**: 2026-04-01
**主题**: Skill Pack 市场

**Issues**:
- [ ] Skill Pack 格式规范
- [ ] Skill Pack 上传和下载
- [ ] Skill Pack 评分系统
- [ ] 官方 Skill Packs（程序员版、HR 版）
- [ ] 企业版功能

### Milestone: v2.0.0
**目标日期**: 2026-06-01
**主题**: 重大更新

**Issues**:
- [ ] 移动端支持
- [ ] 多模态输入（图片、文件）
- [ ] 社区市场
- [ ] 企业 SaaS 功能
- [ ] 国际化（全面多语言）

---

## 📊 看板配置代码

复制以下代码到 GitHub Projects 的配置：

```yaml
# 项目看板配置
name: FeishuMind Development

# 列配置
columns:
  - id: backlog
    name: Backlog
  - id: todo
    name: To Do
  - id: in_progress
    name: In Progress
  - id: in_review
    name: In Review
  - id: done
    name: Done

# 自动化规则
automations:
  - when: issue is opened
    then: add to Backlog
  - when: issue is assigned
    then: add to To Do
  - when: issue is labeled with 'in_progress'
    then: move to In Progress
  - when: pull request is merged
    then: move to Done
```

---

**创建看板后，记得将此文档链接到 README.md！**
