"""
Base class for connecting to WiFi and exposing GPIO to Prometheus
"""

import network
import machine
from time import sleep, time
from binascii import hexlify
import ntptime
import gc

from config import SSID, WPA_KEY
from device_config import DEVICE_CONFIG
from utils import wlan_status_code, logger
from promdevice import PrometheusDevice, GpioSensor
from microdot import Microdot, URLPattern

try:
    import ujson
except ImportError:
    import json as ujson

gc.collect()  # enable garbage collection

app = Microdot()


class PromGpio:

    def __init__(self):
        logger.debug("Init")
        self.unique_id: str = hexlify(machine.unique_id()).decode()
        devconf = DEVICE_CONFIG[self.unique_id]
        pins = [GpioSensor(**x) for x in devconf.get('pins', [])]
        devconf['pins'] = pins
        self.device: PrometheusDevice = PrometheusDevice(**devconf)
        hostname = devconf.get('hostname')
        logger.debug('Set hostname to: %s' % hostname)
        network.hostname(self.device.hostname)
        logger.debug('Instantiate WLAN')
        self.wlan = network.WLAN(network.STA_IF)
        logger.debug('connect_wlan()')
        self.connect_wlan()
        logger.debug('hexlify mac')
        self.mac = hexlify(self.wlan.config('mac')).decode()
        logger.debug('MAC: %s' % self.mac)
        self._set_time_from_ntp()
        self.boot_time = time()

    def _set_time_from_ntp(self):
        logger.debug('Setting time from NTP...')
        logger.debug('Current time: %s' % time())
        for _ in range(0, 5):
            try:
                ntptime.settime()
                logger.debug('Time set via NTP; new time: %s' % time())
                return
            except Exception as ex:
                logger.debug(
                    'Failed setting time via NTP: %s; try again in 5s' % ex
                )
                sleep(5)
        logger.debug('ERROR: Could not set time via NTP')

    def connect_wlan(self):
        logger.debug('set wlan to active')
        self.wlan.active(True)
        logger.debug('test if wlan is connected')
        if not self.wlan.isconnected():
            logger.debug('connecting to network...')
            self.wlan.connect(SSID, WPA_KEY)
            logger.debug('MAC: %s' % hexlify(self.wlan.config('mac')).decode())
            for _ in range(0, 60):
                if self.wlan.isconnected():
                    logger.debug('WLAN is connected')
                    break
                stat = self.wlan.status()
                logger.debug(
                    'WLAN is not connected; sleep 1s; status=%s' %
                    wlan_status_code.get(stat, stat)
                )
                sleep(1)
            else:
                logger.debug('Could not connect to WLAN after 15s; reset')
                machine.reset()
        print('network config:', self.wlan.ifconfig())

    def handle_request(self, _):
        return 'The only thing here is /metrics'

    def run(self):
        logger.debug('Run method; call app.run()')
        app.url_map.append((['GET'], URLPattern('/'), self.handle_request))
        app.run(port=80)


if __name__ == '__main__':
    PromGpio().run()
