#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试可用的AKShare接口
"""
import akshare as ak
import pandas as pd
from datetime import datetime

def test_stock_basic_info():
    """测试股票基本信息接口"""
    print("1. 测试股票基本信息接口...")
    try:
        df = ak.stock_info_sz_name_code()
        print(f"   ✅ 成功获取 {len(df)} 只股票基本信息")
        print(f"   📊 数据列: {list(df.columns)}")
        print("   🔍 前3条数据:")
        print(df.head(3).to_string(index=False))
        return True, df
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False, None

def test_individual_stock_info():
    """测试个股详细信息接口"""
    print("\n2. 测试个股详细信息接口...")
    test_stocks = ['000001', '000002', '600000']
    results = {}
    
    for stock in test_stocks:
        try:
            df = ak.stock_individual_info_em(symbol=stock)
            if df is not None and not df.empty:
                # 提取关键信息
                info = {}
                for _, row in df.iterrows():
                    info[row['item']] = row['value']
                
                stock_name = info.get('股票简称', 'N/A')
                latest_price = info.get('最新', 'N/A')
                total_shares = info.get('总股本', 'N/A')
                
                print(f"   ✅ {stock} ({stock_name}): 最新价 {latest_price}")
                results[stock] = info
            else:
                print(f"   ⚠️ {stock}: 返回数据为空")
                
        except Exception as e:
            print(f"   ❌ {stock} 失败: {e}")
    
    return results

def test_other_stable_apis():
    """测试其他稳定的接口"""
    print("\n3. 测试其他稳定接口...")
    
    # 测试期货主力合约
    try:
        df_futures = ak.futures_main_sina()
        print(f"   ✅ 期货主力合约: {len(df_futures)} 条数据")
    except Exception as e:
        print(f"   ❌ 期货主力合约失败: {e}")
    
    # 测试ETF信息
    try:
        df_etf = ak.fund_etf_category_sina(symbol="股票型")
        print(f"   ✅ ETF基金信息: {len(df_etf)} 条数据")
    except Exception as e:
        print(f"   ❌ ETF基金信息失败: {e}")

def main():
    print("=== AKShare 可用功能测试 ===")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 测试股票基本信息
    success, stock_info_df = test_stock_basic_info()
    
    # 测试个股详细信息
    individual_results = test_individual_stock_info()
    
    # 测试其他接口
    test_other_stable_apis()
    
    print("\n" + "=" * 50)
    print("=== 测试总结 ===")
    
    if success:
        print("✅ 股票基本信息接口: 正常工作")
        print(f"   - 可获取 {len(stock_info_df)} 只股票的基本信息")
        print("   - 包含: 代码、名称、上市日期、行业等")
    
    if individual_results:
        print(f"✅ 个股详细信息接口: 正常工作")
        print(f"   - 成功获取 {len(individual_results)} 只股票的详细信息")
        print("   - 包含: 实时价格、市值、财务指标等")
    
    print("\n💡 建议:")
    print("1. 优先使用这些稳定的接口获取数据")
    print("2. 避免使用有网络问题的历史数据接口")
    print("3. 可以组合多个接口获取完整信息")
    
    print("\n📝 下一步:")
    print("1. 基于可用接口重新设计数据同步策略")
    print("2. 建立本地数据缓存机制")
    print("3. 定期更新股票基础信息")

if __name__ == "__main__":
    main()