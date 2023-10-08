import machine
import cellular
import json
import hashlib
import re
import uasyncio as asyncio

authentication_status = False

with open("config.json") as f:
    config = json.load(f)

led_pin = config["LED_PIN"]

class LogLevel:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3

class LedTime:
    SIM = 5
    NETWORK = 4
    AUTH = 3
    BATTERY = 2

# Set the desired log level here
LOG_LEVEL = LogLevel.DEBUG

def log(level: int, msg: str) -> None:
    """
    Log a message at the given log level.

    :param level: Log level (e.g., LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, or LogLevel.ERROR)
    :param msg: Message to be logged
    """
    if level >= LOG_LEVEL:
        print(msg)

def blink_led(times: int, delay: float) -> None:
    """
    Blink led_pin to a specified number of times with a given delay.
    
    :param times: The number of times to blink the LED
    :param delay: The time in seconds between each blink
    """
    led = machine.Pin(led_pin, machine.Pin.OUT)
    for _ in range(times):
        led.value(1)
        asyncio.sleep(delay)
        led.value(0)
        asyncio.sleep(delay)

def get_imei()-> str:
    """
    Retrieve Network Module unique IMEI number.

    :log: device_imei as *INFO* level
    :return: **device_imei** as a string
    """
    device_imei = cellular.get_imei()
    log(LogLevel.INFO, "IMEI: {}".format(device_imei))
    return device_imei

def generate_id(device_imei: str, user_password: str) -> str:
    """
    Generate a unique device ID based on the device's IMEI and a given password.
    
    :param device_imei: The unique device's IMEI
    :param user_password: The password for the device as a string
    :log: device_id as *INFO* level
    :return: The generated device ID as a string
    """
    m = hashlib.sha256()
    m.update(device_imei.encode('utf-8'))
    m.update(user_password.encode('utf-8'))
    hash_bytes = m.digest()[:5]
    device_id_int = int.from_bytes(hash_bytes, 'big')
    device_id = "{:010d}".format(device_id_int)
    log(LogLevel.INFO, "DEVICE ID: {}".format(device_id))
    return device_id

async def extract_bulk(sms_msg: str)-> dict:
    """
    Extract specified key values pairs from an input message using regular expressions.

    :param **sms_msg**: The input message as a string
    :log: bulk_values as *INFO* level
    :return **values**: A dictionary containing the extracted values as key-value pairs
    """
        
    bulk_values = {}
    
    # Extract Type of Message
    type_match = re.search(r'Type of Message: (\w+)', sms_msg)
    if type_match:
        bulk_values['Type of Message'] = type_match.group(1)
    
    # Extract Phone number
    phone_match = re.search(r'Phone number: ([+\d]+)', sms_msg)
    if phone_match:
        bulk_values['Phone number'] = phone_match.group(1)
    
    # Extract Nature
    nature_match = re.search(r'Nature: (\w+)', sms_msg)
    if nature_match:
        bulk_values['Nature'] = nature_match.group(1)
    
    # Extract IMEI
    imei_match = re.search(r'IMEI: (\d+)', sms_msg)
    if imei_match:
        bulk_values['IMEI'] = imei_match.group(1)
    
    # Extract Voltage
    voltage_match = re.search(r'Voltage: (\d+)', sms_msg)
    if voltage_match:
        bulk_values['Voltage'] = voltage_match.group(1)
    
    # Extract Location
    location_match = re.search(r'Location: \(([-\d.]+), ([-\d.]+)\)', sms_msg)
    if location_match:
        bulk_values['Location'] = (float(location_match.group(1)), float(location_match.group(2)))
    
    # Extract Satellites
    satellites_match = re.search(r'Satellites: \((\d+), (\d+)\)', sms_msg)
    if satellites_match:
        bulk_values['Satellites'] = (int(satellites_match.group(1)), int(satellites_match.group(2)))
    
    # Extract pn_type, index, and purpose
    pn_type_match = re.search(r'pn_type=(\d+)', sms_msg)
    index_match = re.search(r'index=(\d+)', sms_msg)
    purpose_match = re.search(r'purpose=(\d+)', sms_msg)
    if pn_type_match and index_match and purpose_match:
        bulk_values['pn_type'] = int(pn_type_match.group(1))
        bulk_values['index'] = int(index_match.group(1))
        bulk_values['purpose'] = int(purpose_match.group(1))
    
    log(LogLevel.INFO, "BULK VALUES: {}".format(bulk_values))
    return bulk_values

def extract_values(sms_msg: str):
    """
    Extract specified key values pairs from an input message using regular expressions.

    :param **sms_msg**: The input message as a string
    :log: values as *INFO* level
    :return **message_type, password, id, values**: A tuple containing the extracted values as key-value pairs
    """
    
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
    # Return the extracted values as a dictionary
    return values

async def device_auth(device_imei: str, server_phone_number: str, sms_event: callable, send_sms: callable, list_reader: callable, get_voltage: callable, get_gps: callable):
    """
    Verify device authentication by:
    - Get **device_location** and **device_satellites** from **get_gps** function from *gps_utils.py*
    - Get **battery_percentage** from **get_voltage** function from *battery_utils.py*
    - Sending device information : **device_imei**, **battery_percentage**, **device_location**, **device_satellites** to server via SMS using **send_sms** function from *gsm_utils.py*
    - Wait to server response SMS **sms_event** function from *gsm_utils.py*
    - Extract **message_type**, **server_id**, **user_password** values from **sms_msg** with **extract_values** function
    - Generate **device_id** with **device_imei** and **user_password** from **generate_id** function
    - Compare **device_id** value and **server_id** value from an input message.
    - If **device_id** == **server_id**
      - **log**: message_type | device_id, user_password as *INFO* level
      - Send **message_type**, **device_id**, **user_password** values back to server via SMS using **send_sms** function from *gsm_utils.py*
    - If **device_id** != **server_id**
      - **log**: WRONG ID | server_id, user_password as *ERROR* level
      - Send *WRONG ID*, **server_id**, **user_password** values back to server via SMS using **send_sms** function from *gsm_utils.py*

    :param **device_imei**, **server_phone_number**, **get_gps**, **get_voltage**: The input message as a string
    :return **authentication_status**, **user_password**: A list of values
    """
    global authentication_status
    
    sms_content = await list_reader()
    log(LogLevel.INFO, "Last SMS Values: {}".format(sms_content))
    
    if sms_content is not None:
        message_type = server_password = server_id =  None
        # Extract each value here
        message_type = sms_content[:sms_content.find("|")].strip()

        # Extracting ID value
        if "CODE:" in sms_content:
            password_start = sms_content.find("CODE: ") + len("CODE: ")
            password_end = sms_content.find(";", password_start)
            server_password = sms_content[password_start:password_end]

        # Extracting ID value
        if "ID:" in sms_content:
            id_start = sms_content.find("ID: ") + len("ID: ")
            id_end = sms_content.find(";", id_start)
            server_id = sms_content[id_start:id_end]
        
        if server_password is not None and server_id is not None:
            device_id = generate_id(device_imei, server_password)
            if device_id == server_id:
                auth_message0 = "AUTH | CODE:{}; ID:{}".format(server_password, device_id)
                await send_sms(sms_event, server_phone_number, auth_message0)
                authentication_status = True
                return authentication_status, server_password
            else:
                auth_message1 = "WRONG ID | CODE:{}; ID:{}".format(server_password, server_id)
                await send_sms(sms_event, server_phone_number, auth_message1)
                authentication_status = False
                return authentication_status, None
    else:
        device_location, device_satellites = await get_gps()
        battery_percentage = get_voltage()[1]
        sms_message = "AUTH | IMEI:{}; Voltage:{}; Location:{}; Satellites:{}".format(device_imei, battery_percentage, device_location, device_satellites)
        await send_sms(sms_event, server_phone_number, sms_message)
        
        authentication_status = False
        return authentication_status, None
    await asyncio.sleep(1)

