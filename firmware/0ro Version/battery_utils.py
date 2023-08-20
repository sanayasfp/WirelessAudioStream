import machine
import cellular
import uasyncio as asyncio
from gsm_utils import send_sms, sms_handler
from config import log, LogLevel, blink_led

def voltage_decreased_by_10_percent(previous_voltage: float) -> bool:
    log(LogLevel.INFO, "Checking voltage decrease...")
    current_voltage = machine.get_input_voltage()[1]

    if previous_voltage is None:
        previous_voltage = current_voltage
        return False

    voltage_diff = previous_voltage - current_voltage
    ten_percent_decrease = previous_voltage * 0.1

    if voltage_diff >= ten_percent_decrease:
        previous_voltage = current_voltage
        return True

    return False

async def monitor_battery_voltage(server_phone_number: str, device_id: str, low_voltage_threshold: int, gps_task: asyncio.Task):
    previous_voltage = None
    while True:
        log(LogLevel.INFO, "Monitoring battery voltage...")
        location, satellites, gtime = await gps_task
        current_voltage = machine.get_input_voltage()[1]
        network_status = cellular.get_network_status()
        if current_voltage <= low_voltage_threshold:
            await blink_led(27, 1, 2)
            if network_status != 0:
                message = "LOW BAT| ID: {}; Voltage: {}; Time: {}; Location: {}; Satellites: {}".format(device_id, current_voltage, gtime, location, satellites)
                await send_sms(server_phone_number, message, sms_handler)
        else:
            await asyncio.sleep(10)
            if voltage_decreased_by_10_percent(previous_voltage):
                message = "VOLT | ID: {}; Voltage: {}; Time: {}; Location: {}; Satellites: {}".format(device_id, current_voltage, gtime, location, satellites)
                await send_sms(server_phone_number, message, sms_handler)

        previous_voltage = current_voltage