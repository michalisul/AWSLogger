# main loop file:
#
# ADC pin: 32
# Battery pin: 35
# Touch pin: 14
# Built in LED: 13

from machine import ADC, TouchPad, Pin, Timer, RTC, unique_id, reset
import ujson as json
import ubinascii as binascii
import utime as time
from analog_sensor import AnalogSensor

# hardware definitions
adc_pin = 32
battery_pin = 35
touch_pin = 14
led_pin = 13

# initializers
adc = AnalogSensor(adc_pin)
battery = AnalogSensor(battery_pin)
touch = TouchPad(Pin(14))
led = Pin(13, Pin.OUT, value=0)
publish_timer = Timer(0)
rtc = RTC()
device_id = binascii.hexlify(unique_id())

div_to_epoch = 946684800 # Saturday, January 1, 2000 12:00:00 AM vs Thursday, January 1, 1970 12:00:00 AM

def translate(value, left_min, left_max, right_min, right_max):
    # Figure out how 'wide' each range is
    left_span = left_max - left_min
    right_span = right_max - right_min

    # Convert the left range into a 0-1 range (float)
    value_scaled = float(value - left_min) / float(left_span)

    # Convert the 0-1 range into a value in the right range.
    trans_value = round(right_min + (value_scaled * right_span))

    return trans_value


def iso_time(t=None):
    iso_datetime = "%04u-%02u-%02uT%02u:%02u:%02u" % time.localtime(t)[0:6]
    return iso_datetime


def unix_epoch():
    epoch = time.time() + div_to_epoch
    return epoch


def get_adc_reading(max, min):
    raw_data = adc.analog_read()
    data = translate(raw_data, max, min, 1000, 0)  # max: 4095, min: 0 or max: 0, min: 4095
    return data


def get_battery_voltage():
    raw_voltage = 2 * battery.analog_read()
    voltage = raw_voltage / 1000
    return voltage


def get_touch():
    touch_data = touch.read()
    return touch_data


def prepare_payload():
    epoch = unix_epoch()
    date_time = iso_time()
    battery_data = get_battery_voltage()
    adc_data = get_adc_reading(4095, 0)
    touch_data = get_touch()

    data_payload = {
        "state": {
            "reported": {
                "device_id": device_id,
                "timestamp": epoch,
                "date_time": date_time,
                "battery_data": battery_data,
                "adc_data": adc_data,
                "touch_data": touch_data,
            }
        }
    }

    try:
        payload = json.dumps(data_payload)
        return payload
    except OSError:
        return


def publish_payload():
    led.on()
    msg = prepare_payload()

    try:
        client.publish(shadow_update, msg)
        print("Message sent: ", msg)
        led.off()
        return msg
    except OSError as err:
        print("Error: ", err)
        publish_timer.deinit()
        time.sleep(5)
        reset()



def publish_data_callback(timer):
    publish_payload()
    return timer


publish_timer.init(period=6000, mode=Timer.PERIODIC, callback=publish_data_callback) # 6s period


while True:
    try:
        client.check_msg()
        time.sleep_ms(500)
    except (OSError, KeyboardInterrupt) as err:
        print("Error: ", err)
        publish_timer.deinit()
        # restart_and_reconnect()

