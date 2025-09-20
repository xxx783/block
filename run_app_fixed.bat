@echo off
REM 确保在正确的目录运行
cd /d %~dp0

REM 打印当前工作目录和数据库路径信息
echo 当前工作目录: %cd%
echo 数据库路径: %cd%\instancepp.db
if exist %cd%\instancepp.db (
    echo 数据库文件存在
) else (
    echo 警告: 数据库文件不存在
)

REM 启动Flask应用
python app.py

pause
