@echo off
chcp 65001 >nul
echo ========================================
echo   智慧校园餐厅推荐系统 - 快速启动
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/4] 检查后端依赖...
cd backend
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo ✓ 依赖检查完成
echo.

echo [2/4] 启动后端服务...
start "后端服务" cmd /k "cd backend && call venv\Scripts\activate.bat && python app.py"
timeout /t 3 /nobreak >nul
echo ✓ 后端服务已启动 (http://127.0.0.1:5000)
echo.

echo [3/4] 启动前端页面...
cd ..\frontend
start "前端页面" cmd /k "python -m http.server 5500"
timeout /t 2 /nobreak >nul
echo ✓ 前端服务已启动 (http://127.0.0.1:5500)
echo.

echo [4/4] 打开浏览器...
timeout /t 2 /nobreak >nul
start http://127.0.0.1:5500
echo.

echo ========================================
echo   启动完成！
echo ========================================
echo.
echo 后端地址: http://127.0.0.1:5000
echo 前端地址: http://127.0.0.1:5500
echo.
echo 提示: 
echo   - 两个命令行窗口会保持运行
echo   - 关闭任意窗口将停止对应服务
echo   - 按 Ctrl+C 可停止服务
echo.
pause