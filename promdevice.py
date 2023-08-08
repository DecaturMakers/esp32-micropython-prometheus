import sys
from machine import Pin
from typing import List, Optional
from time import time

from utils import logger


class GpioSensor:

    def __init__(
        self, name: str, pin_num: int, pull_up: bool = False,
        pull_down: bool = False, on_value: int = 1
    ):
        """
        Defines a single GPIO pin that we want to monitor.

        :param name: Friendly name of the pin, to use as a prometheus label
        :param pin_num: GPIO pin number
        :param pull_up: Whether to enable the internal pull-up resistor;
          mutually exclusive with ``pull_down``
        :param pull_down: Whether to enable the internal pull-down resistor;
          mutually exclusive with ``pull_up``
        :param on_value: The value (1 or 0) when the pin is in an "on" state
        """
        assert not (pull_down and pull_up), \
            "pull_up and pull_down are mutually exclusive"
        self.name: str = name
        self.pin_num: int = pin_num
        self.pull_up: bool = pull_up
        self.pull_down: bool = pull_down
        self.on_value: int = on_value
        logger.info(
            'Instantiating GpioSensor "%s" on pin %d (pull_up=%s pull_down=%s '
            'on_value=%d)', self.name, self.pin_num, self.pull_up,
            self.pull_down, self.on_value
        )
        self._input_state: int = -1
        self._input_on_time: float = -1
        self._input_off_time: float = -1
        pull = None
        if self.pull_up:
            pull = Pin.PULL_UP
        elif self.pull_down:
            pull = Pin.PULL_DOWN
        self.pin: Pin = Pin(self.pin_num, mode=Pin.IN, pull=pull)
        logger.debug('Instantiated pin %s', self.pin)
        self.pin.irq(
            handler=self.handle_change,
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING
        )
        if self.pin.value() == self.on_value:
            self.set_input_on(self.pin)
        else:
            self.set_input_off(self.pin)

    @property
    def input_on_seconds(self) -> float:
        if self._input_state == 1:
            return self.seconds_since_on
        return -1

    @property
    def input_off_seconds(self) -> float:
        if self._input_state == 0:
            return self.seconds_since_off
        return -1

    @property
    def input_state(self) -> int:
        return self._input_state

    @property
    def seconds_since_on(self) -> float:
        if self._input_on_time == -1:
            return -1
        return time() - self._input_on_time

    @property
    def seconds_since_off(self) -> float:
        if self._input_off_time == -1:
            return -1
        return time() - self._input_off_time

    def set_input_on(self, pin: Pin):
        logger.debug('Pin %s is ON', pin)
        self._input_state = 1
        self._input_on_time = time()

    def set_input_off(self, pin: Pin):
        logger.debug('Pin %s is OFF', pin)
        self._input_state = 0
        self._input_off_time = time()

    def handle_change(self, pin: Pin):
        if pin.value() == self.on_value:
            self.set_input_on(pin)
        else:
            self.set_input_off(pin)


class PrometheusDevice:

    def __init__(
        self, name: str, pins: List[GpioSensor], hostname: Optional[str] = None
    ):
        self.name: str = name
        self.pins: List[GpioSensor] = pins
        if hostname:
            self.hostname: str = hostname
        else:
            self.hostname: str = name
        assert len(self.hostname) < 16,\
            "Hostname must be less than 16 characters"
