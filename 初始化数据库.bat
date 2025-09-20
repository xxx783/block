@echo off
REM 数据库初始化脚本
REM 此脚本用于解决SQLite数据库无法打开的问题

REM 设置工作目录为当前脚本所在目录
cd /d %~dp0

REM 显示当前目录
echo 当前工作目录: %cd%

echo ============================================================
echo                免费观影应用 - 数据库初始化工具

echo 此工具将帮助您创建和初始化应用所需的SQLite数据库

echo ============================================================

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python。请先安装Python并添加到系统环境变量中。
    pause
    exit /b 1
)

REM 运行数据库初始化脚本
echo 开始初始化数据库...
python initialize_database.py

REM 检查脚本执行结果
if %errorlevel% equ 0 (
    echo.
echo 数据库初始化成功！
echo.
echo 现在您可以通过以下方式启动应用：
echo 1. 双击运行 run_app.bat 文件

echo 2. 或者在命令行中执行：python app.py
) else (
    echo.
echo 数据库初始化失败！
echo 请查看错误信息并尝试解决问题。
)

pause