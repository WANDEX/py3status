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
    cache_timeout = 1
    format = "transmitted: {transmitted} received: {received} unreachable: {unreachable} "
    # :TODO
    # format_loss = "{transmitted}{received}{unreachable}"
    # format_separator = ", "
    # defaults: Google Public DNS: 8.8.8.8 or 8.8.4.4
    HOST = "8.8.8.8"
    INTERVAL = 4
    PACKETSIZE = 8
    GET_PACKET_LOSS = True
    # TIME_SLICE = 12 * 60
    TIME_SLICE = 1

    def post_config_hook(self):
        self.statistics = {"transmitted": 0, "received": 0, "unreachable": 0}
        self.time_iteration = count()

    def packet_loss(self):
        """One and only output method."""
        # stat = {}
        # for s in self.statistics.keys():
            # stat[s] = s
        stats = self.py3.time_in(self.cache_timeout)
        response = {
            "full_text": self.py3.safe_format(self.format, stats),
            "cached_until": self.py3.time_in(self.cache_timeout),
        }
        self._make_threads()

        # self.py3.safe_format(self.format_loss, {})

        # format_separator = self.py3.safe_format(self.format_separator)
        # format_loss = self.py3.composite_join(format_separator, self.statistics)
        # response["full_text"] = self.py3.safe_format(
            # self.format, {"format_loss": format_loss}
        # )
        return response

    def _calculate_packet_loss(self):
        """Calculate packet_loss %."""
        received = self.statistics.get("received", 0)
        transmitted = self.statistics.get("transmitted", 0)
        if received > 0 and transmitted > 0:
            return round(100 - (received / transmitted * 100), 2)

    def _update_statistics(self, key, get_packet_loss=GET_PACKET_LOSS):
        """Update ping statistics."""
        self.statistics["transmitted"] = self.statistics.get("transmitted", 0) + 1
        self.statistics[key] = self.statistics.get(key, 0) + 1
        if get_packet_loss:
            self.statistics["packet_loss"] = self.statistics.setdefault("packet_loss", 0)
            self.statistics["packet_loss"] = self._calculate_packet_loss()
        return self.statistics

    def _return_swith(self, returncode):
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

    def _reset_stats(self, dictionary):
        """Reset to 0 all dictionary values.

        Required parameter:
            dictionary: (dict, dictionary to reset)
        """
        for key in dictionary.keys():
            dictionary[key] = 0
        # print("\nValues are now set to 0.\n{0}\n".format(dictionary.items()))

    def _count_iteration(self, counter, string=""):
        """Iteration counter for recursive functions and loops.

        Required parameter:
            counter: (itertools.count(), global variable)
        Optional parameter:
            string: (str, optional message after iteration number)
        """
        iteration = next(counter)
        # print("{0}:{1} iteration.".format(str(iteration), string))
        return iteration

    def _subping(self, host_or_ip=HOST, interval=INTERVAL, packetsize=PACKETSIZE):
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
            return self._return_swith(ping.returncode)
        except subprocess.CalledProcessError:
            ping.kill()
            # suppress the original error, with "from None"
            raise RuntimeError("Something wrong here!") from None

    def _ping_loop(self):
        """Infinite _ping_loop."""
        while True:
            # print(self._subping())
            self._subping()

    def _time_loop(self, time_slice=TIME_SLICE):
        """Infinite _time_loop. Recursive function.

        Optional parameter:
            time_slice (int, last 't' minutes statistics storage)
        """
        self._count_iteration(self.time_iteration, "_time_loop()")
        time_slice *= 60
        while time_slice:
            mins, secs = divmod(time_slice, 60)
            timeformat = "{:02d}:{:02d}".format(mins, secs)
            # print(timeformat, end="\r")
            sleep(1)
            time_slice -= 1
        # print("Timer Has Ended.")
        self._reset_stats(self.statistics)
        self._time_loop()

    def _make_threads(self):
        """Create and start two main threads."""
        thread_ping = Thread(target=self._ping_loop, daemon=True)
        thread_time = Thread(target=self._time_loop, daemon=True)
        thread_ping.start()
        thread_time.start()
        thread_ping.join()
        thread_time.join()

# Packet_loss()._make_threads()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
