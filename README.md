# esp32-micropython-prometheus

[MicroPython](https://docs.micropython.org/en/latest/esp32/quickref.html) code for reading GPIO inputs on an ESP32 and exposing state to [Prometheus](https://prometheus.io/)

## What and Why?

We run [Prometheus](https://prometheus.io/) for monitoring our network and IT equipment, as well as some environmental sensors. We've got a few simple physical things that we'd like to integrate there, such as alarm contacts on the doors to tell if a door has been left open. The code here exposes metrics about the current state and recent changes of GPIO inputs on an ESP32, in a Prometheus-compatible format.

## Local Development / Flashing Setup

To get this code running on an ESP32, first set up a Python virtualenv with the required dependencies:

```commandline
python3 -mvenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Metrics Exposed

* `python_info` Python platform information.
* `esp_info` Information about the underlying platform.
* `process_start_time_seconds` Start time of the process since unix epoch in seconds.
* `process_uptime_seconds` Number of seconds since the process started.
* `gpio_pin_is_on` Whether the GPIO pin is on (1) or off (2)
* `gpio_pin_on_seconds` How many seconds the pin has been on; -1 if it is off.
* `gpio_pin_off_seconds` How many seconds the pin has been off; -1 if it is on.
* `gpio_pin_seconds_since_on` How many seconds since the pin last turned on.
* `gpio_pin_seconds_since_off` How many seconds since the pin last turned off.

Example Output:

```
# HELP python_info Python platform information.
# TYPE python_info gauge
python_info{implementation="MicroPython 1.20.0",major="1",minor="20",patchlevel="0",version="1.20.0"} 1.0
# HELP esp_info Information about the underlying platform.
# TYPE esp_info gauge
esp_info{hostname="esp32-gpiotest",mac="7c:9e:bd:61:ab:e4",platform="esp32",unique_id="7c9ebd61abe4"} 1.0
# HELP process_start_time_seconds Start time of the process since unix epoch in seconds.
# TYPE process_start_time_seconds gauge
process_start_time_seconds{} 1.691518e+09
# HELP process_uptime_seconds Number of seconds since the process started.
# TYPE process_uptime_seconds gauge
process_uptime_seconds{} 178.0
# HELP gpio_pin_is_on Whether the GPIO pin is on (1) or off (2)
# TYPE gpio_pin_is_on gauge
gpio_pin_is_on{hostname="esp32-gpiotest",pin_name="left",pin_number="32"} 0.0
gpio_pin_is_on{hostname="esp32-gpiotest",pin_name="right",pin_number="19"} 0.0
# HELP gpio_pin_on_seconds How many seconds the pin has been on; -1 if it is off.
# TYPE gpio_pin_on_seconds gauge
gpio_pin_on_seconds{hostname="esp32-gpiotest",pin_name="left",pin_number="32"} -1.0
gpio_pin_on_seconds{hostname="esp32-gpiotest",pin_name="right",pin_number="19"} -1.0
# HELP gpio_pin_off_seconds How many seconds the pin has been off; -1 if it is on.
# TYPE gpio_pin_off_seconds gauge
gpio_pin_off_seconds{hostname="esp32-gpiotest",pin_name="left",pin_number="32"} 153.0
gpio_pin_off_seconds{hostname="esp32-gpiotest",pin_name="right",pin_number="19"} 2.0
# HELP gpio_pin_seconds_since_on How many seconds since the pin last turned on.
# TYPE gpio_pin_seconds_since_on gauge
gpio_pin_seconds_since_on{hostname="esp32-gpiotest",pin_name="left",pin_number="32"} 157.0
gpio_pin_seconds_since_on{hostname="esp32-gpiotest",pin_name="right",pin_number="19"} 19.0
# HELP gpio_pin_seconds_since_off How many seconds since the pin last turned off.
# TYPE gpio_pin_seconds_since_off gauge
gpio_pin_seconds_since_off{hostname="esp32-gpiotest",pin_name="left",pin_number="32"} 153.0
gpio_pin_seconds_since_off{hostname="esp32-gpiotest",pin_name="right",pin_number="19"} 2.0
```

## Hardware Setup

This code is currently set up to read "dry contact" (i.e. switch/button/relay) inputs from GPIO. Each input can optionally have the internal pull up or pull down resistor enabled. Inputs are read via hardware interrupts for the fastest and most accurate results. Note that as per [ESP32 Pinout Reference: Which GPIO pins should you use? | Random Nerd Tutorials](https://randomnerdtutorials.com/esp32-pinout-reference-gpios/) some pins have specific states at boot; for the most reliable and safest use, you should use GPIOs 18 through 33 for inputs.

## Configuration and Flashing

### Prepping Brand New ESP32s

If you have a brand new ESP32, you'll first need to erase its flash and then flash MicroPython on it. You can find the MicroPython firmware binary along with installation instructions at  https://micropython.org/download/esp32-ota/ ; we're currently using 1.20.0.

### Getting an ESP32's WiFi MAC and Unique ID

Once you've got MicroPython installed, you'll need to know the unique_id of your board (and possibly the MAC address, if you have a MAC ACL on your WiFi). These can be found via rshell's REPL. Assuming your ESP32 is plugged in to your computer over USB and showed up as `/dev/ttyUSB0`, you can run (possibly with sudo, if your user isn't a member of the `uucp` group) `rshell -p /dev/ttyUSB0 repl` This should drop you into a REPL prompt (`>>> `) on the ESP32. You can then run:

```commandline
import micropython
import machine
import network
from ubinascii import hexlify
wlan = network.WLAN(network.STA_IF)
print('MAC address: %s' % hexlify(wlan.config('mac')).decode())
print('Unique ID: %s' % hexlify(machine.unique_id()).decode())
```

This should give you output showing the ESP32's WiFi MAC address and Unqiue ID as hex strings (they're the same on many ESP32s). Use Ctrl+x to exit the REPL and then `exit` to leave rshell.

### Configuring This Project

This project uses two configuration files: `config.py` which contains sensitive information such as your WiFi network name and key, and [device_config.py](device_config.py) which just lists all of your ESP32s by Unique ID and the GPIO configuration for each of them.

`config.py` can be created by copying [config.example.py](config.example.py) to `config.py` and changing the values as appropriate for your environment.

[device_config.py](device_config.py) configures the actual behavior of each device. Its format is a `DEVICE_CONFIG` dict where keys are the hex Unique ID (`machine.unique_id()`) for each board (as we retrieved in the previous step) and values are keyword arguments for the `PrometheusDevice` class in [promdevice.py](promdevice.py). Values for the `pins` list are keyword arguments for the `GpioSensor` class in [promdevice.py](promdevice.py). **Note** that if you do not specify a value for `hostname` on the `PrometheusDevice` class, the value for `name` is used for the DHCP hostname. This must be a string of less than 16 characters in length!

### Flashing the Code

Once you've added the appropriate configuration in [device_config.py](device_config.py), you should be able to run `./sync.py -p /dev/ttyUSB0` to sync the code and configuration from this repo to the device. When that's done and the device is ready to actually use, it's recommend to confirm that it's actually working right via the console logging: `rshell -p /dev/ttyUSB0 repl` to open the REPL and then Ctrl+d to soft-reboot the device and watch the log messages. When you're done, Ctrl+x to exit the REPL and then `exit` to leave rshell.
