import akshare as ak
import time

print('测试获取股票300251的数据...')
start_time = time.time()

try:
    df = ak.stock_zh_a_hist(symbol='300251', period='daily', start_date='20250101', end_date='20250721', adjust='')
    end_time = time.time()
    print(f'成功获取数据，耗时: {end_time - start_time:.2f}秒')
    print(f'数据行数: {len(df)}')
    print(df.head())
except Exception as e:
    end_time = time.time()
    print(f'获取数据失败，耗时: {end_time - start_time:.2f}秒')
    print(f'错误: {e}')