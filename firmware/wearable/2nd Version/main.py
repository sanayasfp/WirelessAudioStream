import json
import uasyncio as asyncio
from helper_utils import log, LogLevel, get_imei, generate_id, device_auth, blink_led, LedTime
from battery_utils import get_voltage, monitor_voltage, low_voltage
from gsm_utils import check_sim, check_network, make_call, call_event, send_sms, sms_event, list_reader, sms_reader
from gps_utils import get_gps

async def main():
    
    with open("config.json") as f:
        config = json.load(f)

    user_phone_number = config["USER_PHONE_NUMBER"]
    call_phone_number = config["CALL_PHONE_NUMBER"]
    sms_phone_number = config["SMS_PHONE_NUMBER"]
    authentication_status = config["AUTHENTICATION"]
    user_password = config["USER_PASSWORD"]

    blink_led(LedTime.ON, 1)
    device_imei = get_imei()
    log(LogLevel.DEBUG,"Initialization | DEVICE IMEI: {}, AUTHENTICATION: {}, USER_PASSWORD: {}".format(device_imei, authentication_status, user_password))

    network_status = None
    device_id = None
    
    # Set initial value for previous_percentage
    previous_percentage = 0 
    voltage_status = False
    
    # Check for SIM Card
    sim_status = await check_sim()
    if not sim_status:
            sim_status = await check_sim()
            
    while sim_status:  # Add timeout for sim status retries  || and retry_count_sim < 5

        # Check for Network
        network_status = await check_network()
        if not network_status:
            network_status = await check_network()

        while network_status:  # Add timeout for network status retries || and retry_count_network < 5
            if authentication_status ==0:
                init_message = "DEVCE INITIALISATION | ID: {}".format(device_imei)
                await send_sms(sms_event, user_phone_number, init_message)
                auth = await device_auth(device_imei,
                                        sms_phone_number,
                                        sms_event,
                                        send_sms,
                                        list_reader,
                                        get_voltage,
                                        get_gps)
                log(LogLevel.DEBUG,"Auth: {}".format(auth))
                if auth is not None:
                    authentication_status, user_password = auth
                    await list_reader()
            
            elif authentication_status ==1 and user_password =="":
                restart_message = "DEVICE RESTART | ID: {}".format(device_imei)
                await send_sms(sms_event, user_phone_number, restart_message)
                auth = await device_auth(device_imei,
                        sms_phone_number,
                        sms_event,
                        send_sms,
                        list_reader,
                        get_voltage,
                        get_gps)
                log(LogLevel.DEBUG,"Auth: {}".format(auth))
                if auth is not None:
                    authentication_status, user_password = auth
                    await list_reader()
                
            elif authentication_status ==1 and user_password is not "":
                restart_message = "DEVICE AUTHENTICATED | ID: {}".format(device_imei)
                await send_sms(sms_event, user_phone_number, restart_message)
                
                device_id = generate_id(device_imei,user_password)
                call_task = asyncio.create_task(make_call(call_event,call_phone_number))
                low_voltage_task = asyncio.create_task(low_voltage(device_id,sms_phone_number))
                #monitor_voltage_task = asyncio.create_task(monitor_voltage(previous_percentage,device_id,sms_phone_number))
                
                voltage_status = await low_voltage_task
                if voltage_status:
                    low_voltage_message = "LOW VOLTAGE DEVICE | ID: {}".format(device_imei)
                    await send_sms(sms_event, user_phone_number, low_voltage_message)
                    #monitor_voltage_task.cancel()
                    call_task.cancel()
            
            await asyncio.sleep(10)

    while True:
        await asyncio.sleep(1)
    
asyncio.run(main())
