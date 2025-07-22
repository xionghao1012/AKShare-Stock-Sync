@echo off
# 股票数据批量同步脚本
# 生成时间: 2025-07-21 00:06:05

echo 开始补充部分同步的股票数据...
python core/smart_stock_sync.py continue 301630  # C同宇新材 (7条)
python core/smart_stock_sync.py continue 001388  # 信通电子 (14条)
python core/smart_stock_sync.py continue 301678  # 新恒汇 (21条)
python core/smart_stock_sync.py continue 301590  # 优优绿能 (32条)
python core/smart_stock_sync.py continue 001390  # 古麒绒材 (36条)
python core/smart_stock_sync.py continue 301595  # 太力科技 (44条)
python core/smart_stock_sync.py continue 301636  # 泽润新能 (45条)
python core/smart_stock_sync.py continue 301560  # 众捷汽车 (57条)
python core/smart_stock_sync.py continue 001400  # 江顺科技 (58条)
python core/smart_stock_sync.py continue 301662  # 宏工科技 (63条)
python core/smart_stock_sync.py continue 001335  # 信凯科技 (64条)
python core/smart_stock_sync.py continue 301665  # 泰禾股份 (67条)
python core/smart_stock_sync.py continue 301658  # 首航新能 (73条)
python core/smart_stock_sync.py continue 301535  # 浙江华远 (77条)
python core/smart_stock_sync.py continue 301616  # 浙江华业 (77条)
python core/smart_stock_sync.py continue 001382  # 新亚电缆 (80条)
python core/smart_stock_sync.py continue 301629  # 矽电股份 (80条)
python core/smart_stock_sync.py continue 301501  # 恒鑫生活 (83条)
python core/smart_stock_sync.py continue 301479  # 弘景光电 (84条)
python core/smart_stock_sync.py continue 301275  # 汉朔科技 (89条)
python core/smart_stock_sync.py continue 301557  # 常友科技 (94条)
python core/smart_stock_sync.py continue 301173  # 毓恬冠佳 (95条)

echo 同步完成！
