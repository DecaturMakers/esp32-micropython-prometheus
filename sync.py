#!/usr/bin/env python

import sys
import os
import argparse
import logging
from binascii import hexlify
from hashlib import sha256

from rshell.main import (
    connect_serial, autoconnect, UART_BUFFER_SIZE, DeviceError, DEVS,
    listdir, cp
)
import rshell.main as rmain
from device_config import DEVICE_CONFIG

rmain.ASCII_XFER = True

FORMAT = "[%(asctime)s %(levelname)s] %(message)s"
logging.basicConfig(level=logging.WARNING, format=FORMAT)
logger = logging.getLogger()


def get_mac_address():
    import micropython
    import network
    from ubinascii import hexlify
    wlan = network.WLAN(network.STA_IF)
    return hexlify(wlan.config('mac')).decode()


def get_unique_id():
    import machine
    from ubinascii import hexlify
    return hexlify(machine.unique_id()).decode()


def get_file_md5_sums():
    import os
    from uhashlib import sha256
    from ubinascii import hexlify
    results = {}
    for f in os.listdir('/'):
        with open(f, 'rb') as fh:
            results[f] = hexlify(sha256(fh.read()).digest())
    return results


class BoardSyncer:

    def __init__(self, port):
        global BUFFER_SIZE, ASCII_XFER
        BUFFER_SIZE = UART_BUFFER_SIZE
        ASCII_XFER = True
        try:
            connect_serial(port, baud=115200, wait=0)
        except DeviceError as err:
            print(err)
        autoconnect()
        self.device = DEVS[0]
        print('#' * 60)

    def sync(self):
        unique_id = self.device.remote(get_unique_id).decode().strip()
        mac = self.device.remote(get_mac_address).decode().strip()
        logger.warning('Connected to board with Unique ID %s (MAC %s)', unique_id, mac)
        if unique_id in DEVICE_CONFIG:
            logger.info('Board IS known and configured.')
        else:
            logger.warning('Board is not configured in PER_BOARD_FILES.')
        # when looking at stats, we only care about size and mtime
        dev_files = self.device.remote_eval(get_file_md5_sums)
        logger.debug('Device files: %s', dev_files)
        local_files = {}
        for f in listdir('./'):
            if not os.path.isfile(f):
                continue
            with open(f, 'rb') as fh:
                local_files[f] = hexlify(sha256(fh.read()).digest())
        logger.debug('Local files: %s', local_files)
        desired_files = {
            'config.py': 'config.py',
            'device_config.py': 'device_config.py',
            'main.py': 'main.py',
            'promdevice.py': 'promdevice.py',
            'utils.py': 'utils.py',
            'micro-typing.py': 'typing.py',
            'microdot.py': 'microdot.py'
        }
        logger.debug('Desired files: %s', desired_files)
        for src, dest in desired_files.items():
            if dev_files.get(dest, None) == local_files[src]:
                logger.info(
                    'Device file %s already matches local file %s; no changes',
                    dest, src
                )
                continue
            logger.debug('Device file %s: %s', dest, dev_files.get(dest, None))
            logger.debug('Source file %s: %s', src, local_files.get(src, None))
            dest = '/pyboard/' + dest
            logger.info('cp %s %s', src, dest)
            cp(src, dest)
        self.device.close()


def set_log_info():
    """set logger level to INFO"""
    set_log_level_format(logging.INFO,
                         '%(asctime)s %(levelname)s:%(name)s:%(message)s')


def set_log_debug():
    """set logger level to DEBUG, and debug-level output format"""
    set_log_level_format(
        logging.DEBUG,
        "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
        "%(name)s.%(funcName)s() ] %(message)s"
    )


def set_log_level_format(level, format):
    """
    Set logger level and format.

    :param level: logging level; see the :py:mod:`logging` constants.
    :type level: int
    :param format: logging formatter format string
    :type format: str
    """
    formatter = logging.Formatter(fmt=format)
    logger.handlers[0].setFormatter(formatter)
    logger.setLevel(level)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description='Automatically sync to board')
    p.add_argument(
        '-p', '--port', action='store', type=str, dest='port',
        default='/dev/ttyUSB0',
        help='path to device port (default: /dev/ttyUSB0)'
    )
    p.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                   default=False, help='debug-level output.')
    args = p.parse_args(sys.argv[1:])
    # set logging level
    if args.verbose:
        set_log_debug()
    else:
        set_log_info()
    BoardSyncer(args.port).sync()
