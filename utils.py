import sys
import network


wlan_status_code = {
    network.STAT_IDLE: 'Idle',
    network.STAT_CONNECTING: 'Connecting',
    network.STAT_WRONG_PASSWORD: 'Wrong Password',
    network.STAT_NO_AP_FOUND: 'No AP Found',
    network.STAT_GOT_IP: 'Connected'
}


def time_to_unix_time(t: int) -> int:
    """
    Return a timestamp in integer seconds since January 1, 1970.
    """
    if sys.platform in ['esp32', 'esp8266']:
        # 946684800.0 is 2000-01-01 00:00:00 UTC which is used as the
        # epoch on ESP systems
        return t + 946684800
    else:
        return t


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
