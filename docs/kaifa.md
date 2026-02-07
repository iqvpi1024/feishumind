# FeishuMind AI Agent 开发手册

**版本**：1.0（2026年2月6日）  
**作者**：基于Grok与Gemini的协作建议，由杰（SuperGrok用户）指导  
**目标读者**：Claude Code（Anthropic的AI编码工具）作为主要执行者，一人公司开发者作为监督者。  
**手册目的**：本手册提供一个完整的、步步可操作的开发指南，帮助你使用Claude Code快速构建FeishuMind项目。Claude Code的核心是自然语言提示工程，因此手册强调如何撰写高效提示来生成代码、工作流和模块。项目定位为“职场参谋”AI代理，聚焦飞书生态的效率工具与情绪管理。手册整合红蓝对抗观点，确保平衡创新与风险：技术激进但可控，商业务实且合规。  

如果你是Claude Code，直接复制手册中的提示模板，输入你的界面生成输出。然后，开发者（杰）审核并迭代。预计MVP开发时间：1-2周（利用Claude Code的效率提升68%）。资源要求：8GB云服务器，Python环境，免费开源工具。

## 1. 项目概述与原则
**项目名称**：FeishuMind  
**描述**：一个半自主AI代理，集成飞书bot，提供职场效率自动化（如GitHub推送、日程提醒）和韧性辅导（如情绪压力管理）。核心卖点：持久记忆反馈闭环、半自主Skills生成（用户审核执行）、本地隐私存储。避免“身份危机”：功能以职场黑话包装（如“韧性辅导”而非“失恋陪伴”）。  

**设计原则**（针对Claude Code）：
- **半自主进化**：Agent可生成Skills建议，但需Human Approval（用户确认）执行，防止失控。
- **隐私优先**：敏感数据（如情绪记录）本地存储，脱敏上传大模型。
- **反馈闭环**：用Mem0的评分机制（e.g., <0.8时优化），实现RLHF-like迭代。
- **提示工程最佳实践**：你的提示应具体、结构化，包括系统角色、输入示例、输出格式。示例："You are a senior CTO building a secure AI agent. Generate Python code for [功能] using [工具], with safety checks."

**风险警示**：Claude Code生成代码需人工Review（死循环风险）。Token成本监控（阈值警报）。合规：PIPL要求同意弹窗，内容过滤敏感回复。

## 2. 技术栈概述
- **核心工具**：Claude Code（生成代码/workflow）；n8n（自动化工作流）；LangChain（代理链）；Mem0（记忆层）。
- **后端**：Python 3.12+ FastAPI（API服务器）；Docker（部署）。
- **内存**：Mem0 + FAISS/Pinecone（混合检索）；SQLite/Redis（存储/缓存）。
- **集成**：飞书SDK/MCP（bot接入）；GitHub API（热门拉取）。
- **安全/运维**：JWT/NGINX（认证）；GitHub Actions（CI/CD）；Prometheus/Sentry（监控）。
- **模型**：Claude 3.5 Sonnet（或本地Llama-3量化版，减少成本）。

安装基础环境（在你的服务器运行）：  
```bash
# 假设Ubuntu服务器
sudo apt update && sudo apt install python3-pip docker docker-compose git
pip install poetry
git clone https://github.com/your-repo/feishumind.git
cd feishumind
poetry install  # 添加依赖如langchain, mem0ai, fastapi
docker-compose up -d  # 启动n8n/Redis等
```

## 3. 开发流程（Agile + 风险控制）
采用每周Sprint：Claude Code生成 -> 开发者审核 -> n8n测试 -> 迭代。总6阶段。

### 阶段1: Setup（1-2天）
- **目标**：初始化项目结构。
- **Claude Code提示模板**：  
  "You are a CTO setting up a Python AI agent project. Use Poetry for dependencies. Generate a project scaffold with folders: src (for agent.py, memory.py), tests, docs. Include .gitignore, requirements.txt, and docker-compose.yml for n8n, FastAPI, Redis, Postgres. Integrate Mem0 config for memory. Output as zip structure."
- **输出预期**：生成项目文件。审核后，运行`poetry install`。
- **风险控制**：添加.gitignore忽略API密钥。

### 阶段2: Core Dev - 构建代理内核（3-5天）
- **目标**：实现半自主Agent和Memory。
- **Claude Code提示模板（代理生成）**：  
  "You are a senior AI engineer. Build a LangGraph agent in Python for FeishuMind. State includes messages and memory_feedback. Tools: generate_skill (autonomous but with user approval). Prompt: 'You are a Chief of Staff with empathy. Focus on task efficiency and emotional energy.' Integrate Mem0 for persistent memory: add/search/update with feedback score. Add safety: if feedback <0.8, optimize prompt. Code in agent.py."
- **示例代码输出**（Claude生成后审核）：参考之前agent.py片段。
- **Memory整合提示**：  
  "Integrate Mem0 with FAISS for hybrid memory in FeishuMind. Config: local SQLite for events, HuggingFace embedder. Add proactive_scan function: every hour, fetch Feishu updates, add to memory, evolve if score low. Include脱敏: strip sensitive data before LLM call."
- **风险控制**：加Human Approval Node（在n8n：HTTP节点推送到飞书卡片，用户点击确认）。

### 阶段3: 功能模块开发（4-7天）
- **自动化推送提示**：  
  "Generate n8n workflow JSON for daily 9AM GitHub trending push. Nodes: Schedule (cron 0 9 * * *), HTTP (GitHub API), Mem0 Retrieve (user prefs), Feishu Send. Add feedback: after send, ask user score, update Mem0."
- **事件提醒提示**：  
  "Build FastAPI endpoint for Feishu webhook. Parse message for events (use spaCy NLP), store in Mem0, schedule reminder (APScheduler, 1 day before). If emotional (e.g., stress), suggest resilience coaching: 'Suggest no-meeting slot'."
- **压力管理提示**：  
  "Create subconscious review tool: Input weekly chat/logs, analyze emotion curve (use NLTK sentiment), combine GitHub commits. Output: Weekly recap with actionable advice. Prompt: 'Rephrase as business jargon, no therapy vibes.' Integrate A2A: Call calendar bot for slots."
- **风险控制**：每个模块加try-except，日志到Sentry。

### 阶段4: 测试与迭代（2-3天）
- **目标**：单元/集成测试。
- **Claude Code提示**：  
  "Generate Pytest tests for FeishuMind. Cover: Memory add/search (simulate lost event), Skill generation (mock approval), Token usage (assert < threshold). Include edge cases: fuzzy query hallucination."
- **迭代**：运行测试，收集反馈。用Mem0存储开发者笔记，Agent建议优化。
- **风险控制**：模拟死循环（e.g., infinite API call），加阈值断路器。

### 阶段5: 部署与运维（2天）
- **Claude Code提示**：  
  "Update docker-compose.yml for full stack: FastAPI, n8n, Redis, Mem0. Add NGINX proxy with JWT auth. Include Prometheus for monitoring Token/CPU. Generate GitHub Actions workflow: on push, test/deploy to阿里云ECS."
- **示例**：参考之前docker-compose.yml。
- **风险控制**：加防火墙（UFW命令），环境变量加密API密钥。

### 阶段6: 开源与商业准备（持续）
- **Claude Code提示**：  
  "Write README.md for GitHub: Project desc, install guide, Skill Pack examples (e.g., Programmer Pack: Jira integrate). Add LICENSE (MIT), contribution guidelines. Generate Stripe integration for SaaS subscription (29元/月)."
- **商业**：创建Skill Store（简单FastAPI endpoint列Pack），用户订阅激活。
- **风险控制**：添加同意弹窗（飞书卡片："同意存储偏好数据？"），审计日志。

## 4. Claude Code使用指南
- **高效提示技巧**：始终指定角色（e.g., "senior CTO"），输入示例，输出格式（e.g., "Code in file.py, JSON for n8n"）。迭代：如果输出错，添加"Fix based on error: [paste error]"。
- **常见命令**：在VS Code插件中输入提示，生成后复制到项目。
- **集成n8n**：Claude生成JSON后，导入n8n UI调整。
- **调试**：用Claude："Debug this code: [paste] with error [paste]. Suggest fixes."

## 5. 风险管理与优化
- **技术**：Token监控（Prometheus警报>阈值）；半自主守门员（所有写操作需批准）。
- **合规**：PIPL备案（咨询律师）；内容过滤（Prompt中加"避免医疗建议"）。
- **商业**：优先SaaS Pack销售，避免定制泥潭。
- **优化**：72小时行动：修改Prompt为“幕僚长”角色；锁定MVP为“周报情绪复盘”；用Mem0隔离敏感记忆。

手册完。启动开发：复制阶段1提示到Claude Code！如果需更新，告诉我。