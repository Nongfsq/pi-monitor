from gpiozero import RGBLED
import logging

class HardwareController:
    """硬件抽象层：统一定义状态与颜色的映射关系"""
    def __init__(self):
        try:
            # 对应硬件接线 (红=GPIO22, 绿=GPIO27, 蓝=GPIO17)，active_high=True表示高电平点亮
            self.led = RGBLED(red=22, green=27, blue=17, active_high=True)
            self.hardware_ready = True
            logging.info("Hardware LED initialized successfully.")
        except Exception as e:
            self.hardware_ready = False
            logging.error(f"Failed to initialize hardware: {e}")

    def set_status(self, category):
        """根据传入的状态分类，设置对应的颜色"""
        if not self.hardware_ready:
            return

        status_colors = {
            "healthy": (0, 1, 0),     # 纯绿：健康，延迟极低
            "degraded": (1, 1, 0),    # 黄色：200 OK，但延迟很高，性能退化
            "error": (1, 0.5, 0),     # 橙色：4xx 或 5xx 错误
            "critical": (1, 0, 0),    # 红色：彻底断网或超时
            "maintenance": (0, 0, 1), # 蓝色：维护/静默模式
            "off": (0, 0, 0)          # 关灯
        }

        # 获取颜色，如果传入未知状态，默认关灯
        color = status_colors.get(category.lower(), (0, 0, 0))
        self.led.color = color
        
    def set_manual_color(self, color_name):
        """开发者模式：直接设置指定颜色"""
        if not self.hardware_ready:
            return
            
        colors = {
            'red': (1, 0, 0),
            'green': (0, 1, 0),
            'blue': (0, 0, 1),
            'yellow': (1, 1, 0),
            'purple': (1, 0, 1),
            'cyan': (0, 1, 1),
            'white': (1, 1, 1),
            'off': (0, 0, 0)
        }
        self.led.color = colors.get(color_name.lower(), (0, 0, 0))
    
    def set_hex_color(self, hex_code):
        """解析任意 HEX 颜色并瞬间应用到物理 LED"""
        if not self.hardware_ready or not hex_code:
            return
        try:
            # 去除 '#' 符号
            hex_code = hex_code.lstrip('#')
            # 将 00-FF 转换为 0.0-1.0 的浮点数
            r = int(hex_code[0:2], 16) / 255.0
            g = int(hex_code[2:4], 16) / 255.0
            b = int(hex_code[4:6], 16) / 255.0
            self.led.color = (r, g, b)
        except Exception as e:
            logging.error(f"Invalid hex color parsing: {e}")
            
hw_controller = HardwareController()
