import machine
import json
import uasyncio as asyncio
from helper_utils import log, LogLevel, blink_led
from gsm_utils import send_sms, sms_event
from gps_utils import get_gps

with open("config.json") as f:
    config = json.load(f)

threshold_value = config["THRESHOLD_VALUE"]

def get_voltage() -> tuple:
    battery_values  = machine.get_input_voltage()
    battery_voltage = battery_values[0]
    battery_percentage = battery_values[1]
    log(LogLevel.INFO, "BATTERY VOLTAGE: {}, BATTERY PERCENTAGE: {}".format(battery_voltage, battery_percentage))
    return battery_values

def voltage_decreased(previous_percentage: float) -> bool:
    battery_percentage = get_voltage()[1]

    if previous_percentage is None:
        previous_percentage = battery_percentage
        return False
    else:
        percentage_diff = previous_percentage - battery_percentage
        ten_percent_decrease = threshold_value * 2

        if percentage_diff >= ten_percent_decrease:
            previous_percentage = battery_percentage
            return True
        return False

async def monitor_voltage(previous_percentage: float, device_id: str, server_phone_number: str):
    while True:
        battery_percentage = get_voltage()[1]
        if voltage_decreased(previous_percentage):
            device_location, device_satellites = get_gps()
            bat_message = "VOLT | ID: {}; Voltage: {}; Location: {}; Satellites: {}".format(device_id, battery_percentage, device_location, device_satellites)
            send_sms(sms_event, server_phone_number, bat_message)
            log(LogLevel.INFO, sms_message)

        previous_percentage = battery_percentage
        await asyncio.sleep(10)

async def low_voltage(device_id: str, server_phone_number: str) -> bool:
    while True:
        battery_percentage = get_voltage()[1]
        if battery_percentage <= threshold_value:
            device_location, device_satellites = get_gps()
            low_message = "LOW BAT| ID: {}; Voltage: {}; Location: {}; Satellites: {}".format(device_id, battery_percentage, device_location, device_satellites)
            send_sms(sms_event, server_phone_number, low_message)
            log(LogLevel.INFO, sms_message)
            return True
        await asyncio.sleep(10)
