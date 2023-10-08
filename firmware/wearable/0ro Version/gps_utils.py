import gps
from config import log, LogLevel
import uasyncio as asyncio

class GpsContext:
    async def __aenter__(self):
        log(LogLevel.INFO, "Managing GPS connections...")
        gps.on()
        return gps

    async def __aexit__(self, exc_type, exc_value, traceback):
        gps.off()

async def get_gps() -> tuple:
    log(LogLevel.INFO, "Retrieving GPS location, satellite information, and time...")
    async with GpsContext() as gps_instance:
        location = satellites = gtime = None
        while location is None or satellites is None or gtime is None:
            location = gps_instance.get_location()
            satellites = gps_instance.get_satellites()
            gtime = gps_instance.time()
            await asyncio.sleep(1)

        log(LogLevel.INFO, "GPS data | Location: {}, Satellites: {}, Time: {}".format(location, satellites, gtime))
        return location, satellites, gtime