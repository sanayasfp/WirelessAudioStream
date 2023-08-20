import gps
import uasyncio as asyncio
from helper_utils import log, LogLevel

# Get online
import cellular

async def get_agps_location():
    cellular.gprs("internet", "", "")
    # Import agps (download client if necessary)
    try:
        import agps
    except ImportError:
        import upip
        upip.install("micropython-agps")
        import agps

    # Get your token from https://unwiredlabs.com
    token_unwiredlabs = "pk.b151e6a4b218b87b549bf0b9701ea43f"
    #openCellid Token from https://my.opencellid.org/
    token_openCellid = "pk.76188ceeec8323bb4ad1f0f4be178fb0"

    agps_location = agps.get_location_opencellid(cellular.agps_station_data(), token_openCellid)
    print("AGPS location", agps_location)
    return agps_location


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
