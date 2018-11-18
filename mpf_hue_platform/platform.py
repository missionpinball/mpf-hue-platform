"""Platform to control the philips hue lights via the hue bridge."""
import asyncio
from phue import Bridge
import math

from mpf.core.platform import LightsPlatform
from mpf.platforms.interfaces.light_platform_interface import LightPlatformInterface
from typing import Callable, Tuple, List, Union


class HueLight:

    __slots__ = ["number", "dirty", "hardware_fade_ms", "colors", "log"]

    def __init__(self, number: str) -> None:
        """Initialise FAST LED."""
        self.number = number
        self.dirty = True
        self.colors = [0, 0, 0]     # type: List[Union[int, Callable[[int], Tuple[float, int]]]]

    def get_color_and_clear_dirty_flag(self):
        """Return current color."""
        result = ""
        self.dirty = False
        # send this as grb because the hardware will twist it again
        colors = []
        max_fade_ms = None
        for index in [0, 1, 2]:
            color = self.colors[index]
            if callable(color):
                brightness, fade_ms = color(30000)  # pylint: disable-msg=not-callable
                if not max_fade_ms or max_fade_ms > fade_ms:
                    max_fade_ms = fade_ms
                colors.append(brightness)
                if fade_ms >= 30000:
                    self.dirty = True
            else:
                colors.append(0)

        return self._rgb_to_xy_and_bri(*colors), max_fade_ms

    @staticmethod
    def _enhance_color(normalized):
        if normalized > 0.04045:
            return math.pow( (normalized + 0.055) / (1.0 + 0.055), 2.4)
        else:
            return normalized / 12.92

    def _rgb_to_xy_and_bri(self, r, g, b):
        r_final = self._enhance_color(r)
        g_final = self._enhance_color(g)
        b_final = self._enhance_color(b)

        x = r_final * 0.649926 + g_final * 0.103455 + b_final * 0.197109
        y = r_final * 0.234327 + g_final * 0.743075 + b_final * 0.022598
        z = r_final * 0.000000 + g_final * 0.053077 + b_final * 1.035763

        if x + y + z == 0:
            return 0, 0, 0
        else:
            x_final = x / (x + y + z)
            y_final = y / (x + y + z)
            return x_final, y_final, y


class HueLightChannel(LightPlatformInterface):

    __slots__ = ["led", "channel"]

    def __init__(self, led: HueLight, channel) -> None:
        """Initialise light channel."""
        super().__init__("{}-{}".format(led.number, channel))
        self.led = led
        self.channel = int(channel)

    def set_fade(self, color_and_fade_callback: Callable[[int], Tuple[float, int]]):
        """Set brightness via callback."""
        self.led.dirty = True
        self.led.colors[self.channel] = color_and_fade_callback

    @staticmethod
    def get_board_name():
        """Return the board of this light."""
        return "Philips Hue"


class HueHardwarePlatform(LightsPlatform):

    """Control Philips Hue lights."""

    def __init__(self, machine):
        """Initialise platform."""
        super().__init__(machine)

        self.config = None      # type: dict
        self.leds = {}
        self.flag_led_tick_registered = False
        self.hue = None

    @asyncio.coroutine
    def initialize(self):
        """Initialise platform."""
        # load config
        self.config = self.machine.config_validator.validate_config("hue", self.machine.config.get('hue', {}))
        self.hue = Bridge(self.config['ip'])

    @classmethod
    def get_config_spec(cls):
        return "hue", """
__valid_in__: machine
ip: single|str|
        """

    def stop(self):
        """Stop platform."""
        if self.pi:
            self.pi = None

    @staticmethod
    def parse_light_number_to_channels(number: str, subtype: str):
        """Parse light number to a list of channels."""
        del subtype
        return [
            {
                "number": number + "-0"
            },
            {
                "number": number + "-1"
            },
            {
                "number": number + "-2"
            },
        ]

    def update_leds(self):
        """Update leds."""
        dirty_leds = [led for led in self.fast_leds.values() if led.dirty]

        for led in dirty_leds:
            (x, y, bri), fade_ms = led.get_color_and_clear_dirty_flag()

            if bri == 0:
                self.hue.set_light(led.number, 'on', False)
                return
            if not self.hue.get_light(led.number, 'on'):
                self.hue.set_light(led.number, 'on', True)
            self.hue.set_light(led.number, {'xy': (x, y), 'bri': bri, 'transitiontime': int(fade_ms / 100)})

    def configure_light(self, number: str, subtype: str, platform_settings: dict) -> "LightPlatformInterface":
        """Configure a hue light."""
        number_str, channel = number.split("-")
        if number_str not in self.leds:
            self.leds[number_str] = HueLight(number_str)
        if not self.flag_led_tick_registered:
            # Update leds every frame
            self.machine.clock.schedule_interval(self.update_leds,
                                                 1 / self.machine.config['mpf']['default_light_hw_update_hz'])
            self.flag_led_tick_registered = True

        return HueLightChannel(self.leds[number_str], channel)
