import gps
import uasyncio as asyncio
from helper_utils import log, LogLevel

# Get online
import cellular

class GpsContext:
    async def __aenter__(self):
        gps.on()
        return gps

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        gps.off()

async def get_gps() -> tuple:
    """
    Get the GPS location and satellite information.

    :return: A tuple containing the GPS location and satellite information.
    """
    async with GpsContext() as gps_instance:
        device_location = gps_instance.get_location()
        device_satellites = gps_instance.get_satellites()
        gps_time = gps_instance.time()
    log(LogLevel.INFO, "GPS DATA | Location: {}, Satellites: {}, Time: {}".format(device_location, device_satellites, gps_time))
    return device_location, device_satellites

async def get_agps():
    """
    Get the AGPS location using cell tower information.

    :return: The AGPS location.
    """
    cellular.gprs("apn", "wholesale", "")
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

    try:
        agps_location = agps.get_location_opencellid(cellular.agps_station_data(), token_openCellid)
        log(LogLevel.INFO, "AGPS location: {}".format(agps_location))
        return agps_location
    except Exception as e:
        # Log any errors that occur while getting the location.
        log(LogLevel.ERROR, "Error occurred while getting AGPS location: {}".format(e))
        return None