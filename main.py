"""
Base class for connecting to WiFi and exposing GPIO to Prometheus
"""

import os
import sys
import network
import machine
from time import sleep, time
from binascii import hexlify
import ntptime
import gc
from typing import List

from config import SSID, WPA_KEY
from device_config import DEVICE_CONFIG
from utils import (
    wlan_status_code, logger, time_to_unix_time, prom_metric_str
)
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
        del devconf['pins']
        self.device: PrometheusDevice = PrometheusDevice(
            **devconf, pins=pins
        )
        del devconf
        del pins
        logger.debug('Set hostname to: %s' % self.device.hostname)
        network.hostname(self.device.hostname)
        logger.debug('Instantiate WLAN')
        self.wlan = network.WLAN(network.STA_IF)
        logger.debug('connect_wlan()')
        self.connect_wlan()
        logger.debug('hexlify mac')
        self.mac = hexlify(self.wlan.config('mac')).decode()
        logger.debug('MAC: %s' % self.mac)
        self.mac_colons = ':'.join(
            [self.mac[i:i + 2] for i in range(0, len(self.mac), 2)]
        )
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

    def _internal_metrics(self) -> str:
        rel: str = os.uname().release
        r: List[str] = rel.split('.')
        return \
            prom_metric_str(
                'python_info', 'Python platform information.',
                [(
                    {
                        'implementation': f'MicroPython {rel}',
                        'major': r[0],
                        'minor': r[1],
                        'patchlevel': r[2],
                        'version': rel
                    },
                    1.0
                )]
            ) + \
            prom_metric_str(
                'esp_info', 'Information about the underlying platform.',
                [(
                    {
                        'platform': sys.platform,
                        'unique_id': self.unique_id,
                        'mac': self.mac_colons,
                        'hostname': self.device.hostname
                    },
                    1.0
                )]
            ) + \
            prom_metric_str(
                'process_start_time_seconds',
                'Start time of the process since unix epoch in seconds.',
                [({}, time_to_unix_time(self.boot_time))]
            ) + \
            prom_metric_str(
                'process_uptime_seconds',
                'Number of seconds since the process started.',
                [({}, time() - self.boot_time)]
            )

    def prom_gpio_metric_str(self, name: str, help: str, attr_name: str) -> str:
        values = []
        pin: GpioSensor
        for pin in self.device.pins:
            values.append((
                {
                    'hostname': self.device.hostname,
                    'pin_name': pin.name,
                    'pin_number': pin.pin_num
                },
                getattr(pin, attr_name)
            ))
        return prom_metric_str(name, help, values)

    def handle_request(self, _) -> str:
        s: str = self._internal_metrics()
        s += self.prom_gpio_metric_str(
            'gpio_pin_is_on',
            'Whether the GPIO pin is on (1) or off (2)',
            'input_state'
        )
        s += self.prom_gpio_metric_str(
            'gpio_pin_on_seconds',
            'How many seconds the pin has been on; -1 if it is off.',
            'input_on_seconds'
        )
        s += self.prom_gpio_metric_str(
            'gpio_pin_off_seconds',
            'How many seconds the pin has been off; -1 if it is on.',
            'input_off_seconds'
        )
        s += self.prom_gpio_metric_str(
            'gpio_pin_seconds_since_on',
            'How many seconds since the pin last turned on.',
            'seconds_since_on'
        )
        s += self.prom_gpio_metric_str(
            'gpio_pin_seconds_since_off',
            'How many seconds since the pin last turned off.',
            'seconds_since_off'
        )
        return s + '\n'

    def run(self):
        logger.debug('Run method; call app.run()')
        app.url_map.append((['GET'], URLPattern('/'), self.handle_request))
        app.run(port=80)


if __name__ == '__main__':
    PromGpio().run()
