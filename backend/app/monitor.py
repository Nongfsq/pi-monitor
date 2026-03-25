import requests
import time
from datetime import datetime, timedelta
from .models import db, StatusLog, AppConfig
from .hardware import hw_controller
from .display import lcd_controller

def check_website_status(app):
    """这是后台定时运行的引擎核心"""
    with app.app_context():
        # 1. 读取当前配置
        cfg_url = AppConfig.query.filter_by(key='target_url').first()
        cfg_maint = AppConfig.query.filter_by(key='maintenance_mode').first()
        cfg_dev = AppConfig.query.filter_by(key='dev_override').first()
        
        target_url = cfg_url.value if cfg_url else "https://www.google.com"
        is_maint = True if (cfg_maint and cfg_maint.value == 'true') else False
        is_dev = True if (cfg_dev and cfg_dev.value == 'true') else False

        # --- 开发者接管模式拦截 ---
        if is_dev:
            # 开发者正在测试灯光，后台引擎暂停工作
            return

        # --- 维护模式拦截逻辑 ---
        if is_maint:
            hw_controller.set_status("maintenance")
            lcd_controller.show_status("maintenance")
            log = StatusLog(
                timestamp=datetime.utcnow(),
                target_url=target_url,
                status_code=0,
                latency_ms=0,
                status_category="maintenance"
            )
            db.session.add(log)
            db.session.commit()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Maintenance Mode is ON. Skipping check.")
            return

        # --- 正常的网络探测逻辑 ---
        status_code = None
        latency_ms = None
        category = "critical"
        
        try:
            start_time = time.time()
            resp = requests.get(target_url, timeout=5)
            latency_ms = round((time.time() - start_time) * 1000, 2)
            status_code = resp.status_code

            if status_code == 200:
                if latency_ms < 500:
                    category = "healthy"
                else:
                    category = "degraded"
            elif status_code >= 400:
                category = "error"
            else:
                category = "degraded"
                
        except requests.exceptions.RequestException as e:
            category = "critical"

        # 2. 指挥硬件 并且 更新输出设备
        hw_controller.set_status(category)
        lcd_controller.show_status(category, latency_ms=latency_ms, status_code=status_code)

        # 3. 记录日志并执行垃圾回收 (GC)
        log = StatusLog(
            timestamp=datetime.utcnow(),
            target_url=target_url,
            status_code=status_code,
            latency_ms=latency_ms,
            status_category=category
        )
        db.session.add(log)
        
        # 清理 3 天前的老数据
        try:
            three_days_ago = datetime.utcnow() - timedelta(days=3)
            deleted_count = StatusLog.query.filter(StatusLog.timestamp < three_days_ago).delete()
            if deleted_count > 0:
                print(f"🧹 GC: Deleted {deleted_count} old records.")
        except Exception as e:
            print(f"GC Error: {e}")

        db.session.commit()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Checked {target_url} -> {category.upper()} ({latency_ms}ms)")
