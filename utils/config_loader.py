"""
配置加载模块
"""
import os
import yaml
from pathlib import Path
from loguru import logger


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_dir='config'):
        """
        初始化配置加载器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.config = {}
        self.api_config = {}
    
    def load_config(self, config_file='config.yaml'):
        """
        加载主配置文件
        
        Args:
            config_file: 配置文件名
            
        Returns:
            配置字典
        """
        config_path = self.config_dir / config_file
        
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"加载配置文件成功: {config_path}")
            return self.config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise
    
    def load_api_config(self, api_config_file='api_config.yaml'):
        """
        加载API配置文件
        
        Args:
            api_config_file: API配置文件名
            
        Returns:
            API配置字典
        """
        api_config_path = self.config_dir / api_config_file
        
        if not api_config_path.exists():
            raise FileNotFoundError(f"API配置文件不存在: {api_config_path}")
        
        try:
            with open(api_config_path, 'r', encoding='utf-8') as f:
                self.api_config = yaml.safe_load(f)
            logger.info(f"加载API配置文件成功: {api_config_path}")
            return self.api_config
        except Exception as e:
            logger.error(f"加载API配置文件失败: {e}")
            raise
    
    def get(self, key, default=None):
        """
        获取配置项
        
        Args:
            key: 配置键（支持点号分隔的嵌套键，如 'database.type'）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_api(self, key, default=None):
        """
        获取API配置项
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.api_config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def load_all(self):
        """
        加载所有配置文件
        
        Returns:
            (config, api_config) 元组
        """
        self.load_config()
        self.load_api_config()
        return self.config, self.api_config


# 全局配置加载器
_config_loader = None


def init_config(config_dir='config'):
    """
    初始化全局配置加载器
    
    Args:
        config_dir: 配置文件目录
        
    Returns:
        ConfigLoader实例
    """
    global _config_loader
    _config_loader = ConfigLoader(config_dir)
    _config_loader.load_all()
    return _config_loader


def get_config_loader():
    """
    获取全局配置加载器
    
    Returns:
        ConfigLoader实例
    """
    if _config_loader is None:
        raise RuntimeError("配置加载器未初始化，请先调用 init_config()")
    return _config_loader

