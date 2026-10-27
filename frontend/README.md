# 智能会议纪要助手系统

基于 LangChain 的 AI 会议纪要生成系统（Python + FastAPI + Vue3）

## 项目结构

```
.
├── backend/           # 后端（FastAPI）
├── frontend/          # 前端（Vue3 + Element Plus）
├── docx/             # 需求和设计文档
└── 数据库执行文件/    # 数据库初始化脚本
```

## 快速开始

### 1. 数据库初始化

```bash
# 执行 SQL 脚本创建数据库和表
mysql -u root -p < 数据库执行文件/db_meeting_minutes.sql
```

### 2. 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量模板并配置
cp .env.example .env
# 编辑 .env 文件，填入必要的配置（数据库、API Key 等）

# 启动服务
python main.py
```

后端将在 http://localhost:8000 启动

### 3. 前端启动

```bash
cd frontend

# 安装依赖（如果还没安装）
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:3000 启动

### 4. 验证连接

打开浏览器访问 http://localhost:3000，点击"测试连接"按钮，如果显示连接成功，说明前后端已成功联通。

## 环境变量配置说明

### 必须配置的环境变量

1. **数据库配置**
   - `MYSQL_HOST`: 数据库地址
   - `MYSQL_PORT`: 数据库端口
   - `MYSQL_USER`: 数据库用户名
   - `MYSQL_PASSWORD`: 数据库密码
   - `MYSQL_DATABASE`: 数据库名（db_meeting_minutes）

2. **阿里云百炼配置**（MVP 阶段必填）
   - `DASHSCOPE_API_KEY`: 阿里云百炼 API Key
   - `ASR_PROVIDER`: 设置为 `funasr`（真实调用）

3. **通义千问配置**（MVP 阶段必填）
   - `LLM_BASE_URL`: 通义千问 OpenAI 兼容端点
   - `LLM_MODEL`: 模型名称（如 qwen-plus）
   - `LLM_PROVIDER`: 设置为 `qwen`（真实调用）

4. **公网访问配置**（MVP 阶段必填）
   - `PUBLIC_BASE_URL`: 公网访问地址（用 ngrok/frp 获取）

### 可选配置

- `DEBUG`: 调试模式（默认 True）
- `JWT_SECRET`: JWT 密钥（阶段2使用）
- `UPLOAD_DIR`: 文件上传目录
- `ASR_POLL_INTERVAL`: ASR 轮询间隔（秒）

## 开发阶段

### ✅ 阶段 0：环境与脚手架（已完成）
- 后端框架搭建
- 前端项目初始化
- 数据库脚本创建
- 基础配置文件

### 🚧 阶段 1：MVP 核心流水线（进行中）
- 文件上传与存储
- ASR 语音转写（真实调用 Fun-ASR）
- LangChain 纪要生成（真实调用通义千问）
- 会议状态机
- 前端页面完善

### ⏳ 阶段 2：登录鉴权（待开发）
### ⏳ 阶段 3：企业多用户与权限（待开发）
### ⏳ 阶段 4：统计与导出完善（待开发）
### ⏳ 阶段 5：生产部署优化（待开发）

## 技术栈

### 后端
- Python 3.10+
- FastAPI
- SQLAlchemy 2.0
- LangChain
- 阿里云百炼 Fun-ASR
- 通义千问（OpenAI 兼容）

### 前端
- Vue 3
- Vite
- Element Plus
- Pinia
- Vue Router
- Axios
- ECharts
- html2pdf.js

## API 文档

启动后端后访问：http://localhost:8000/docs

## 注意事项

1. **MVP 阶段无登录鉴权**，所有会议的 `create_user_id` 默认为 1（admin 用户）
2. **必须配置公网地址**，否则阿里云 ASR 无法下载音频文件
3. **API Key 安全**：不要将 .env 文件提交到 git
4. **Node.js 版本**：建议使用 Node.js 18+
5. **Python 版本**：建议使用 Python 3.10+

## 常见问题

### 1. 前端无法连接后端
- 检查后端是否启动（http://localhost:8000/docs）
- 检查 Vite 代理配置是否正确

### 2. 数据库连接失败
- 检查 MySQL 是否启动
- 检查 .env 中的数据库配置是否正确
- 确认数据库 db_meeting_minutes 已创建

### 3. ASR 转写失败
- 检查 DASHSCOPE_API_KEY 是否正确
- 检查 PUBLIC_BASE_URL 是否配置为公网地址（不能是 127.0.0.1）
- 确认已使用 ngrok/frp 暴露本地服务

## 开发规范

- 后端代码遵循 PEP 8 规范
- 前端代码遵循 Vue 3 风格指南
- 提交前确保代码通过测试
- API 接口统一使用 RESTful 风格

## License

MIT
