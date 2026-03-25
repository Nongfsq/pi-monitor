from threading import Lock
from RPLCD.i2c import CharLCD
import logging


class LCDController:
    def __init__(self):
        self.ready = False
        self.lock = Lock()

        try:
            self.lcd = CharLCD(
                i2c_expander='PCF8574',
                address=0x27,
                port=1,
                cols=16,
                rows=2,
                charmap='A02',
                auto_linebreaks=False
            )
            self.ready = True
            self.show_lines("Pi Monitor", "Starting...")
        except Exception as e:
            logging.warning(f"LCD init failed: {e}")

    def _fit(self, text):
        return str(text)[:16].ljust(16)

    def show_lines(self, line1="", line2=""):
        if not self.ready:
            return

        with self.lock:
            self.lcd.clear()
            self.lcd.write_string(self._fit(line1))
            self.lcd.crlf()
            self.lcd.write_string(self._fit(line2))

    def show_status(self, category, latency_ms=None, status_code=None):
        category = (category or "").lower()

        if category == "healthy":
            line1 = "HEALTHY"
            line2 = f"{int(latency_ms)} ms" if latency_ms is not None else "Online"
        elif category == "degraded":
            line1 = "DEGRADED"
            line2 = f"{int(latency_ms)} ms" if latency_ms is not None else "Slow"
        elif category == "error":
            line1 = "ERROR"
            line2 = f"HTTP {status_code}" if status_code else "HTTP error"
        elif category == "critical":
            line1 = "CRITICAL"
            line2 = "No response"
        elif category == "maintenance":
            line1 = "MAINTENANCE"
            line2 = "Paused"
        else:
            line1 = "UNKNOWN"
            line2 = ""

        self.show_lines(line1, line2)

    def show_dev_override(self, color_text="Manual mode"):
        self.show_lines("DEV OVERRIDE", color_text)

    def show_boot(self):
        self.show_lines("Pi Monitor", "Starting...")


lcd_controller = LCDController()
