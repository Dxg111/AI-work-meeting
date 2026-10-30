# 阶段1 MVP 核心流水线完成说明

> **状态更新时间：2026-10-30**
>
> 阶段1 核心链路已跑通：上传 → 转写 → 纪要 → 导出。
> 当前默认配置为 **Mock ASR + 真实通义千问**；真实 Fun-ASR 代码已按官方接口重写并通过公开示例音频验证，上传本地音频使用真实 ASR 仍需云端可访问的公网地址。

## 已完成内容

### 后端
- 会议管理接口：上传、列表、详情、删除、手动处理、发言人重命名、Markdown 导出、分享开关
- 状态机：`uploaded → transcribing → transcribed → summarizing → done / failed`
- ASR Provider：Mock + 真实 Fun-ASR（阿里云百炼异步录音文件识别）
- LLM Provider：Mock + 真实通义千问（LangChain 四步链式调用）
- APScheduler 轮询 ASR 任务，转写完成后自动继续生成纪要
- 文件存储：本地磁盘 / 腾讯云 COS 可切换（`STORAGE_PROVIDER`），含公网 URL、预签名 URL、回环地址检测

### 前端
- 会议列表（上传、搜索、状态筛选、分页、5 秒轮询）
- 会议详情（基础信息、发言人、AI 纪要、逐句转写、Markdown 下载）
- 发言人重命名
- 统一 Axios 响应处理

## 启动方式

### 1. 配置环境变量

复制 `backend/.env.example` 为 `backend/.env`，至少填写：

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的数据库密码
MYSQL_DATABASE=db_meeting_minutes

PUBLIC_BASE_URL=http://localhost:8000   # 真实 ASR 时必须改为公网地址

ASR_PROVIDER=mock                       # 有公网地址后改为 funasr
ASR_BASE_URL=https://dashscope.aliyuncs.com/api/v1
ASR_MODEL=paraformer-v2

LLM_PROVIDER=qwen
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
DASHSCOPE_API_KEY=你的百炼APIKey
```

### 2. 初始化数据库

执行 `数据库执行文件/db_meeting_minutes.sql`。

### 3. 启动后端

项目自带虚拟环境 `backend/venv`，依赖版本已与 `requirements.txt` 对齐，建议使用它运行：

```bash
cd backend
venv/Scripts/python.exe main.py      # Windows
# source venv/bin/activate && python main.py   # macOS/Linux
```

如需重新安装依赖：

```bash
venv/Scripts/pip.exe install -r requirements.txt
```

后端：`http://localhost:8000`，Swagger：`http://localhost:8000/docs`

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端：`http://localhost:5173`

## 验收状态

| 验收项 | 状态 |
|---|---|
| 上传 → 状态自动流转到 done | 通过（Mock ASR + 真实 LLM） |
| 手动处理完整流水线 | 通过 |
| transcribed 状态继续生成纪要 | 通过 |
| 真实 Fun-ASR 转写 | 通过（公开示例音频验证） |
| 真实通义千问纪要生成 | 通过 |
| 详情页/列表页前端调用链 | 已修复并通过构建，待浏览器点击验收 |
| Markdown 导出 | 后端通过，前端调用链已修复 |
| 5 秒轮询 | 代码完成，待浏览器验收 |

## 已知限制

1. 上传本地音频走真实 ASR 时，云端必须能下载音频；ngrok 免费地址会被阿里云拒绝，建议使用阿里云 OSS 或 frp + 固定域名。
2. `requirements.txt` 的固定版本与实际安装版本不一致，换机安装可能需要调整。
3. 上传文件目前一次性读入内存，大文件存在内存峰值风险。
4. 阶段1 无登录鉴权，会议创建人固定为 admin（阶段2 接入 JWT 后替换）。

## 下一步

阶段2 登录鉴权、阶段3 部门管理与数据权限、阶段4 统计首页与 PDF 导出、个人中心均已完成。

- 默认管理员：`admin / Admin@123456`。首次登录会强制进入个人中心修改初始密码；新建用户、管理员重置密码后同样需要先改密。
- 阶段2：见《阶段2开发完成说明.md》
- 阶段3：见《阶段3开发完成说明.md》
- 阶段4：见《阶段4开发完成说明.md》
- 个人中心：见《个人中心开发完成说明.md》

后续进入阶段5：生产部署、HTTPS、长音频 Map-Reduce 调优。
