import machine
import cellular
import json
import hashlib
import re
import uasyncio as asyncio

# Configuration
with open('config.json', 'r') as f:
    config = json.load(f)

led_pin_1 = config["LED_1"]
led_pin_2 = config["LED_2"]
led_pin_3 = config["LED_3"]
led_pin_4 = config["LED_4"]
led1 = machine.Pin(led_pin_1, machine.Pin.OUT)
led2 = machine.Pin(led_pin_2, machine.Pin.OUT)
led3 = machine.Pin(led_pin_3, machine.Pin.OUT)
led4 = machine.Pin(led_pin_4, machine.Pin.OUT)

authentication_status = config["AUTHENTICATION"]
user_password = config["USER_PASSWORD"]

# Log levels
class LogLevel:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3

# LED blink times
class LedTime:
    ON = 6
    SMS = 6
    SIM = 5
    NETWORK = 4
    AUTH = 3
    CALL = 2
    BATTERY = 1

# Set the desired log level here
LOG_LEVEL = LogLevel.DEBUG

# Logging function
def log(level: int, msg: str) -> None:
    if level >= LOG_LEVEL:
        print(msg)

async def led_on():
    try:
        led1.value(1)
        led2.value(1)
        led3.value(1)
        led4.value(1)
    except Exception as e:
        log(LogLevel.ERROR, "Error occurred while turning on LED. Error message: {}".format(str(e)))
    
async def led_off():
    try:
        led1.value(0)
        led2.value(0)
        led3.value(0)
        led4.value(0)
    except Exception as e:
        log(LogLevel.ERROR, "Error occurred while turning off LED. Error message: {}".format(str(e)))

# Blink LED function
async def blink_led(times: int, delay: float) -> None:
    try:
        log(LogLevel.INFO,"Blinking LED: {} times, for: {} seconds".format(times, delay))
        for _ in range(times):
            await led_on()
            asyncio.sleep(delay)
            await led_off()
            asyncio.sleep(delay)
    except Exception as e:
        log(LogLevel.ERROR, "Error occurred while blinking LED. Error message: {}".format(str(e)))

# Get the Network Module's unique IMEI number
def get_imei() -> str:
    try:
        device_imei = cellular.get_imei()
        log(LogLevel.INFO, "IMEI: {}".format(device_imei))
        return device_imei
    except Exception as e:
        log(LogLevel.ERROR, "Error occurred while retrieving IMEI. Error message: {}".format(str(e)))

# Generate a unique device ID based on the device's IMEI and a given password
def generate_id(device_imei: str, user_password: str) -> str:
    try:
        m = hashlib.sha256()
        m.update(device_imei.encode('utf-8'))
        m.update(user_password.encode('utf-8'))
        hash_bytes = m.digest()[:5]
        device_id_int = int.from_bytes(hash_bytes, 'big')
        device_id = "{:010d}".format(device_id_int)
        log(LogLevel.INFO, "DEVICE ID: {}".format(device_id))
        return device_id
    except Exception as e:
        log(LogLevel.ERROR, "Error occurred while generating DEVICE ID. Error message: {}".format(str(e)))

# Extract specified key-value pairs from an input message using regular expressions
def extract_values(sms_msg: str) -> dict:
    try:
        values = {}

        # Extracting message type
        message_type = sms_msg[:sms_msg.find("|")].strip()
        values['Type'] = message_type

        # Extracting ID value
        if "CODE:" in sms_msg:
            password_start = sms_msg.find("CODE: ") + len("CODE: ")
            password_end = sms_msg.find(";", password_start)
            password = sms_msg[password_start:password_end]
            values['CODE'] = password

        # Extracting ID value
        if "ID:" in sms_msg:
            id_start = sms_msg.find("ID: ") + len("ID: ")
            id_end = sms_msg.find(";", id_start)
            server_id = sms_msg[id_start:id_end]
            values['ID'] = server_id

        # Extracting IMEI value
        if "IMEI:" in sms_msg:
            imei_start = sms_msg.find("IMEI: ") + len("IMEI: ")
            imei_end = sms_msg.find(";", imei_start)
            imei = sms_msg[imei_start:imei_end]
            values['IMEI'] = imei

        # Extracting Time value
        if "Time:" in sms_msg:
            gtime_start = sms_msg.find("Time: ") + len("Time: ")
            gtime_end = sms_msg.find(";", gtime_start)
            gtime = sms_msg[gtime_start:gtime_end]
            values['Time'] = gtime

        # Extracting Voltage value
        if "Voltage:" in sms_msg:
            voltage_start = sms_msg.find("Voltage: ") + len("Voltage: ")
            voltage_end = sms_msg.find(";", voltage_start)
            current_voltage = sms_msg[voltage_start:voltage_end]
            values['Voltage'] = current_voltage

        # Extracting Location value
        if "Location: " in sms_msg:
            location_start = sms_msg.find("Location: (") + len("Location: (")
            location_end = sms_msg.find(")", location_start)
            location = sms_msg[location_start:location_end]
            values['Location'] = location

        # Extracting Satellites value
        if "Satellites: " in sms_msg:
            satellites_start = sms_msg.find("Satellites: (") + len("Satellites: (")
            satellites_end = sms_msg.find(")", satellites_start)
            satellites = sms_msg[satellites_start:satellites_end]
            values['Satellites'] = satellites

        log(LogLevel.INFO, "MESSAGE VALUES: {}".format(values))
        return values

    except Exception as e:
        log(LogLevel.ERROR, "Error occurred while Extracting SMS Values. Error message: {}".format(str(e)))


async def device_auth(device_imei: str, sms_phone_number: str, sms_event: str, send_sms: callable, list_reader: callable, get_voltage: callable):
    try:
        global authentication_status
        server_password = None
        server_id = None

        sms_content = await list_reader()

        log(LogLevel.INFO, "Last SMS Values:{} ".format(sms_content))

        if sms_content is not None:
            # Extract server password and ID from the received SMS content
            if "CODE:" in sms_content:
                code_start = sms_content.find("CODE: ") + len("CODE: ")
                code_end = sms_content.find(";", code_start)
                server_password = sms_content[code_start:code_end]
                log(LogLevel.INFO, "CODE Value : {}".format(server_password))

            if "ID:" in sms_content:
                id_start = sms_content.find("ID: ") + len("ID: ")
                id_end = sms_content.find(";", id_start)
                server_id = sms_content[id_start:id_end]
                log(LogLevel.INFO, "ID Value : {}".format(server_id))

            if server_password is not None and server_id is not None:
                # Generate device ID based on the received server password and check for authentication
                device_id = generate_id(device_imei=device_imei, user_password=server_password)

                if device_id == server_id:
                    # Device authenticated
                    auth_message = "AUTH | CODE:{}; ID:{}".format(server_password, device_id)
                    await send_sms(sms_event, sms_phone_number, auth_message)
                    authentication_status = 1

                    # Update authentication status and user password in config file
                    config['AUTHENTICATION'] = authentication_status
                    config['USER_PASSWORD'] = server_password
                    with open('config.json', 'w') as f:
                        json.dump(config, f)
                        log(LogLevel.INFO, "Config file updated successfully!")

                    return authentication_status, server_password
                else:
                    # Wrong ID received
                    auth_message = "WRONG ID | CODE:{}; ID:{}".format(server_password, server_id)
                    await send_sms(sms_event, sms_phone_number, auth_message)
                    authentication_status = 0
                    return authentication_status, None

        else:
            # No authentication info received, send IMEI, voltage, location, and satellites to request authentication
            battery_percentage = get_voltage()[1]
            sms_message = "AUTH | IMEI:{}; Voltage:{}".format(device_imei, battery_percentage)
            await send_sms(sms_event, sms_phone_number, sms_message)
            authentication_status = 0
            await asyncio.sleep(10)
            return authentication_status, None

    except Exception as e:
        log(LogLevel.ERROR, "Error occurred during Device Authentication process.Error Message:"+str(e))
        return authentication_status, None

