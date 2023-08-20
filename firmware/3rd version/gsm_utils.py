import cellular
import uasyncio as asyncio
from helper_utils import LogLevel, log, blink_led, LedTime, extract_values

async def check_sim():
    """
    Check if SIM card is present.

    :return: True if SIM card is present, otherwise False.
    """
    sim = cellular.is_sim_present()
    if not sim:
        await blink_led(LedTime.SIM, 2)
        log(LogLevel.ERROR, "No SIM Card")
        await asyncio.sleep(3)
    else:
        log(LogLevel.INFO, "SIM Card Present")
    return sim

async def check_network():
    """
    Check network status.

    :return: True if there is network coverage, otherwise False.
    """
    network = cellular.get_network_status()
    if not network:
        await blink_led(LedTime.NETWORK, 2)
        log(LogLevel.ERROR, "No Network Coverage")
        await asyncio.sleep(3)
    else:
        log(LogLevel.INFO, "Good Network Coverage")
    return network

def sms_event(evt_sms) -> tuple:
    log(LogLevel.INFO, "SMS EVENTS: {}".format(evt_sms))
    
    if evt_sms is None:
        log(LogLevel.INFO, "NO SMS EVENT: {}".format(evt_sms))
        return evt_sms, None,None
    elif evt_sms == cellular.SMS_SENT:
        log(LogLevel.INFO, "SMS SENT: {}".format(evt_sms))
        return evt_sms, None,None
    else:
        message = evt_sms.message
        sender = evt_sms.phone_number
        log(LogLevel.INFO,
            "SMS RECEIVED | From: {}, content: {}".format(sender,message))
        
        # Return the event type along with the sender phone number and message content.
        return evt_sms,sender,message
    
async def send_sms(sms_event: callable, phone_number: str, message: str):
    """
    Send an SMS to the specified phone number with the given message content.

    :param sms_event: Callback function for handling SMS events.
    :param phone_number: Phone number to send the SMS.
    :param message: The content of the SMS.
    :return: The event object returned by on_sms().
    """
    try:
        # Create an instance of the SMS class with the specified phone number and message content.
        t_sms = cellular.SMS(phone_number, message)

        await blink_led(LedTime.SMS, 2)
        await asyncio.sleep(1)
        
        # Send the SMS using the send() method of the SMS class.
        log(LogLevel.INFO, "SENDING SMS| To: {}, content: {}".format(phone_number,message))
        t_sms.send()
        
        # Register a callback function for handling SMS events using on_sms().
        evt = cellular.on_sms(sms_event)
        
        # Return the event object returned by on_sms().
        return evt

    except Exception as e:
        # Log any errors that occur while sending an SMS.
        log(LogLevel.ERROR, "Error occurred while sending SMS: {}".format(e))
        # Wait for 1 second before returning control to the caller.
        await asyncio.sleep(1)

async def make_call(call_event: callable, phone_number: str):
    """
    Make a call to the specified phone number and register a callback function for handling call events.

    :param call_event: Callback function for handling call events.
    :param phone_number: Phone number to make the call.
    """
    # Register a callback function for handling call events using on_call().
    t_call = cellular.on_call(call_event)
    log(LogLevel.INFO,"T CALL: {}".format(t_call))
    
    #Check for No Ongoing call and Call just Stopped
    while t_call is None:
        try:
            log(LogLevel.INFO, "DIALING | Phone Number: {}".format(phone_number))
            await blink_led(LedTime.CALL, 2)
            # Dial the specified phone number using dial().
            cellular.dial(phone_number)
        except Exception as e:
            # Log any errors that occur while making a call.
            log(LogLevel.ERROR,"Error occurred while dialing : {}".format(e))
            
        # Wait for 1 seconds before attempting to make a call again.
        await asyncio.sleep(1)

def call_event(evt_call):
    # Handle call events and print them to console. 
    log(LogLevel.INFO,"CALL EVENT : {}".format(evt_call))

    return evt_call

async def list_reader():
    """
    Read all messages in the inbox and delete them from SIM card memory.

    :return: The content of the last SMS message or None if there are no messages.
    """
    sms_list = cellular.SMS.list()
    
    if sms_list:
        try:
            last_message = sms_list[-1]
            sms_content = last_message.message
            sms_sender = last_message.phone_number
            log(LogLevel.INFO, "LAST SMS | content: {}, from: {}".format(sms_content, sms_sender))

            try:
                for l_msg in sms_list:
                    l_msg.withdraw()
                    log(LogLevel.DEBUG, "Message Deleted! Content:{}, From:{}".format(l_msg.message,l_msg.phone_number))
            except Exception as e:
                log(LogLevel.ERROR, "Error occurred : {} | Deleting Message:{}".format(e,l_msg))
            return sms_content
        except Exception as e:
            log(LogLevel.ERROR, "Error occurred while reading message : {} |  Message List:{}".format(e,sms_list))
    else:
        log(LogLevel.INFO, "No messages in inbox.")
        return None

async def sms_reader(sms_event: callable):
    """
    Read incoming messages from SIM card memory and handle them using a callback function.

    :param sms_event: Callback function for handling SMS events.
    """
    try:
        # Register a callback function for handling incoming messages using on_sms().
        reader = cellular.on_sms(sms_event)
        log(LogLevel.INFO, "Reader Value : {}".format(reader))
    except Exception as e:
        pass

