# -*- coding: utf-8 -*-
"""
Keep track of packet loss over a period of time.

Counts lost packets during last one-, five-, and fifteen-minute periods.

Requires:

Notes:
    https://stackoverflow.com/questions/2953462/pinging-servers-in-python
"""


import subprocess
from itertools import count
from threading import Thread
from time import sleep


class Py3status:
    """
    """

    # available configuration parameters
    # defaults: Google Public DNS: 8.8.8.8 or 8.8.4.4
    HOST = "8.8.8.8"
    INTERVAL = 4
    PACKETSIZE = 8
    GET_PACKET_LOSS = True
    # TIME_SLICE = 12 * 60
    TIME_SLICE = 1

    time_iteration = count()

    statistics = {"transmitted": 0, "received": 0, "unreachable": 0}
    cache_timeout = 5
    format = (
        "packet_loss [\?color=1avg {1min}] " "[\?color=5avg {5min}] [\?color=15avg {15min}]"
    )
    thresholds = [
        (0, "#9dd7fb"),
        (20, "good"),
        (40, "degraded"),
        (60, "#ffa500"),
        (80, "bad"),
    ]

    class Meta:
        update_config = {
            "update_placeholder_format": [
                {
                    "placeholder_formats": {
                        "1min": ":.2f",
                        "5min": ":.2f",
                        "15min": ":.2f",
                        "1avg": ":.1f",
                        "5avg": ":.1f",
                        "15avg": ":.1f",
                    },
                    "format_strings": ["format"],
                }
            ]
        }

    def post_config_hook(self):
        self.load_data = {}
        self.thresholds_init = self.py3.get_color_names_list(self.format)





    def calculate_packet_loss(self):
        """Calculate packet_loss %."""
        received = self.statistics.get("received", 0)
        transmitted = self.statistics.get("transmitted", 0)
        return round(100 - (received / transmitted * 100), 2)

    def update_statistics(self, key, get_packet_loss=GET_PACKET_LOSS):
        """Update ping statistics."""
        self.statistics["transmitted"] = self.statistics.get("transmitted", 0) + 1
        self.statistics[key] = self.statistics.get(key, 0) + 1
        if get_packet_loss:
            self.statistics["packet_loss"] = self.statistics.setdefault("packet_loss", 0)
            self.statistics["packet_loss"] = self.calculate_packet_loss()
        return self.statistics

    def return_swith(self, returncode):
        """Gets returncode from subping() and returns update_statistics().

        Required parameter: returncode.
            returncode: "0" - success,
            returncode: "1", "2" - interprets like host unreachable. (see man ping)
        """
        switch = {
                0: "received",
                1: "unreachable",
                2: "unreachable",
        }
        return self.update_statistics(switch.get(returncode, None))

    def reset_stats(self, dictionary):
        """Reset to 0 all dictionary values.

        Required parameter:
            dictionary: (dict, dictionary to reset)
        """
        for key in dictionary.keys():
            dictionary[key] = 0
        print("\nValues are now set to 0.\n{0}\n".format(dictionary.items()))

    def count_iteration(self, counter, string=""):
        """Iteration counter for recursive functions and loops.

        Required parameter:
            counter: (itertools.count(), global variable)
        Optional parameter:
            string: (str, optional message after iteration number)
        """
        iteration = next(counter)
        print("{0}:{1} iteration.".format(str(iteration), string))
        return iteration

    def subping(self, host_or_ip=HOST, interval=INTERVAL, packetsize=PACKETSIZE):
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
            ping = subprocess.Popen(
                command,
                bufsize=1,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            sleep(interval)
            # to get returncode, but don't raise CalledProcessError()
            stdout, _ = ping.communicate()
            ping.poll()
            return self.return_swith(ping.returncode)
        except subprocess.CalledProcessError:
            ping.kill()
            # suppress the original error, with "from None"
            raise RuntimeError("Something wrong here!") from None

    def ping_loop(self):
        """Infinite ping_loop."""
        while True:
            print(self.subping())

    def time_loop(self, time_slice=TIME_SLICE):
        """Infinite time_loop. Recursive function.

        Optional parameter:
            time_slice (int, last 't' minutes statistics storage)
        """
        self.count_iteration(self.time_iteration, "time_loop()")
        time_slice *= 60
        while time_slice:
            mins, secs = divmod(time_slice, 60)
            timeformat = "{:02d}:{:02d}".format(mins, secs)
            print(timeformat, end="\r")
            sleep(1)
            time_slice -= 1
        print("Timer Has Ended.")
        self.reset_stats(self.statistics)
        self.time_loop()

    def make_threads(self):
        """Create and start two main threads."""
        thread_ping = Thread(target=self.ping_loop, daemon=True)
        thread_time = Thread(target=self.time_loop, daemon=True)
        thread_ping.start()
        thread_time.start()
        thread_ping.join()
        thread_time.join()


# Packet_loss().make_threads()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
