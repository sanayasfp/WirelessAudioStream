import json
import machine
import gps
import cellular
import uasyncio as asyncio
from config import generate_device_id, blink_led, log, LogLevel
from gps_utils import get_gps
from gsm_utils import sms_handler, r_handler, call_handler, send_sms, receive_auth, make_call, initiate_gsm_event, check_sim_card, check_network, check_auth, request_auth
from battery_utils import voltage_decreased_by_10_percent, monitor_battery_voltage

# Load configuration values from the JSON file
with open("config.json") as f:
    config = json.load(f)

user_phone_number = config["USER_PHONE_NUMBER"]
server_phone_number = config["SERVER_PHONE_NUMBER"]
password = None
device_id = None
sleep_time = config["SLEEP_TIME"]
low_voltage_threshold = config["LOW_VOLTAGE_THRESHOLD"]


async def main():
    
    # Define a global variable for authentication status
    sim = False
    network = False
    check = False
    authentication_task = None
    confirmation_task = None

    #Initialize main function
    log(LogLevel.INFO, "Starting main function...")
    
    #Retrieve IMEI 
    imei = cellular.get_imei()
    log(LogLevel.INFO, "IMEI: {}".format(imei))

    # create GPS Task
    gps_task = asyncio.create_task(get_gps())

    # Check SIM card 
    while not sim:
        sim = await check_sim_card()
    if sim:
        # Check for Network,
        while not network:
            network = await check_network()
    if network:
        # Request authentication
        authentication_task = asyncio.create_task(request_auth(imei, server_phone_number, gps_task))

        if authentication_task:
            # Check authentication
            confirmation_task = asyncio.create_task(check_auth(imei))
            
    check = True

    # If the authentication is successful, start the other tasks
    if check:
        log(LogLevel.INFO, "Device check status: {}".format(check))

        # Cancel the authentication_task when check is granted
        authentication_task.cancel()
        confirmation_task.cancel()
        
        # Generate device_id
        device_id = generate_device_id(imei, password)
        log(LogLevel.INFO, "Computed Device Id: {}".format(device_id))

        #Monitor Battery
        asyncio.create_task(monitor_battery_voltage(server_phone_number, device_id, low_voltage_threshold, gps_task))

        #Initiate GSM Events
        asyncio.create_task(initiate_gsm_event(server_phone_number, user_phone_number, device_id, gps_task))


    while True:
        await asyncio.sleep(1)

asyncio.run(main())