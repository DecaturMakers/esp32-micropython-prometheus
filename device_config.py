"""
ESP32 device configuration

Keys are Unique ID for the board; values are dictionaries matching the
keyword arguments of the ``PrometheusDevice`` class in ``promdevice.py``.
Within the ``pins`` list, values are dictionaries matching the keyword arguments
of the ``GpioSensor`` class in ``promdevice.py``.
"""

DEVICE_CONFIG = {
    '7c9ebd61abe4': {
        'name': 'esp32-gpiotest',
        'pins': [
            {
                'name': 'left',
                'pin_num': 32,
                'pull_up': False,
                'on_value': 0
            },
            {
                'name': 'right',
                'pin_num': 19,
                'pull_up': False,
                'on_value': 0
            }
        ]
    }
}
