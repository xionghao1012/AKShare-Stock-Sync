@echo off
REM 安装Windows定时任务
REM 需要管理员权限运行

echo ========================================
echo 安装股票数据同步定时任务
echo ========================================

set SCRIPT_PATH=%~dp0..\tools\daily_sync_scheduler.py
set PYTHON_PATH=%~dp0..\venv\Scripts\python.exe

REM 如果没有虚拟环境，使用系统Python
if not exist "%PYTHON_PATH%" (
    set PYTHON_PATH=python
)

echo 脚本路径: %SCRIPT_PATH%
echo Python路径: %PYTHON_PATH%

REM 创建定时任务 - 每天早上9点执行
schtasks /create /tn "股票数据同步-早盘" /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\" --run-once" /sc daily /st 09:00 /f

REM 创建定时任务 - 每天晚上6点执行
schtasks /create /tn "股票数据同步-收盘" /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\" --run-once" /sc daily /st 18:00 /f

REM 创建定时任务 - 周六上午10点执行
schtasks /create /tn "股票数据同步-周末检查" /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\" --run-once" /sc weekly /d SAT /st 10:00 /f

echo.
echo ========================================
echo 定时任务安装完成！
echo ========================================
echo.
echo 已创建以下定时任务：
echo 1. 股票数据同步-早盘 (每天 09:00)
echo 2. 股票数据同步-收盘 (每天 18:00)  
echo 3. 股票数据同步-周末检查 (周六 10:00)
echo.
echo 查看任务: schtasks /query /tn "股票数据同步*"
echo 删除任务: schtasks /delete /tn "股票数据同步*" /f
echo.

pause