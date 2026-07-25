# LangChain 全套工程

基于 DeepSeek 的 LangChain 工程示例，涵盖 LangChain 核心功能。  
包含后端 API、前端 UI 和 PostgreSQL 数据库，支持 Docker Compose 一键部署。

---

## 项目结构

```
agent-langchain/
├── backend/                          # 后端服务 (Python FastAPI)
│   ├── app/
│   │   ├── config.py                 # 配置管理
│   │   ├── database.py               # PostgreSQL 数据库连接
│   │   ├── models/
│   │   │   └── llm.py                # LLM 模型封装
│   │   ├── chains/
│   │   │   ├── basic_chain.py        # 基础链
│   │   │   ├── conversation_chain.py # 对话链（PG 持久化）
│   │   │   ├── multi_chain.py        # 顺序链 + 路由链
│   │   │   └── memory_examples.py    # 记忆管理
│   │   ├── agents/
│   │   │   ├── tools.py              # 自定义工具
│   │   │   └── agent_executor.py     # Agent 执行器
│   │   ├── rag/
│   │   │   └── rag_pipeline.py       # RAG 管道（pgvector）
│   │   ├── api/
│   │   │   ├── routes.py             # API 路由定义
│   │   │   └── server.py             # FastAPI 应用入口
│   │   ├── examples/
│   │   │   ├── chat_bot.py           # 交互式聊天
│   │   │   └── translator.py         # 翻译 + 文本处理
│   │   └── cli.py                    # CLI 主菜单
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/                         # 前端界面 (React + TypeScript + Vite)
│   ├── src/
│   │   ├── App.tsx                   # 主应用
│   │   ├── App.css                   # 样式
│   │   ├── components/
│   │   │   ├── Chat.tsx              # 聊天主逻辑
│   │   │   ├── ChatInput.tsx         # 输入框
│   │   │   ├── MessageList.tsx       # 消息列表（Markdown 渲染）
│   │   │   └── Sidebar.tsx           # 侧边栏（会话管理）
│   │   ├── api/client.ts             # API 调用
│   │   └── types/index.ts            # 类型定义
│   ├── Dockerfile + nginx.conf
│   └── package.json
├── db/
│   └── init.sql                      # 数据库初始化（pgvector）
├── docker-compose.yml                # 一键部署编排
├── main.py                           # CLI 入口（兼容旧路径）
├── .env.example                      # 环境变量模板
└── README.md
```

## 功能模块

| 模块 | 说明 |
|------|------|
| **基础链** | LCEL 声明式链、Prompt 模板、输出解析 |
| **对话链** | 带 PostgreSQL 持久化对话历史的连续对话 |
| **顺序链** | 多步链式调用（头脑风暴→评估→总结） |
| **路由链** | 根据输入内容路由到不同专业领域 |
| **记忆管理** | Buffer / Summary / 手动三种记忆方式 |
| **Agent** | Tool Calling Agent，自定义工具集 |
| **RAG** | pgvector 向量检索增强生成 |
| **聊天机器人** | 命令行交互式聊天 |
| **翻译助手** | 翻译→校对管道 |
| **API 服务** | FastAPI HTTP 接口，支持无状态/有状态对话 |
| **前端 UI** | React 聊天界面，多会话管理 |

---

## 快速开始

### 方式一：Docker Compose 本地开发

```bash
# 1. 设置 DeepSeek API Key
set DEEPSEEK_API_KEY=your_key_here

# 2. 一键启动所有服务
docker compose up -d --build

# 3. 访问前端界面
#    http://localhost:3000

# 4. API 服务
#    http://localhost:8000
#    http://localhost:8000/docs  (Swagger 文档)
```

### 方式二：生产部署（带域名 + HTTPS）

```bash
# 1. 准备：将域名解析到服务器 IP
#    确保服务器 80 和 443 端口开放

# 2. 设置环境变量
set DOMAIN=your-domain.com
set ACME_EMAIL=admin@your-domain.com    # Let's Encrypt 通知邮箱
set DEEPSEEK_API_KEY=your_key_here
set DB_PASSWORD=your_strong_password_here

# 3. 一键部署（生产模式）
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 4. Traefik 会自动申请 Let's Encrypt SSL 证书
#    访问 https://your-domain.com 即可使用

# 5. 查看日志
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### 方式三：本地开发

#### 后端

```bash
# 1. 配置 API Key
cd backend
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行 CLI 主菜单
python -m app.cli

# 4. 启动 API 服务
python -m app.api.server
# 服务运行在 http://localhost:8000
```

#### 前端

```bash
cd frontend
npm install
npm run dev
# 开发服务器运行在 http://localhost:5173
```

---

## API 示例

```bash
# 无状态聊天
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "你好！"}'

# 带系统提示词
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "你好", "system_prompt": "你是一个幽默的助手"}'

# 带历史记录的连续对话
curl -X POST http://localhost:8000/conversation \
  -H "Content-Type: application/json" \
  -d '{"prompt": "你好！我叫小明", "session_id": "my-session"}'

curl -X POST http://localhost:8000/conversation \
  -H "Content-Type: application/json" \
  -d '{"prompt": "我叫什么名字？", "session_id": "my-session"}'
```

## CLI 交互式聊天

```bash
python backend/app/examples/chat_bot.py
```

## 架构图

```
                          ┌──────────────┐
                          │   用户浏览器   │
                          └──────┬───────┘
                                 │
                          HTTPS :443
                                 │
                     ┌───────────┴───────────┐
                     │   Traefik (自动 SSL)   │
                     │   Let's Encrypt 证书   │
                     └───┬───────────────┬───┘
                         │               │
                   /api/*         其他路径
                         │               │
                ┌────────┴────────┐  ┌───┴────┐
                │  Backend:8000   │  │ Frontend│
                │ FastAPI+LangChn│  │  Nginx  │
                └────────┬───────┘  │ :80    │
                         │          └────────┘
                ┌────────┴────────┐
                │     DB:5432     │
                │ Postgres+pgvec  │
                │ 聊天历史 + 向量 │
                └─────────────────┘
```

## 技术栈

| 层 | 技术 |
|------|------|
| **前端** | React 18, TypeScript, Vite, react-markdown |
| **后端** | Python 3.12, FastAPI, LangChain, DeepSeek |
| **数据库** | PostgreSQL 16 + pgvector |
| **容器化** | Docker, Docker Compose |
| **反向代理** | Traefik (生产) / Nginx (前端) |
