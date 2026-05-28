# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

SIMS-NEXT 是一个基于 FastAPI 的学生信息管理系统，包含成绩管理和升学预测 AI 分析功能。

## 常用命令

### 后端开发
```bash
# 启动后端服务
uv run uvicorn app.main:app --reload --port 8000

# 数据库初始化
mysql -u root -p sims < scripts/create_tables.sql

# 安装依赖
uv sync
```

### 前端开发
```bash
cd frontend
npm run dev     # 开发服务器
npm run build  # 构建生产版本
```

## 架构

### 分层结构
```
API Router → Service → Repository → Model
```

每个业务模块都有对应的四层：
- `api/v1/` - 路由层（FastAPI Router）
- `services/` - 业务逻辑
- `repositories/` - 数据访问
- `models/` - ORM模型

### 预测模块 (app/predict/)
```
app/predict/
├── api/v1/          # API端点
│   ├── predict_router.py   # /predictions
│   ├── advice_router.py     # /advice (AI建议和Chat)
│   └── admission_router.py  # /admissions
├── services/        # 业务逻辑
│   ├── prediction_service.py  # 升学预测
│   ├── portrait_service.py    # 学生画像
│   ├── risk_service.py        # 风险分析
│   ├── chat_service.py        # AI对话
│   └── trace_service.py       # 调试追踪
├── repositories/    # 数据访问
├── models/          # ORM模型
├── schemas/         # Pydantic模型
└── ml/              # 机器学习模块
```

### AI对话分析流程
```
用户问题 → ChatService
    ├── get_context() → 调用各Service获取上下文
    │   ├── PredictionService.predict_student_admission()
    │   ├── PortraitService.analyze_student()
    │   └── RiskService.analyze_risk()
    ├── build_prompt() → 构建Prompt
    └── _call_llm() → 调用MiniMax API
```

## 关键配置

环境变量在 `.env` 中：
- `DATABASE_URL` - MySQL连接
- `MINIMAX_API_KEY` - MiniMax LLM API密钥
- `MINIMAX_MODEL` - 使用的模型（默认MiniMax-M2.7）

## 代码规范

- 使用软删除（`is_deleted` 字段标记）
- 模糊搜索需用 `_escape_like` 转义特殊字符
- API文档：http://localhost:8000/docs

## 调试

预测模块的 `/api/v1/advice/{student_id}/debug` 端点可获取AI分析的调用链trace，用于排查问题。