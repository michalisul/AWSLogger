import network
import esp
import gc
import utime as time
from machine import unique_id, reset
from ntptime import settime
import ubinascii as binascii
from robust import MQTTClient
import SECRET

ssid = SECRET.ssid
password = SECRET.password

device_id = binascii.hexlify(unique_id())
div_to_epoch = 946684800


# AWS credentials
end_point = SECRET.end_point
key_path = SECRET.key_path
cert_path = SECRET.cert_path

shadow_update = b'$aws/things/AWSTutLogger/shadow/update'
shadow_accepted = b'$aws/things/AWSTutLogger/shadow/update/accepted'
shadow_rejected = b'$aws/things/AWSTutLogger/shadow/update/rejected'
get_shadow = b'$aws/things/AWSTutLogger/shadow/get' # can be used if we want to check when last update was sent

try:
    with open(key_path, 'r') as f:
        key = f.read()

    with open(cert_path, 'r') as f:
        cert = f.read()

except OSError:
    print("File error!")

client = MQTTClient(device_id, end_point, port=8883, keepalive=4000, ssl=True, ssl_params={"key":key, "cert":cert, "server_side":False})


def sub_cb(topic, msg):
    print("Payload received on topic: " + topic.decode("utf-8") + " with message: " + msg.decode("utf-8"))
    if topic == shadow_accepted:
        print("Message accepted by the server")
        print("+++++++++++++++++")
        print("")
    elif topic == shadow_rejected:
        print("Message rejected by the server")
        print("+++++++++++++++++")
        print("")


def connect_and_subscribe():
    client.connect()
    client.set_callback(sub_cb)
    client.subscribe(shadow_accepted)
    client.subscribe(shadow_rejected)
    print('Connected to MQTT broker, subscribed to topics')
    return client


def restart_and_reconnect():
    print('Failed to connect to MQTT broker. Reconnecting...')
    time.sleep(5)
    reset()


def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...') # TODO: Try????
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    time.sleep(1)
    try:
        settime()
        epoch = time.time() + div_to_epoch
        print("Time: ", time.localtime())
        print("Epoch: ", epoch)
    except OSError:
        pass


def ap_status(status: bool):
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(status)
    print('Access point status', ap_if.active())
    return status


def no_debug():
    esp.osdebug(None)


def garbage():
    gc.collect()


no_debug()
ap_status(False)
do_connect()
garbage()


try:
    connect_and_subscribe()
except OSError as err:
    print("Error: ", err)
    restart_and_reconnect()