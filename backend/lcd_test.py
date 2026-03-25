from RPLCD.i2c import CharLCD
from time import sleep

lcd = CharLCD(
    i2c_expander='PCF8574',
    address=0x27,
    port=1,
    cols=16,
    rows=2,
    charmap='A02',
    auto_linebreaks=False
)

lcd.clear()
lcd.write_string('Pi Monitor')
lcd.crlf()
lcd.write_string('LCD OK')

sleep(10)
lcd.clear()
