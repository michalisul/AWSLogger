# New Python file: AnalogSensor.py

# ADC sensor ESP32
# 3 purposes: refactoring, stabilizing, powering
# PINS:
# adc2: 32
# pwr: 27
# bat: 35

from machine import ADC, Pin
import utime as time


class AnalogSensor:

    def __init__(self, adc_pin, power_pin=0):
        self.adc = ADC(Pin(adc_pin))
        self.adc.atten(ADC.ATTN_11DB)
        self.power_pin = Pin(power_pin, Pin.OUT, Pin.PULL_DOWN, value=0)

    def analog_read(self, tries=3):
        reading = None
        timeout = 0
        self.power_pin.on()
        while reading is None or timeout <= tries:
            time.sleep_ms(500)
            try:
                reading = self.adc.read()
            except OSError:
                reading = None
            timeout = timeout + 1

        self.power_pin.off()

        return reading
