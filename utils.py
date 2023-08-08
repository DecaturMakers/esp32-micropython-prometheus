import sys
import network
import math
from typing import Union, List, Tuple, Dict, TYPE_CHECKING

INF = float("inf")
MINUS_INF = float("-inf")
NaN = float("NaN")

wlan_status_code = {
    network.STAT_IDLE: 'Idle',
    network.STAT_CONNECTING: 'Connecting',
    network.STAT_WRONG_PASSWORD: 'Wrong Password',
    network.STAT_NO_AP_FOUND: 'No AP Found',
    network.STAT_GOT_IP: 'Connected'
}


def prom_metric_str(
    name: str, help: str, values: List[Tuple[Dict, Union[int, float]]],
    metric_type: str = 'gauge'
) -> str:
    """
    Generate and return a Prometheus client-compatible exposition string for
    a given metric, which has one or more values.

    :param name: Prometheus metric name
    :param help: help/description string for the metric
    :param values: Current values for the metric, as a list of 2-tuples where
      the first item is a dictionary of labels and the second items is the
      integer or float value.
    :param metric_type: Metric type, i.e. gauge
    """
    s = '# HELP ' + name + ' ' + help + '\n' + \
        '# TYPE ' + name + ' ' + metric_type + '\n'
    labels: Dict
    value: Union[int, float]
    for labels, value in values:
        s += name + '{' + ','.join([
            f'{k}="{v}"' for k, v in sorted(labels.items())
        ]) + '} ' + floatToGoString(value) + '\n'
    return s


def time_to_unix_time(t: Union[int, float]) -> int:
    """
    Return a timestamp in integer seconds since January 1, 1970.
    """
    if sys.platform in ['esp32', 'esp8266']:
        # 946684800.0 is 2000-01-01 00:00:00 UTC which is used as the
        # epoch on ESP systems
        return int(t) + 946684800
    else:
        return int(t)


def floatToGoString(d) -> str:
    if d == 1:
        return '1.0'
    if d == 0:
        return '0.0'
    # from https://github.com/prometheus/client_python/blob/master/prometheus_client/utils.py#L8
    d = float(d)
    if d == INF:
        return '+Inf'
    elif d == MINUS_INF:
        return '-Inf'
    elif math.isnan(d):
        return 'NaN'
    else:
        s = repr(d)
        dot = s.find('.')
        # Go switches to exponents sooner than Python.
        # We only need to care about positive values for le/quantile.
        if d > 0 and dot > 6:
            mantissa = f'{s[0]}.{s[1:dot]}{s[dot + 1:]}'.rstrip('0.')
            return f'{mantissa}e+0{dot - 1}'
        return s


class Logger:
    """Stand-in for a real logging library"""

    def debug(self, *args):
        if len(args) == 0:
            print(args[0])
            return
        print(args[0] % args[1:])

    def info(self, *args):
        return self.debug(*args)

    def warning(self, *args):
        return self.debug(*args)

    def error(self, *args):
        return self.debug(*args)

    def critical(self, *args):
        return self.debug(*args)


logger = Logger()
