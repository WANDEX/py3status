# -*- coding: utf-8 -*-
"""
Track packet loss and host/ip availability over a period of time.

Counts and notifies about lost packets for a certain period of time.

Configuration parameters:
    cache_timeout: refresh interval for this module in seconds (default 5)
    format_prefix: Text preceding the 'format'. (default 'PL: ')
    format_postfix: Text following after 'format'. (default ' ')
    format: Display format for this module
        *(default 'PL: [\?color=packet_loss {unreachable} {packet_loss}]% ')*
    time_slice: The period of time in minutes for which you need to collect
        statistics. (default 60)
    get_packet_loss: If False -> {packet_loss} placeholder won't be calculated
        every 'interval' seconds. (default True)
    hide_if_zero: Hide module if the {unreachable} variable, which is the number of lost
        packets, is 0. (default False)
    host: Address of host/ip to ping. By default, Google Public DNS is used.
        (default '8.8.8.8')
    interval: Wait interval seconds between sending each packet. (default 4)
    packetsize: Number of data bytes to be sent + 8 bytes of ICMP header data.
        (default 8)
    thresholds: specify color thresholds to use
        *(default [(0, 'good'), (10, 'degraded'),
        (20, '#ffa500'), (30, 'bad')])*

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Notes:
    https://stackoverflow.com/questions/2953462/pinging-servers-in-python

Examples:
```
# default format with color thresholds based on the packet_loss placeholder
packet_loss {
    format = "[\?color=packet_loss {unreachable} {packet_loss}]%"
}

# show statistics in the default format, but without color thresholds
packet_loss {
    format = "{unreachable} {packet_loss}%"
}

# show detailed statistics with all available placeholders
packet_loss {
    format = '[\?color=packet_loss '
    format += 'transmitted: {transmitted} '
    format += 'received: {received} '
    format += 'unreachable: {unreachable} '
    format += 'packet_loss: {packet_loss}]%'
}

# get statistics for 24 hours
packet_loss {
    cache_timeout = 1
    format_prefix = " 24H: "
    format_postfix = ""
    time_slice = 1440
    get_packet_loss = True
    hide_if_zero = False
    host = "8.8.8.8"
    interval = 4
    packetsize = 8
}

```

@author WANDEX

SAMPLE OUTPUT
[
    {'full_text': 'PL: '},
    {'full_text': '1 33.33', 'color': '#FF0000'},
    {'full_text': '% '}
]

detailed
[
    {'full_text': 'PL: '},
    {'full_text': 'transmitted: 6'},
    {'full_text': 'received:' 4},
    {'full_text': 'unreachable: 2'},
    {'full_text': 'packet_loss: 33.33', 'color': '#FF0000'},
    {'full_text': '% '}
]
"""

from time import time, sleep
from subprocess import Popen, DEVNULL, CalledProcessError


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 5
    format_prefix = "PL: "
    format_postfix = " "
    format = "[\?color=packet_loss {unreachable} {packet_loss}]%"
    time_slice = 60
    get_packet_loss = True
    hide_if_zero = False
    host = "8.8.8.8" # default: Google Public DNS: 8.8.8.8 or 8.8.4.4
    interval = 4
    packetsize = 8
    thresholds = [
        (0, "good"),
        (10, "degraded"),
        (20, "#ffa500"),
        (30, "bad"),
    ]

    def post_config_hook(self):
        self.statistics = {"transmitted": 0, "received": 0, "unreachable": 0}
        self.minutes = self.time_slice * 60
        self.end_time = time() + self.minutes
        self.thresholds_init = self.py3.get_color_names_list(self.format)
        self.format = self.format_prefix + self.format + self.format_postfix

    def packet_loss(self):
        """One and only output method."""
        current_time = time()
        self._subping()
        if current_time > self.end_time:
            self._reset_stats(self.statistics)
            self.end_time = time() + self.minutes

        for x in self.thresholds_init:
            if x in self.statistics:
                self.py3.threshold_get_color(self.statistics[x], x)

        response = {"cached_until": self.py3.time_in(self.cache_timeout)}
        if self.hide_if_zero and self.statistics.get("unreachable", 0) == 0:
            response["full_text"] = ""
        else:
            response["full_text"] = self.py3.safe_format(self.format, self.statistics)
        return response

    def on_click(self, event):
        """Clear statistics."""
        button = event['button']
        format_string = 'CLEAR {button}'
        data = {'button': button}
        self.full_text = self.py3.safe_format(format_string, data)
        self._reset_stats(self.statistics)

    def _calculate_packet_loss(self):
        """Calculate packet_loss %."""
        received = self.statistics.get("received", 0)
        transmitted = self.statistics.get("transmitted", 0)
        return format(100 - (received / transmitted * 100), ".2f")

    def _update_statistics(self, key, get_packet_loss=get_packet_loss):
        """Update ping statistics."""
        self.statistics["transmitted"] = self.statistics.get("transmitted", 0) + 1
        self.statistics[key] = self.statistics.get(key, 0) + 1
        if get_packet_loss:
            self.statistics["packet_loss"] = self.statistics.setdefault("packet_loss", 0)
            self.statistics["packet_loss"] = self._calculate_packet_loss()
        return self.statistics

    def _reset_stats(self, dictionary):
        """Reset to 0 all dictionary values.

        Required parameter:
            dictionary: (dict, dictionary to reset)
        """
        for key in dictionary.keys():
            dictionary[key] = 0

    def _return_switch(self, returncode):
        """Gets returncode from _subping() and returns _update_statistics().

        Required parameter: returncode.
            returncode: "0" - success,
            returncode: "1", "2" - interprets like host unreachable. (see man ping)
        """
        switch = {
                0: "received",
                1: "unreachable",
                2: "unreachable",
        }
        return self._update_statistics(switch.get(returncode, None))

    def _subping(self, host_or_ip=host, interval=interval, packetsize=packetsize):
        """Calls system "ping" command as subprocess, and returns returncode.

        Optional parameters:
            host_or_ip (str, address of host/ip to ping),
            interval   (int, wait interval seconds between sending each packet),
            packetsize (int, number of data bytes to be sent + 8 bytes of ICMP
            header data)
        """
        command = ["ping", str(host_or_ip), "-c", "1", "-s", str(packetsize)]
        try:
            # Popen parameters: discard input, output and error messages
            ping = Popen(
                command,
                bufsize=1,
                stdin=DEVNULL,
                stdout=DEVNULL,
                stderr=DEVNULL,
            )
            sleep(interval)
            # to get returncode, but don't raise CalledProcessError()
            stdout, _ = ping.communicate()
            ping.poll()
            return self._return_switch(ping.returncode)
        except CalledProcessError:
            ping.kill()
            # suppress the original error, with "from None"
            raise RuntimeError("Something wrong here!") from None


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
