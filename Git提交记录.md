# Git 提交记录

## 第一次提交 - 阶段 0 完成

**提交哈希**: e8b3b3e  
**提交时间**: 2026-10-27  
**提交信息**: feat: 完成阶段0环境与脚手架搭建

### 包含内容

**后端 (Backend):**
- ✅ FastAPI 应用框架
- ✅ SQLAlchemy 2.0 数据库模型（6张表）
- ✅ Pydantic 配置管理（环境变量）
- ✅ 统一响应格式和异常处理
- ✅ JWT 和 bcrypt 安全模块（预留）
- ✅ 依赖清单 requirements.txt
- ✅ 环境变量模板 .env.example

**前端 (Frontend):**
- ✅ Vue3 + Vite 项目初始化
- ✅ Element Plus UI 框架
- ✅ Pinia 状态管理
- ✅ Vue Router 路由配置
- ✅ Axios 请求封装（含拦截器）
- ✅ 基础工具函数库
- ✅ 测试页面（健康检查）

**数据库 (Database):**
- ✅ 完整的 MySQL 初始化脚本
- ✅ 6张表：t_dept, t_user, t_meeting, t_transcript, t_speaker, t_minutes
- ✅ 默认数据：3个部门 + admin 超级管理员

**文档 (Documentation):**
- ✅ README.md - 项目说明
- ✅ 需求文档 - 项目需求文档_最终版.md
- ✅ 设计文档 - 方案设计文档_最终版.md
- ✅ 阶段0完成总结.md

### 统计信息

- **文件数量**: 47 个文件
- **代码行数**: 5140+ 行
- **目录结构**: 完整的前后端分离架构

### 验证状态

- ✅ 后端可正常启动（http://localhost:8000）
- ✅ API 文档可访问（http://localhost:8000/docs）
- ✅ 健康检查接口正常（/api/health）
- ✅ uploads 目录创建正确
- ✅ 配置文件路径已修复

---

---

## 第二次提交 - 阶段 1 MVP 核心流水线

**提交哈希**: 24df2d4  
**提交时间**: 2026-10-27  
**提交信息**: feat: 完成阶段1 MVP核心流水线开发

### 包含内容

- 后端：Provider 抽象层、ASR/LLM/Meeting/Storage/Speaker 服务、会议管理接口、APScheduler 调度器
- 前端：会议列表、会议详情、状态轮询、发言人重命名、Markdown 下载
- 数据库：复用 6 张表，MVP 阶段 `create_user_id` 固定为 1

---

## 第三次提交 - 阶段 1 验收问题修复

**提交哈希**: 752b2bf  
**分支**: feature/stage2-auth  
**提交时间**: 2026-10-30  
**提交信息**: fix: 修复阶段1验收问题并跑通真实AI链路

### 包含内容

- 修复前端响应信封解析错位
- 修复 GBK 终端下 emoji 导致的启动失败
- 按阿里云百炼官方接口重写真实 Fun-ASR
- 修正通义千问兼容端点并启用真实 LLM
- 修复手动处理、transcribed 状态继续生成纪要
- Mock 模式跳过公网地址校验
- 强化待办提取与 JSON 容错，修复 JSON 字段双重编码
- 更新阶段1状态文档与修复记录

---

## 第四次提交 - 阶段 2 登录鉴权

**提交哈希**: f4ef12a  
**分支**: feature/stage2-auth  
**提交时间**: 2026-10-30  
**提交信息**: feat: 完成阶段2登录鉴权

### 包含内容

- 新增 `/api/auth/login`、`/api/auth/me`、`/api/auth/logout`
- bcrypt 密码校验 + JWT 签发，会议接口统一要求 Bearer Token
- 上传会议 `create_user_id` 改为取自 token 中的真实用户
- 前端登录页、Token 拦截器、路由守卫、退出登录
- 管理员真实密码哈希写入数据库与初始化 SQL
- 新增《阶段2开发完成说明.md》

---

## 第五次提交 - 阶段 3 部门管理与数据权限

**提交哈希**: 3b96790  
**分支**: feature/stage3-permissions  
**提交时间**: 2026-10-30  
**提交信息**: feat: 完成阶段3部门管理与数据权限

### 包含内容

- 新增 `/api/org/depts`、`/api/org/users` 部门与用户管理接口
- `require_super_admin` 保护全部组织管理接口
- 会议数据隔离：普通用户仅本人会议 + 同部门分享会议
- 分享会议只读，写操作与导出权限分别校验
- 会议列表/详情返回创建人、部门、`can_edit`、`is_shared`
- 前端部门管理、用户管理页面与管理员导航
- 超级管理员账号保护、部门删除约束
- 新增《阶段3开发完成说明.md》

---

## 第六次提交 - 个人中心

**提交哈希**: dd05338  
**分支**: feature/profile  
**提交时间**: 2026-10-30  
**提交信息**: feat: 补齐个人中心功能

### 包含内容

- 个人资料修改（昵称、邮箱）
- 头像上传：格式/大小校验、保存到 `uploads/avatars/`、旧头像清理
- 本人修改密码（校验原密码）
- `/api/auth/me` 返回所属部门名称
- 前端个人中心页面、顶部头像、用户菜单入口
- 新增《个人中心开发完成说明.md》

---

## 第七次提交 - 阶段 4 统计首页与 PDF 导出

**提交哈希**: 5311f62  
**分支**: feature/stage4-stats  
**提交时间**: 2026-10-30  
**提交信息**: feat: 完成阶段4统计首页与PDF导出

### 包含内容

- `/api/stats`：超级管理员全局统计、普通用户个人统计
- KPI 卡片、状态分布饼图、近 7 天柱状图、分部门柱状图
- 转写完成自动写入会议时长
- 会议详情使用 html2pdf.js 导出 PDF（懒加载；后续因空白问题改为 html2canvas + jsPDF）
- 登录后默认进入统计首页
- 新增《阶段4开发完成说明.md》

---

## 第八次提交 - 遗留修复与长音频 Map-Reduce

**提交哈希**: f2c46e7  
**分支**: feature/leftover-fixes  
**提交时间**: 2026-10-30  
**提交信息**: fix: 修复遗留问题并完成长音频Map-Reduce

### 包含内容

- 发言人重命名后同步刷新 Markdown
- ASR 任务超时、summarizing 卡住恢复
- localhost/私网地址检测
- 首次登录强制修改密码
- 超管会议列表按创建人筛选
- 前端时间格式统一
- requirements 对齐 backend/venv
- 上传文件分块写入
- 历史会议 duration 回填
- 长音频四步 Map-Reduce
- PDF 导出空白修复（html2canvas + jsPDF 直接截图 + 全白检测）
- vue-router `next()` 弃用警告修复
- 新增《阶段5长音频处理说明.md》

---

## 下一步

- 阶段5 剩余生产部署（Nginx、HTTPS、systemd）未做；
- 真实 ASR 公网地址测试未做；
- 历史测试数据清理待确认；
- 建议在浏览器中复测统计图表与 PDF 导出。


如需推送到远程仓库，请提供仓库地址。
