@echo off
REM 免费观影应用启动脚本
REM 请确保已安装所有依赖：pip install -r requirements.txt

REM 设置工作目录为当前脚本所在目录
cd /d %~dp0

REM 启动Flask应用
python app.py

REM 按任意键退出
pause