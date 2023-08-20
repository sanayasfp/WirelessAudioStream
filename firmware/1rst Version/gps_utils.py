import gps
import uasyncio as asyncio
from helper_utils import log, LogLevel

class GpsContext:
    async def __aenter__(self):
        gps.on()
        return gps

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        gps.off()

async def get_gps() -> tuple:
    async with GpsContext() as gps_instance:
        device_location = gps_instance.get_location()
        device_satellites = gps_instance.get_satellites()
        gps_time = gps_instance.time()
    log(LogLevel.INFO, "GPS DATA | Location: {}, Satellites: {}, Time: {}".format(device_location, device_satellites, gps_time))
    return device_location, device_satellites
