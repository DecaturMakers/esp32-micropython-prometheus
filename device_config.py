"""
ESP32 device configuration

Keys are Unique ID for the board; values are dictionaries matching the
keyword arguments of the ``PrometheusDevice`` class in ``promdevice.py``.
Within the ``pins`` list, values are dictionaries matching the keyword arguments
of the ``GpioSensor`` class in ``promdevice.py``.
"""

DEVICE_CONFIG = {
    '0cb815c328dc': {
        'name': 'esp32-frontdoor',
        'pins': [
            {
                'name': 'latch',
                'pin_num': 32,
                'pull_up': True,
                'on_value': 1
            },
            {
                'name': 'leftmag',
                'pin_num': 19,
                'pull_up': True,
                'on_value': 0
            },
            {
                'name': 'rightmag',
                'pin_num': 18,
                'pull_up': True,
                'on_value': 0
            }
        ]
    },
    '0cb815c53148': {
        'name': 'esp32-sidedoor',
        'pins': [
            {
                'name': 'latch',
                'pin_num': 32,
                'pull_up': False,
                'on_value': 0
            },
            {
                'name': 'magnet',
                'pin_num': 19,
                'pull_up': True,
                'on_value': 0
            }
        ]
    }
}
