"""
数据库管理模块
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from loguru import logger

from database.models import Base


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config):
        """
        初始化数据库管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.engine = None
        self.Session = None
        self._init_engine()
    
    def _init_engine(self):
        """初始化数据库引擎"""
        db_config = self.config.get('database', {})
        db_type = db_config.get('type', 'sqlite')
        
        if db_type == 'sqlite':
            # SQLite配置
            db_path = db_config.get('sqlite', {}).get('path', 'data/longport_quant.db')
            
            # 确保目录存在
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            database_url = f'sqlite:///{db_path}'
            self.engine = create_engine(
                database_url,
                echo=False,
                connect_args={'check_same_thread': False}
            )
            logger.info(f"使用SQLite数据库: {db_path}")
            
        elif db_type == 'postgresql':
            # PostgreSQL配置
            pg_config = db_config.get('postgresql', {})
            host = pg_config.get('host', 'localhost')
            port = pg_config.get('port', 5432)
            database = pg_config.get('database', 'longport_quant')
            user = pg_config.get('user', 'postgres')
            password = pg_config.get('password', '')
            
            database_url = f'postgresql://{user}:{password}@{host}:{port}/{database}'
            
            # 性能配置
            perf_config = self.config.get('performance', {})
            pool_size = perf_config.get('db_pool_size', 10)
            max_overflow = perf_config.get('db_max_overflow', 20)
            
            self.engine = create_engine(
                database_url,
                echo=False,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True
            )
            logger.info(f"使用PostgreSQL数据库: {host}:{port}/{database}")
        
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
        
        # 创建Session工厂
        self.Session = scoped_session(sessionmaker(bind=self.engine))
    
    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
    
    def drop_tables(self):
        """删除所有表（谨慎使用）"""
        try:
            Base.metadata.drop_all(self.engine)
            logger.warning("数据库表已删除")
        except Exception as e:
            logger.error(f"删除数据库表失败: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """
        获取数据库会话（上下文管理器）
        
        使用示例:
            with db_manager.get_session() as session:
                stocks = session.query(StockInfo).all()
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    def execute_query(self, query_func):
        """
        执行查询函数
        
        Args:
            query_func: 接受session参数的查询函数
            
        Returns:
            查询结果
        """
        with self.get_session() as session:
            return query_func(session)
    
    def bulk_insert(self, objects):
        """
        批量插入对象
        
        Args:
            objects: 要插入的对象列表
        """
        if not objects:
            return
        
        with self.get_session() as session:
            session.bulk_save_objects(objects)
            logger.info(f"批量插入 {len(objects)} 条记录")
    
    def bulk_update(self, model, mappings):
        """
        批量更新
        
        Args:
            model: 模型类
            mappings: 更新映射列表
        """
        if not mappings:
            return
        
        with self.get_session() as session:
            session.bulk_update_mappings(model, mappings)
            logger.info(f"批量更新 {len(mappings)} 条记录")
    
    def get_or_create(self, session, model, defaults=None, **kwargs):
        """
        获取或创建对象
        
        Args:
            session: 数据库会话
            model: 模型类
            defaults: 创建时的默认值
            **kwargs: 查询条件
            
        Returns:
            (instance, created): 对象实例和是否新创建的标志
        """
        instance = session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance, False
        else:
            params = dict(kwargs)
            if defaults:
                params.update(defaults)
            instance = model(**params)
            session.add(instance)
            return instance, True
    
    def close(self):
        """关闭数据库连接"""
        if self.Session:
            self.Session.remove()
        if self.engine:
            self.engine.dispose()
        logger.info("数据库连接已关闭")


# 全局数据库管理器实例
_db_manager = None


def init_database(config):
    """
    初始化全局数据库管理器
    
    Args:
        config: 配置字典
    """
    global _db_manager
    _db_manager = DatabaseManager(config)
    return _db_manager


def get_db_manager():
    """
    获取全局数据库管理器
    
    Returns:
        DatabaseManager实例
    """
    if _db_manager is None:
        raise RuntimeError("数据库管理器未初始化，请先调用 init_database()")
    return _db_manager

