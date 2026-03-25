from flask import Blueprint, jsonify, request, render_template, current_app
from .models import db, StatusLog, AppConfig
from .hardware import hw_controller
from .monitor import check_website_status

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/status', methods=['GET'])
def get_current_status():
    """获取最新的一条状态"""
    latest_log = StatusLog.query.order_by(StatusLog.timestamp.desc()).first()
    if not latest_log:
        return jsonify({"message": "No data yet"}), 404
    return jsonify(latest_log.to_dict())

@api_bp.route('/history', methods=['GET'])
def get_history():
    """获取历史记录，支持分页"""
    limit = request.args.get('limit', 20, type=int)
    logs = StatusLog.query.order_by(StatusLog.timestamp.desc()).limit(limit).all()
    return jsonify([log.to_dict() for log in logs])

@api_bp.route('/config', methods=['GET', 'POST'])
def manage_config():
    """获取或修改系统配置 (URL 和 维护模式)"""
    if request.method == 'GET':
        cfg_url = AppConfig.query.filter_by(key='target_url').first()
        cfg_maint = AppConfig.query.filter_by(key='maintenance_mode').first()
        
        url = cfg_url.value if cfg_url else "https://www.google.com"
        # 如果数据库里存的是字符串 'true'，则返回布尔值 True
        is_maint = True if (cfg_maint and cfg_maint.value == 'true') else False
        
        return jsonify({
            "target_url": url, 
            "maintenance_mode": is_maint
        })
        
    if request.method == 'POST':
        data = request.json
        
        # 1. 更新 URL
        if 'url' in data:
            cfg_url = AppConfig.query.filter_by(key='target_url').first()
            if not cfg_url:
                cfg_url = AppConfig(key='target_url', value=data['url'])
                db.session.add(cfg_url)
            else:
                cfg_url.value = data['url']
                
        # 2. 更新维护模式开关
        if 'maintenance_mode' in data:
            maint_val = 'true' if data['maintenance_mode'] else 'false'
            cfg_maint = AppConfig.query.filter_by(key='maintenance_mode').first()
            if not cfg_maint:
                cfg_maint = AppConfig(key='maintenance_mode', value=maint_val)
                db.session.add(cfg_maint)
            else:
                cfg_maint.value = maint_val
                
        db.session.commit()
        return jsonify({"message": "Configuration updated successfully"})

@api_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """获取 SLA 可用率和用于图表绘制的延迟数据"""
    # 1. 计算图表数据（取最近 40 次非维护状态的记录）
    logs = StatusLog.query.filter(StatusLog.status_category != 'maintenance') \
                          .order_by(StatusLog.timestamp.desc()).limit(40).all()
    
    # 因为查询是倒序的（最新的在前面），画图需要正序（从左到右），所以反转一下
    logs.reverse() 

    labels = []
    latencies = []
    for log in logs:
        # 提取时间 (例如 14:05:00)
        labels.append(log.timestamp.strftime('%H:%M:%S'))
        latencies.append(log.latency_ms if log.latency_ms else 0)

    # 2. 计算总体 SLA (Uptime 可用率)
    total_checks = StatusLog.query.filter(StatusLog.status_category != 'maintenance').count()
    good_checks = StatusLog.query.filter(StatusLog.status_category.in_(['healthy', 'degraded'])).count()
    
    uptime_percent = 100.00
    if total_checks > 0:
        uptime_percent = round((good_checks / total_checks) * 100, 2)

    return jsonify({
        "uptime_percent": uptime_percent,
        "chart_labels": labels,
        "chart_data": latencies
    })

# root router
main_bp = Blueprint('main', __name__)
@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/dev')
def dev_page():
    """渲染开发者控制台页面"""
    return render_template('dev.html')

@api_bp.route('/dev/control', methods=['POST'])
def dev_control():
    """处理开发者指令"""
    data = request.json
    action = data.get('action')
    
    if action == 'override_toggle':
        # 切换硬件接管状态
        is_override = 'true' if data.get('state') else 'false'
        cfg_dev = AppConfig.query.filter_by(key='dev_override').first()
        if not cfg_dev:
            db.session.add(AppConfig(key='dev_override', value=is_override))
        else:
            cfg_dev.value = is_override
        db.session.commit()
        return jsonify({"msg": "Override toggled"})
        
    elif action == 'set_color':
        # 接收并应用任意颜色
        color_val = data.get('color')
        if color_val == 'off':
            hw_controller.set_manual_color('off')
        elif color_val.startswith('#'):
            hw_controller.set_hex_color(color_val)
        return jsonify({"msg": "Color updated instantly"})
        
    elif action == 'instant_trigger':
        # 瞬间触发一次网络探测 (绕过 10 秒等待)
        # 注意：触发时临时解除一下 Dev 拦截，否则引擎不工作
        check_website_status(current_app._get_current_object())
        return jsonify({"msg": "Instant check completed"})

    return jsonify({"error": "Unknown action"}), 400