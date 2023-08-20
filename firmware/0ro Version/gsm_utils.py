import machine
import time
import cellular
import uasyncio as asyncio
from gps_utils import get_gps
from config import log, LogLevel, generate_device_id, blink_led, extract_message_values

authentication = False
password = None
server_authentication = None
server_id = None
auth_message = None
auth_handler = None
r_sms = None
flag = False

async def check_sim_card()-> bool:
    #while True:
    log(LogLevel.INFO, "Checking SIM card...")
    sim = cellular.is_sim_present()
    if sim != 1:
        log(LogLevel.ERROR, "Error: SIM card")
        await blink_led(27, 3, 1)
        await asyncio.sleep(3)
        return False
    else:
        log(LogLevel.INFO, "SIM Checked")
        return True

async def check_network ()-> bool:
    #while True:
    log(LogLevel.INFO, "Checking Network...")
    network_status = cellular.get_network_status()
    if network_status != 1:
        log(LogLevel.ERROR, "Error: No Network Coverage")
        await blink_led(27, 3, 1)
        await asyncio.sleep(3)
        return False
    else:
        log(LogLevel.INFO, "Network Checked")
        return True
        
async def request_auth(imei: str, server_phone_number: str, gps_task: asyncio.Task)-> bool:
    log(LogLevel.INFO, "Checking Authentication...")

    while not authentication:
        location, satellites, gtime = await gps_task
        current_voltage = machine.get_input_voltage()[1]
        message = "AUTH | IMEI: {}; Voltage: {}; Location: {}; Satellites: {}".format(imei, current_voltage, location, satellites)
        await send_sms(server_phone_number, message, sms_handler)
        await asyncio.sleep(30)
    return True
        
async def check_auth (imei: str)-> tuple:
    #global authentication
    #global password

    auth_rec= await receive_auth(imei, r_handler)
    log(LogLevel.INFO, "Reading Check Auth Values: {}".format(auth_rec))
    
    #authentication, password = auth_rec
    #await asyncio.sleep(1) | authentication, password
    return auth_rec

async def receive_auth(imei: str, r_handler: callable)-> tuple:
    global authentication
    global password
    global auth_message
    global auth_handler
    global r_sms
    global password
    global server_id
    
    while auth_message is None:
        
         
        auth_message = cellular.on_sms(r_handler)
        log(LogLevel.INFO, "Reading Auth SMS from Server: {}".format(auth_message))
        
        # Initialize server_authentication, server_id, and server_password to None
        auth_handler = r_handler(r_sms)
        log(LogLevel.INFO, "Auth Handler: {}".format(auth_handler))
        log(LogLevel.INFO, "R SMS: {}".format(r_sms))
        if auth_handler is not None:
            message = r_sms.message
            sender = r_sms.phone_number
            log(LogLevel.INFO, "Message: {}".format(message))
            log(LogLevel.INFO, "Sender: {}".format(sender))

            message_type, password, server_id, values = extract_message_values(message)
            log(LogLevel.INFO, "Extracted SMS Values: {}".format(values))

            device_id = generate_device_id(imei, password)
            log(LogLevel.INFO, "Device Id: {}".format(device_id))

            if device_id == server_id:
                # Set the authentication global variable to True after the SMS has been sent
                message = "{} | ID: {}; CODE: {}".format(message_type, device_id, password)
                await send_sms(sender, message, sms_handler)
                authentication = True
                log(LogLevel.INFO, "Authentication Completed: {}".format(authentication))
                return authentication, password, server_id
            else:
                # Set the authentication global variable to True after the SMS has been sent
                log(LogLevel.ERROR, "Wrong ID: {}".format(server_id))
                message = "WRONG ID | ID: {}; CODE: {}".format(server_id, password)
                await send_sms(sender, message, sms_handler)
                authentication = False
                return authentication
    await asyncio.sleep(5)

def r_handler(r_sms)-> str:
    log(LogLevel.INFO, "Waiting for Server SMS: {}".format(r_sms))
    if r_sms == cellular.SMS_SENT:
        log(LogLevel.INFO, "SENDING SMS {}".format(r_sms))
        return 0
    elif r_sms == 1:
        log(LogLevel.INFO, "SMS SENT: {}".format(r_sms))
        return 1 
    elif r_sms is None:
        log(LogLevel.INFO, "No SMS STATUS: {}".format(r_sms))
        return None
    else:
        log(LogLevel.INFO, "Reading new SMS: {}".format(r_sms))
        return r_sms
        
async def send_sms(phone_number: str, message: str, sms_handler: callable):
    log(LogLevel.INFO, "Sending SMS...")
    cellular.on_sms(sms_handler)
    t_sms = cellular.SMS(phone_number, message)
    log(LogLevel.INFO, "Message: {}".format(message))
    try:
        t_sms.send()
        log(LogLevel.INFO, "SMS Content: {}".format(message))
    except Exception as e:
        log(LogLevel.ERROR, "Error occurred while sending SMS: {}".format(e))
    await asyncio.sleep(5)

def sms_handler(evt_sms)-> tuple:
    if evt_sms == cellular.SMS_SENT:
        log(LogLevel.INFO, "SENDING SMS: {}".format(evt_sms))
        return evt_sms
    elif evt_sms == 1:
        log(LogLevel.INFO, "SMS SENT: {}".format(evt_sms))
    else:
        log(LogLevel.INFO, "SMS RECEIVED: {}".format(evt_sms))
        message = evt_sms.message
        sender = evt_sms.phone_number
        log(LogLevel.INFO, "Message: {}".format(message))
        log(LogLevel.INFO, "Sender: {}".format(sender))
        if message is not None:
            message_type, server_password, server_id, values = extract_message_values(message)
            log(LogLevel.INFO, "Extracted SMS Values: {}".format(values))
            return message_type, server_password, server_id, values
        else:
            log(LogLevel.ERROR, "Error occurred while Reading SMS: {}".format(message))
            return evt_sms

async def make_call(phone_number: str, call_handler: callable)-> str:
    log(LogLevel.INFO, "Dialing phone number...")
    cellular.on_call(call_handler)
    try:
        cellular.dial(phone_number)
    except Exception as e:
        log(LogLevel.ERROR, "Error occurred while dialing: {}".format(e))
    await asyncio.sleep(5)

def call_handler(evt_call)-> str:
    log(LogLevel.INFO, "CALL EVENT: {}".format(evt_call))
    return evt_call
                
async def initiate_gsm_event(server_phone_number: str, user_phone_number: str, device_id: str, gps_task: asyncio.Task):
    while True:
        log(LogLevel.INFO, "Initiating GSM event...")
        location, satellites, gtime = gps_task
        current_voltage = machine.get_input_voltage()[1]
        message = "INIT | ID: {}; Voltage: {}; Location: {}; Satellites: {}".format(device_id, current_voltage, location, satellites)
        #await send_sms(server_phone_number, message, sms_handler)
        log(LogLevel.INFO, "Message: {}".format(message))
        log(LogLevel.INFO, "Sending SMS...")
        cellular.on_sms(sms_handler)
        t_sms = cellular.SMS(server_phone_number, message)
        t_sms.send()
        log(LogLevel.INFO, "SMS Content: {}".format(message))
    await asyncio.sleep(1)

        cellular.on_sms(sms_handler)
        await asyncio.sleep(1)

        #await make_call(user_phone_number, call_handler)
        #await asyncio.sleep(1)
