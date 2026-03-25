from app import create_app
from app.models import db, AppConfig
from app.monitor import check_website_status
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = create_app()

with app.app_context():
    # 1. 建表
    db.create_all()
    # 2. 写入默认配置
    if not AppConfig.query.filter_by(key='target_url').first():
        db.session.add(AppConfig(key='target_url', value='https://www.google.com'))
        
    # 【核心修复】：每次重启服务时，强制释放开发者接管模式，唤醒后台自动探测引擎！
    dev_cfg = AppConfig.query.filter_by(key='dev_override').first()
    if dev_cfg:
        dev_cfg.value = 'false'
    else:
        db.session.add(AppConfig(key='dev_override', value='false'))
        
    db.session.commit()
# --- 核心：启动定时任务引擎 ---
# 创建调度器
scheduler = BackgroundScheduler(daemon=True)

# 把探测任务加进去，每隔 10 秒执行一次
# 注意：我们把 app 作为参数传给它，这样它才能访问数据库
scheduler.add_job(func=check_website_status, args=[app], trigger="interval", seconds=10)

# 启动
scheduler.start()

# 当程序退出时，安全关闭调度器
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    # print("等待第一次探测...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
