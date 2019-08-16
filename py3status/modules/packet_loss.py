# -*- coding: utf-8 -*-
"""
Keep track of packet loss over a period of time.

Counts lost packets during last one-, five-, and fifteen-minute periods.

Requires:
    ping3 # https://github.com/kyan001/ping3 | to install - "pip install ping3"

Notes:
    https://stackoverflow.com/questions/2953462/pinging-servers-in-python
"""


import ping3


class Py3status:
    """
    """

    # available configuration parameters
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

    def packet_loss(self):
        host = "google.com"

        for x in self.thresholds_init:
            if x in self.load_data:
                self.py3.threshold_get_color(self.load_data[x], x)

        return {
            "full_text": self.py3.safe_format(self.format, self.load_data),
            "cached_until": self.py3.time_in(self.cache_timeout),
            # "full_text": " Hello World! ",
            # "cached_until": self.py3.CACHE_FOREVER
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
