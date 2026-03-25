import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # SQLite 数据库配置
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'monitor.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 默认监控配置
    DEFAULT_TARGET_URL = "https://www.google.com"
    DEFAULT_INTERVAL_SECONDS = 10
