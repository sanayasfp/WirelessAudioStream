You are a senior python developer with 20 years of experience especially in micropython. You're writing the firmware code for hardware devices.
Your code is always detailed secure, scalable and well documented with as much detail as possible. You always use a chain of thought process and think of a better way to improve your code and make it optimal while explaining thing STEP BY STEP.
'''
Main algorithm:
# Import machine
# Import time
# Import gps
# Import cellular
# Set a variable as Server phone number
# Set a variable as Password 
# Set a variable as Device ID 
# Set a variable Led to pin 27
# Set a variable Voltage
# Make a hash function 
# set Device ID as a hash of cellular Imei with Password
# Check if SIM card Inserted
# - If SIM card not inserted
# -- Blink LED, three times every 20 seconds
# - If SIM Card inserted
# -- Check Network status
# --- If Network status is not okay
# ---- Blink LED, five times every 10 seconds
# --- While Network status is ok
# ---- Call Server phone number and keep it on 
# ---- Check Voltage (battery voltage) every 5 min
# ----- Every time the Voltage decrease by 10% 
# ------ Turn On GPS 
# ------ Get Location 
# ------ Get Satellites
# ------ Send SMS to Server phone number with Voltage, Location, Satellites
# ------ Turn Off GPS
# ---- If Voltage is below or equal to 5%
# ----- Hangup call
# ----- Blink LED, every 2 seconds  
'''
Go through all the following lines of code, one by one, correct, optimize and re write the full code while solving all bugs. Let's think step by step. 
main.py
```python
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

```
config.py
```python
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

```
battery_utils.py
```python
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
```
gps_utils.py
```python
import gps
from config import log, LogLevel
import uasyncio as asyncio

class GpsContext:
    async def __aenter__(self):
        log(LogLevel.INFO, "Managing GPS connections...")
        gps.on()
        return gps

    async def __aexit__(self, exc_type, exc_value, traceback):
        gps.off()

async def get_gps() -> tuple:
    log(LogLevel.INFO, "Retrieving GPS location, satellite information, and time...")
    async with GpsContext() as gps_instance:
        location = satellites = gtime = None
        while location is None or satellites is None or gtime is None:
            location = gps_instance.get_location()
            satellites = gps_instance.get_satellites()
            gtime = gps_instance.time()
            await asyncio.sleep(1)

        log(LogLevel.INFO, "GPS data | Location: {}, Satellites: {}, Time: {}".format(location, satellites, gtime))
        return location, satellites, gtime
```
config.json
```json
{
  "USER_PHONE_NUMBER": "7266008987",
  "SERVER_PHONE_NUMBER": "+17266008987",
  "PASSWORD": "your_password",
  "DEVICE_ID_ZERO": "0000000000",
  "SLEEP_TIME": 10,
  "LOW_VOLTAGE_THRESHOLD": 5,
  "LOG_LEVEL": 1
}
```