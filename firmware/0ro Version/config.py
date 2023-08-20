import uasyncio as asyncio
import machine
import hashlib
import re

class LogLevel:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3

# Set the desired log level here
LOG_LEVEL = LogLevel.INFO

def log(level: int, msg: str) -> None:
    """
    Log a message at the given log level.

    :param level: Log level (e.g., LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, or LogLevel.ERROR)
    :param msg: Message to be logged
    """
    if level >= LOG_LEVEL:
        print(msg)

def generate_device_id(imei: str, password: str) -> str:
    """
    Generate a unique device ID based on the device's IMEI and a given password.
    
    :param imei: The unique device's IMEI
    :param password: The password for the device as a string
    :return: The generated device ID as a string
    """
    m = hashlib.sha256()
    m.update(imei.encode('utf-8'))
    m.update(password.encode('utf-8'))
    hash_bytes = m.digest()[:5]
    device_id_int = int.from_bytes(hash_bytes, 'big')
    return "{:010d}".format(device_id_int)

async def blink_led(pin: int, times: int, delay: float) -> None:
    """
    Blink the LED a specified number of times with a given delay.
    
    :param pin: An integer representing the GPIO pin number for the LED
    :param times: The number of times to blink the LED
    :param delay: The time in seconds between each blink
    """
    led = machine.Pin(pin, machine.Pin.OUT)
    for _ in range(times):
        led.value(1)
        await asyncio.sleep(delay)
        led.value(0)
        await asyncio.sleep(delay)

def extract_bulk_values(message: str) -> dict:
    """
    Extract specified values from an input message using regular expressions.
    
    :param message: The input message as a string
    :return: A dictionary containing the extracted values as key-value pairs
    """
    values = {}
    
    # Extract Type of Message
    type_match = re.search(r'Type of Message: (\w+)', message)
    if type_match:
        values['Type of Message'] = type_match.group(1)
    
    # Extract Phone number
    phone_match = re.search(r'Phone number: ([+\d]+)', message)
    if phone_match:
        values['Phone number'] = phone_match.group(1)
    
    # Extract Nature
    nature_match = re.search(r'Nature: (\w+)', message)
    if nature_match:
        values['Nature'] = nature_match.group(1)
    
    # Extract IMEI
    imei_match = re.search(r'IMEI: (\d+)', message)
    if imei_match:
        values['IMEI'] = imei_match.group(1)
    
    # Extract Voltage
    voltage_match = re.search(r'Voltage: (\d+)', message)
    if voltage_match:
        values['Voltage'] = voltage_match.group(1)
    
    # Extract Location
    location_match = re.search(r'Location: \(([-\d.]+), ([-\d.]+)\)', message)
    if location_match:
        values['Location'] = (float(location_match.group(1)), float(location_match.group(2)))
    
    # Extract Satellites
    satellites_match = re.search(r'Satellites: \((\d+), (\d+)\)', message)
    if satellites_match:
        values['Satellites'] = (int(satellites_match.group(1)), int(satellites_match.group(2)))
    
    # Extract pn_type, index, and purpose
    pn_type_match = re.search(r'pn_type=(\d+)', message)
    index_match = re.search(r'index=(\d+)', message)
    purpose_match = re.search(r'purpose=(\d+)', message)
    if pn_type_match and index_match and purpose_match:
        values['pn_type'] = int(pn_type_match.group(1))
        values['index'] = int(index_match.group(1))
        values['purpose'] = int(purpose_match.group(1))
    
    return values

def extract_message_values(message: str) -> tuple:
    """
    Extract the specified values from an input message.

    :param message: The input message as a string
    :return: A dictionary with the extracted values as key-value pairs
    """
    values = {}
    
    # Extracting message type
    message_type = message[:message.find("|")].strip()
    values['Nature'] = message_type

    # Extracting ID value
    if "CODE: " in message:
        password_start = message.find("CODE: ") + len("CODE: ")
        password_end = message.find(";", password_start)
        password = message[password_start:password_end]
        values['CODE'] = password

    # Extracting ID value
    if "ID: " in message:
        id_start = message.find("ID: ") + len("ID: ")
        id_end = message.find(";", id_start)
        device_id = message[id_start:id_end]
        values['ID'] = device_id

    # Extracting IMEI value
    if "IMEI: " in message:
        imei_start = message.find("IMEI: ") + len("IMEI: ")
        imei_end = message.find(";", imei_start)
        imei = message[imei_start:imei_end]
        values['IMEI'] = imei
    
    # Extracting Time value
    if "Time: " in message:
        gtime_start = message.find("Time: ") + len("Time: ")
        gtime_end = message.find(";", gtime_start)
        gtime = message[gtime_start:gtime_end]
        values['Time'] = gtime

    # Extracting Voltage value
    if "Voltage: " in message:
        voltage_start = message.find("Voltage: ") + len("Voltage: ")
        voltage_end = message.find(";", voltage_start)
        current_voltage = message[voltage_start:voltage_end]
        values['Voltage'] = current_voltage

    # Extracting Location value
    if "Location: " in message:
        location_start = message.find("Location: (") + len("Location: (")
        location_end = message.find(")", location_start)
        location = message[location_start:location_end]
        values['Location'] = location

    # Extracting Satellites value
    if "Satellites: " in message:
        satellites_start = message.find("Satellites: (") + len("Satellites: (")
        satellites_end = message.find(")", satellites_start)
        satellites = message[satellites_start:satellites_end]
        values['Satellites'] = satellites

    # Return the extracted values as a dictionary
    return message_type, password, device_id, values

