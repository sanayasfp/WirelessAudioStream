import cellular
from cellular import SMS
import time
import uasyncio as asyncio
from helper_utils import LogLevel, log, blink_led, LedTime, extract_values


async def check_sim():
    sim = cellular.is_sim_present()
    if not sim:
        blink_led(LedTime.SIM, 0.5)
        log(LogLevel.ERROR, "No SIM Card")
        await asyncio.sleep(3)
    else:
        log(LogLevel.INFO, "SIM Card Present")
    return sim

async def check_network():
    network = cellular.get_network_status()
    if not network:
        blink_led(LedTime.NETWORK, 0.5)
        log(LogLevel.ERROR, "No Network Coverage")
        await asyncio.sleep(3)
    else:
        log(LogLevel.INFO, "Good Network Coverage")
    return network

def sms_event(evt_sms)-> tuple:
    log(LogLevel.INFO, "SMS EVENTS: {}".format(evt_sms))
    
    if evt_sms is None:
        log(LogLevel.INFO, "NO SMS EVENT: {}".format(evt_sms))
        return evt_sms, None,None
    elif evt_sms == cellular.SMS_SENT:
        log(LogLevel.INFO, "SMS SENT: {}".format(evt_sms))
        return evt_sms, None, None
    else:
        message = evt_sms.message
        sender = evt_sms.phone_number
        log(LogLevel.INFO, "SMS RECEIVED | from: {}, content: {}".format(sender, message))
        return evt_sms, sender, message

async def send_sms(sms_event: callable, phone_number: str, message: str):
    try:
        log(LogLevel.INFO, "SENDING SMS | To: {}, Content: {}".format(phone_number, message))
        t_sms = SMS(phone_number, message)
        t_sms.send()
        evt = cellular.on_sms(sms_event)
        return evt
    except Exception as e:
        log(LogLevel.ERROR, "Error occurred while sending SMS: {}".format(e))
    await asyncio.sleep(1)

async def make_call(call_event: callable, phone_number: str):
    cellular.on_call(call_event)
    try:
        log(LogLevel.INFO, "DIALING | Phone Number: {}".format(phone_number))
        cellular.dial(phone_number)
    except Exception as e:
        log(LogLevel.ERROR, "Error occurred while dialing: {}".format(e))
    await asyncio.sleep(5)

def call_event(evt_call):
    log(LogLevel.INFO, "CALL EVENT: {}".format(evt_call))
    return evt_call

async def list_reader():
    sms_list = last_sms = sms_content = sms_sender = None
    log(LogLevel.DEBUG, "List Reader Initiated!")

    sms_list = SMS.list()
    log(LogLevel.INFO, "SMS List: {}".format(sms_list))
    if sms_list:
        # Get the last message from the list
        last_sms = sms_list[-1]  
        sms_content = last_sms.message
        sms_sender = last_sms.phone_number
        log(LogLevel.INFO, "LAST SMS | content: {}, from: {}".format(sms_content, sms_sender))
        for l_sms in sms_list:
            try:
                l_sms.withdraw()
                log(LogLevel.DEBUG, "SMS Deleted!")
            except Exception as e:
                log(LogLevel.ERROR, "Error occurred : {} | Deleting SMS: {}".format(e, l_sms))
        return sms_content
    else:
        log(LogLevel.INFO, "No SMS messages in the list.")

    log(LogLevel.DEBUG, "List Reader Done!")    
    await asyncio.sleep(10)
    return None

async def sms_reader(sms_event: callable):
    log(LogLevel.DEBUG, "SMS Reader Initiated!")

    sms_check = cellular.on_sms(sms_event)
    if sms_check is not None:
        log(LogLevel.INFO, "SMS Checker: {}".format(sms_check))
    
    if sms_event is not None:
        log(LogLevel.INFO, "SMS Checker Event: {}".format(sms_event))

    log(LogLevel.DEBUG, "SMS Reader Done!")    
    await asyncio.sleep(10)
    return None
