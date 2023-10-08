import machine
import json
import uasyncio as asyncio
from helper_utils import log, LogLevel, blink_led
from gsm_utils import send_sms, sms_event

with open("config.json") as f:
    config = json.load(f)

threshold_value = config["THRESHOLD_VALUE"]

def get_voltage() -> tuple:
    """
    Get the battery voltage and percentage.

    :return: A tuple containing the battery voltage and percentage.
    """
    battery_values = machine.get_input_voltage()
    battery_voltage = battery_values[0]
    battery_percentage = battery_values[1]
    log(LogLevel.INFO, "BATTERY VOLTAGE: {}, BATTERY PERCENTAGE: {}".format(battery_voltage, battery_percentage))
    return battery_values

def voltage_decreased(previous_percentage: float) -> bool:
    """
    Check if the battery voltage has decreased by 10% from the previous reading.

    :param previous_percentage: The previous battery percentage.
    :return: True if the voltage has decreased by 10%, False otherwise.
    """
    # Get the current percentage of the battery.
    battery_percentage = get_voltage()[1]

    # If there is no previous percentage value, set it to the current percentage and return False.
    if previous_percentage is None:
        previous_percentage = battery_percentage
        return False

    # Calculate the difference between the previous and current percentages.
    percentage_diff = previous_percentage - battery_percentage

    # Calculate the threshold for a 10% decrease in voltage.
    ten_percent_decrease = threshold_value * 0.1

    # If the difference is greater than or equal to twice the threshold value,
    # update the previous percentage and return True.
    if percentage_diff >= ten_percent_decrease * 2:
        previous_percentage = battery_percentage
        return True

    # Otherwise, just update the previous percentage and return False.
    else:
        previous_percentage = battery_percentage
        return False

async def monitor_voltage(previous_percentage: float, device_id: str, sms_phone_number: str):
    """
    Continuously monitor the battery voltage and send a notification if it decreases by 10%.

    :param previous_percentage: The previous battery percentage.
    :param device_id: The unique device ID.
    :param sms_phone_number: The phone number to send the notification to.
    """
    while True:
        # Get the current voltage level.
        battery_values = get_voltage()
        battery_voltage = battery_values[0]
        battery_percentage = battery_values[1]

        if voltage_decreased(previous_percentage):
            bat_message = "VOLT | ID: {}; Voltage: {}".format(device_id, round(battery_voltage, 2))
            send_sms(sms_event, sms_phone_number, bat_message)
            log(LogLevel.INFO, bat_message)

        previous_percentage = battery_percentage

        await asyncio.sleep(30)

async def low_voltage(device_id: str, sms_phone_number: str) -> bool:
    """
    Check if the battery voltage has fallen below the threshold value.

    :param device_id: The unique device ID.
    :param sms_phone_number: The phone number to send the notification to.
    :return: True if the battery voltage is low, False otherwise.
    """
    battery_values = get_voltage()
    battery_voltage = battery_values[0]
    battery_percentage = battery_values[1]

    # Check if voltage has fallen below the threshold value.
    if battery_percentage <= threshold_value:
        low_message = "LOW BAT| ID:{}; Voltage:{}".format(device_id, round(battery_voltage))
        send_sms(sms_event, sms_phone_number, low_message)
        log(LogLevel.INFO, low_message)

        # Return True to indicate that voltage has fallen below the threshold value.
        return True

    await asyncio.sleep(30)
