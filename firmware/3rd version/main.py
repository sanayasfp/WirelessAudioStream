import json
import uasyncio as asyncio
from machine import Pin
from helper_utils import log, LogLevel, get_imei, generate_id, device_auth, blink_led, LedTime
from battery_utils import get_voltage, low_voltage
from gsm_utils import check_sim, check_network, make_call, call_event, send_sms, sms_event, list_reader, sms_reader

# Function to detect button press
def is_button_pressed(button_pin):
    return button_pin.value()

async def main():
    with open("config.json") as f:
        config = json.load(f)

    user_phone_number = config["USER_PHONE_NUMBER"]
    call_phone_number = config["CALL_PHONE_NUMBER"]
    sms_phone_number = config["SMS_PHONE_NUMBER"]
    authentication_status = config["AUTHENTICATION"]
    user_password = config["USER_PASSWORD"]

    switch_pin = config["ON_OFF_BUTTON"]
    sos_pin = config["SOS_BUTTON"]

    on_off = Pin(switch_pin, Pin.IN)
    on_off_value = is_button_pressed(on_off)

    sos = Pin(sos_pin, Pin.IN)
    sos_value =is_button_pressed(sos)

    await blink_led(LedTime.ON, 2)
    device_imei = get_imei()
    log(LogLevel.DEBUG, "Initialization | DEVICE IMEI: {}, AUTHENTICATION: {}, USER_PASSWORD: {}, ON/OFF: {}, SOS: {}\n".format(device_imei, authentication_status, user_password, on_off_value, sos_value))

    network_status = None
    device_id = None
    voltage_status = False
    user_msg = 0

    sim_status = await check_sim()
    if not sim_status:
        sim_status = await check_sim()

    while sim_status:
        network_status = await check_network()
        if not network_status:
            network_status = await check_network()

        while network_status:
            if authentication_status == 0:
                await list_reader()
                init_message = "DEVICE INITIALISATION | IMEI: {}".format(device_imei)
                await send_sms(sms_event, user_phone_number, init_message)
                
                while authentication_status == 0:
                    auth = await device_auth(device_imei, sms_phone_number, sms_event, send_sms, list_reader, get_voltage)
                    log(LogLevel.DEBUG, "Auth: {}".format(auth))
                    if auth is not None:
                        authentication_status, user_password = auth
                    await list_reader()
                    await asyncio.sleep(30)

            elif authentication_status == 1 and user_password == "":
                await list_reader()
                init_message = "DEVICE RESTART | IMEI: {}".format(device_imei)
                await send_sms(sms_event, user_phone_number, init_message)

                while authentication_status == 1 and user_password == "":
                    auth = await device_auth(device_imei, sms_phone_number, sms_event, send_sms, list_reader, get_voltage)
                    log(LogLevel.DEBUG, "Auth: {}".format(auth))
                    if auth is not None:
                        authentication_status, user_password = auth
                    await list_reader()
                    await asyncio.sleep(30)

            elif authentication_status == 1 and user_password != "":
                await list_reader()
                device_id = generate_id(device_imei, user_password)
                
                if user_msg != 1:
                    init_message = "DEVICE AUTHENTICATED | ID: {}".format(device_id)
                    try:
                        await send_sms(sms_event, user_phone_number, init_message)
                        user_msg= 1
                        log(LogLevel.DEBUG, "User Msg: {}".format(user_msg))
                    except Exception as e:
                        log(LogLevel.ERROR, "Error occurred during Device Authentication process.Error Message:"+str(e))
                        user_msg= 0
                        log(LogLevel.DEBUG, "User Msg: {}".format(user_msg))

                # Check if ON/OFF button is pressed before continuing
                while is_button_pressed(on_off):
                    while True:
                        call_task = asyncio.create_task(make_call(call_event, call_phone_number))
                        low_voltage_task = asyncio.create_task(low_voltage(device_id, sms_phone_number))
                        voltage_status = await low_voltage_task
                        if voltage_status:
                            low_voltage_message = "LOW VOLTAGE DEVICE | ID: {}".format(device_imei)
                            await send_sms(sms_event, user_phone_number, low_voltage_message)
                            call_task.cancel()
                        await asyncio.sleep(1)
                else:
                    log(LogLevel.INFO, "Waiting for Switch Button")
                    await asyncio.sleep(10)
                    
asyncio.run(main())