@echo off
REM 智能股票数据同步脚本
REM 生成时间: 2025-07-21 00:01:19
REM 需要同步的股票数量: 9

echo 开始智能股票数据同步...
echo 总共需要同步 9 只股票
echo.

echo ========================================
echo 开始同步中优先级股票(数据不完整/过旧)
echo 数量: 9 只
echo ========================================

python core/smart_stock_sync.py continue 301630  REM C同宇新材 - 记录数过少(7条)
python core/smart_stock_sync.py continue 001388  REM 信通电子 - 记录数过少(14条)
python core/smart_stock_sync.py continue 301678  REM 新恒汇 - 记录数过少(21条)
python core/smart_stock_sync.py continue 301590  REM 优优绿能 - 记录数过少(32条)
python core/smart_stock_sync.py continue 001390  REM 古麒绒材 - 记录数过少(36条)
python core/smart_stock_sync.py continue 301595  REM 太力科技 - 记录数过少(44条)
python core/smart_stock_sync.py continue 301636  REM 泽润新能 - 记录数过少(45条)
python core/smart_stock_sync.py continue 300841  REM 康华生物 - 数据过旧(最新:2025-07-11)
python core/smart_stock_sync.py continue 300174  REM 元力股份 - 数据过旧(最新:2025-07-11)

echo.
echo ========================================
echo 智能同步完成！
echo ========================================
pause
