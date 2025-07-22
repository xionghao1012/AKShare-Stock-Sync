@echo off
REM 启动每日股票数据同步服务
REM 使用方法：
REM   start_daily_sync.bat          - 启动定时服务
REM   start_daily_sync.bat once     - 立即执行一次同步
REM   start_daily_sync.bat check    - 检查交易日历

echo ========================================
echo 每日股票数据同步服务
echo ========================================

if "%1"=="once" (
    echo 立即执行一次同步任务...
    python tools/daily_sync_scheduler.py --run-once
    goto :end
)

if "%1"=="check" (
    echo 检查交易日历状态...
    python tools/daily_sync_scheduler.py --check-calendar
    goto :end
)

echo 启动定时同步服务...
echo 按 Ctrl+C 停止服务
echo.
python tools/daily_sync_scheduler.py

:end
pause