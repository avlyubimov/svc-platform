#!/usr/bin/env python3

import json
import subprocess


def main() -> int:
    devices = json.loads(
        subprocess.check_output(
            ["xcrun", "simctl", "list", "devices", "available", "-j"],
            text=True,
        )
    )
    for runtime_devices in devices["devices"].values():
        for device in runtime_devices:
            if device["name"].startswith("iPhone") and device["isAvailable"]:
                print(device["udid"])
                return 0
    raise SystemExit("no available iPhone simulator")


if __name__ == "__main__":
    raise SystemExit(main())
