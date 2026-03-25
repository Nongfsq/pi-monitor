from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class StatusLog(db.Model):
    """历史监控日志表"""
    __tablename__ = 'status_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    target_url = db.Column(db.String(255), nullable=False)
    status_code = db.Column(db.Integer, nullable=True)
    latency_ms = db.Column(db.Float, nullable=True)
    # 状态分类: healthy, degraded, error, critical, maintenance
    status_category = db.Column(db.String(50), nullable=False) 

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() + "Z",
            "target_url": self.target_url,
            "status_code": self.status_code,
            "latency_ms": self.latency_ms,
            "status_category": self.status_category
        }

class AppConfig(db.Model):
    """系统动态配置表（存入数据库，断电不丢失）"""
    __tablename__ = 'app_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
