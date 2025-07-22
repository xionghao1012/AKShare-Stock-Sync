"""
数据管理工具
"""
import pandas as pd
from sqlalchemy import create_engine, text
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DataManager:
    """数据管理类"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.engine = create_engine(
            db_config.get_connection_string(),
            **db_config.get_engine_config()
        )
    
    def get_table_list(self) -> List[str]:
        """获取所有表名"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SHOW TABLES"))
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"获取表列表失败: {e}")
            return []
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """获取表信息"""
        try:
            with self.engine.connect() as conn:
                # 获取表结构
                result = conn.execute(text(f"DESCRIBE {table_name}"))
                columns = result.fetchall()
                
                # 获取记录数
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                
                # 获取最后更新时间
                result = conn.execute(text(f"""
                    SELECT UPDATE_TIME 
                    FROM information_schema.tables 
                    WHERE table_schema = '{self.db_config.database}' 
                    AND table_name = '{table_name}'
                """))
                update_time = result.scalar()
                
                return {
                    'table_name': table_name,
                    'columns': [{'name': col[0], 'type': col[1]} for col in columns],
                    'record_count': count,
                    'last_updated': update_time
                }
        except Exception as e:
            logger.error(f"获取表 {table_name} 信息失败: {e}")
            return {}
    
    def get_data_sample(self, table_name: str, limit: int = 5) -> Optional[pd.DataFrame]:
        """获取数据样本"""
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(
                    f"SELECT * FROM {table_name} LIMIT {limit}",
                    conn
                )
                return df
        except Exception as e:
            logger.error(f"获取表 {table_name} 数据样本失败: {e}")
            return None
    
    def export_table_to_csv(self, table_name: str, output_path: str) -> bool:
        """导出表数据到CSV"""
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
                logger.info(f"表 {table_name} 已导出到 {output_path}")
                return True
        except Exception as e:
            logger.error(f"导出表 {table_name} 失败: {e}")
            return False
    
    def cleanup_old_data(self, table_name: str, days: int = 30) -> bool:
        """清理旧数据"""
        try:
            with self.engine.connect() as conn:
                # 假设表中有date或datetime列
                conn.execute(text(f"""
                    DELETE FROM {table_name} 
                    WHERE DATE(created_at) < DATE_SUB(CURDATE(), INTERVAL {days} DAY)
                """))
                logger.info(f"已清理表 {table_name} 中 {days} 天前的数据")
                return True
        except Exception as e:
            logger.error(f"清理表 {table_name} 旧数据失败: {e}")
            return False