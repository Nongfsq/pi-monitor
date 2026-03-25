from flask import Flask, jsonify, request
from gpiozero import RGBLED
import requests
import threading
import time
import sqlite3
from datetime import datetime

# 1. 初始化 Flask
app = Flask(__name__)

# 2. 初始化硬件 (红=GPIO22, 绿=GPIO27, 蓝=GPIO17)
led = RGBLED(red=22, green=27, blue=17)

# 3. 初始化配置
config = {
    "target_url": "https://www.google.com",
    "check_interval": 10,
    "current_status": "Unknown"
}

# 4. 数据库初始化函数
def init_db():
    conn = sqlite3.connect('monitoring.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS status_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            url TEXT,
            status_code INTEGER,
            latency_ms REAL,
            is_online INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# 5. 存入数据的函数
def log_to_db(url, status_code, latency, is_online):
    try:
        conn = sqlite3.connect('monitoring.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO status_logs (timestamp, url, status_code, latency_ms, is_online)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), url, status_code, latency, 1 if is_online else 0))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"数据库写入错误: {e}")

# 6. 后台监控循环
def monitor_loop():
    while True:
        status_code = 0
        latency = 0
        is_online = False
        
        try:
            start_time = time.time()
            resp = requests.get(config["target_url"], timeout=5)
            latency = round((time.time() - start_time) * 1000, 2)
            status_code = resp.status_code
            
            if resp.status_code == 200:
                led.color = (0, 1, 0) # 绿色
                config["current_status"] = "Online"
                is_online = True
            else:
                led.color = (1, 1, 0) # 黄色 (Warning)
                config["current_status"] = "Warning"
        except Exception as e:
            led.color = (1, 0, 0) # 红色 (Offline)
            config["current_status"] = "Offline"
            print(f"检测失败: {e}")

        # 将结果存入数据库
        log_to_db(config["target_url"], status_code, latency, is_online)
        time.sleep(config["check_interval"])

# --- API 路由定义 ---

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(config)

@app.route('/api/history', methods=['GET'])
def get_history():
    limit = request.args.get('limit', 20)
    conn = sqlite3.connect('monitoring.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM status_logs ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for r in rows:
        history.append({
            "id": r[0], "time": r[1], "url": r[2], 
            "code": r[3], "latency": r[4], "online": r[5]
        })
    return jsonify(history)

@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.json
    if data and 'url' in data:
        config['target_url'] = data['url']
        return jsonify({"message": "URL updated", "new_url": data['url']})
    return jsonify({"error": "Invalid data"}), 400

# --- 启动入口 ---

if __name__ == '__main__':
    init_db() # 启动时确保数据库表已创建
    # 启动后台监控线程
    threading.Thread(target=monitor_loop, daemon=True).start()
    # 运行 Flask
    app.run(host='0.0.0.0', port=5000)