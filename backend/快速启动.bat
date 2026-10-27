@echo off
chcp 65001 > nul
echo ==========================================
echo    智能会议纪要助手系统 - 快速启动脚本
echo ==========================================
echo.

REM 检查环境
echo 1. 检查环境...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安装，请先安装 Python 3.10+
    pause
    exit /b 1
)
python --version

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js 未安装，请先安装 Node.js 18+
    pause
    exit /b 1
)
node --version

REM 检查数据库
echo.
echo 2. 检查数据库...
echo ⚠️  请确保已执行 数据库执行文件/db_meeting_minutes.sql
set /p db_confirm="数据库已初始化？(y/n): "
if not "%db_confirm%"=="y" (
    echo ❌ 请先初始化数据库
    pause
    exit /b 1
)

REM 检查配置文件
echo.
echo 3. 检查配置文件...
if not exist "backend\.env" (
    echo ⚠️  backend\.env 不存在，从 .env.example 复制...
    copy backend\.env.example backend\.env
    echo ✅ 已创建 backend\.env，请编辑此文件配置数据库密码
    echo    主要配置项：
    echo    - MYSQL_PASSWORD=你的数据库密码
    echo    - ASR_PROVIDER=mock (测试) 或 funasr (真实)
    echo    - LLM_PROVIDER=mock (测试) 或 qwen (真实)
    pause
)

REM 启动后端
echo.
echo 启动后端...
start "智能会议纪要助手-后端" cmd /k "cd backend && python main.py"

REM 等待后端启动
echo 等待后端启动...
timeout /t 5 /nobreak > nul

REM 启动前端
echo 启动前端...
start "智能会议纪要助手-前端" cmd /k "cd frontend && npm run dev"

echo.
echo ✅ 服务启动完成！
echo.
echo 访问地址：
echo   - 前端页面: http://localhost:3000
echo   - 后端 API 文档: http://localhost:8000/docs
echo   - 健康检查: http://localhost:8000/api/health
echo.
pause
