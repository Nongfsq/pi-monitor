from flask import Flask
from flask_cors import CORS
from .models import db

def create_app():
    app = Flask(__name__)
    CORS(app) # 允许跨域请求，前端
    
    # 加载配置
    app.config.from_object('config.Config')
    
    # 绑定数据库
    db.init_app(app)
    
    # 注册路由
    from . import routes
    app.register_blueprint(routes.api_bp)

    from . import routes
    app.register_blueprint(routes.main_bp)
    
    return app
