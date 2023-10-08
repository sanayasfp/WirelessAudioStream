import json
import uasyncio as asyncio
from helper_utils import log, LogLevel, get_imei, generate_id, device_auth
from battery_utils import get_voltage, monitor_voltage, low_voltage
from gsm_utils import check_sim, check_network, make_call, call_event, send_sms, sms_event, list_reader, sms_reader
from gps_utils import get_gps

with open("config.json") as f:
    config = json.load(f)

user_phone_number = config["USER_PHONE_NUMBER"]
server_phone_number = config["SERVER_PHONE_NUMBER"]
previous_percentage = None

async def main():

    device_imei = get_imei()
    log(LogLevel.DEBUG, "Initialization | DEVICE IMEI: {}".format(device_imei))

    sim_status = await check_sim()
    network_status = None
    authentication_status = False
    device_id = None
    user_password = None
    voltage_status = None

    while sim_status:
        network_status = await check_network()

        while network_status:
            if authentication_status is False:
                auth = await device_auth(device_imei, server_phone_number, sms_event, send_sms, list_reader, get_voltage, get_gps)
                if auth is not None:
                    authentication_status, user_password = auth
                    #sms_task = asyncio.create_task(list_reader())
                
            
            await asyncio.sleep(10)

            if authentication_status is True and user_password is not None:
                device_id = generate_id(device_imei, user_password)
                monitor_voltage_task = asyncio.create_task(monitor_voltage(previous_percentage, device_id, server_phone_number))
                call_task = asyncio.create_task(make_call(call_event, user_phone_number))
                low_voltage_task = asyncio.create_task(low_voltage(device_id, server_phone_number))

                voltage_status = await low_voltage_task

                if voltage_status:
                    monitor_voltage_task.cancel()
                    call_task.cancel()
                    #sms_task.cancel()

    while True:
        await asyncio.sleep(1)

asyncio.run(main())
