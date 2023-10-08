import cellular
from cellular import SMS
import time
import uasyncio as asyncio
from helper_utils import LogLevel, log, blink_led, LedTime, extract_values

# Check if SIM card is present and return True if it is present else False.
async def check_sim():
    sim = cellular.is_sim_present()
    if not sim:
        blink_led(LedTime.SIM, 0.5)
        log(LogLevel.ERROR, "No SIM Card")
        await asyncio.sleep(3)
    else:
        log(LogLevel.INFO, "SIM Card Present")
    return sim

# Check network status and return True if there is network coverage else False.
async def check_network():
    network = cellular.get_network_status()
    if not network:
        blink_led(LedTime.NETWORK, 0.5)
        log(LogLevel.ERROR, "No Network Coverage")
        await asyncio.sleep(3)
    else:
        log(LogLevel.INFO, "Good Network Coverage")
    return network

# Handle SMS events and return a tuple containing the event type,
# sender phone number and message content.
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

# Send an SMS to the specified phone number with the given message content.
async def send_sms(sms_event: callable, phone_number: str,message: str):
    
    try:

        # Create an instance of the SMS class with the specified phone number and message content.
        t_sms = SMS(phone_number,message)

        blink_led(LedTime.SMS, 0.5)
        await asyncio.sleep(1)
        # Send the SMS using the send() method of the SMS class.
        log(LogLevel.INFO,
        "SENDING SMS| To: {}, content: {}".format(phone_number,message))
        t_sms.send()
        
        # Register a callback function for handling SMS events using on_sms().
        evt = cellular.on_sms(sms_event)
        
        # Return the event object returned by on_sms().
        return evt

    except Exception as e:
        
        # Log any errors that occur while sending an SMS.
        log(LogLevel.ERROR,"Error occurred while sending SMS: {}".format(e))
        
        # Wait for 1 second before returning control to the caller.
        await asyncio.sleep(1)

# Make a call to the specified phone number and register a callback function for handling call events.
async def make_call(call_event: callable ,phone_number: str):
    while True:
        # Register a callback function for handling call events using on_call().
        cellular.on_call(call_event)
        try:
            log(LogLevel.INFO, "DIALING | Phone Number: {}".format(phone_number))
            blink_led(LedTime.CALL, 0.5)
            await asyncio.sleep(1)
            # Dial the specified phone number using dial().
            cellular.dial(phone_number)

        except Exception as e:
            # Log any errors that occur while making a call.
            log(LogLevel.ERROR,"Error occurred while dialing : {}".format(e))
            # Wait for 5 seconds before returning control to the caller.
        await asyncio.sleep(15)

# Handle call events and print them to console. 
def call_event(evt_call):
    
    log(LogLevel.INFO,"CALL EVENT : {}".format(evt_call))

    return evt_call

# Read all messages in inbox and delete them from SIM card memory. 
async def list_reader():

    sms_list = last_sms = sms_content = sms_sender = None
    
    log(LogLevel.DEBUG,"List Reader Initiated!")
    
    sms_list = SMS.list()
    
    if sms_list:

        last_index=len(sms_list)-1
        
        last_message=sms_list[last_index]
        
        sms_content=last_message.message
        
        sms_sender=last_message.phone_number
        
        log(
            LogLevel.INFO,
            "LAST SMS | content: {}, from: {}".format(sms_content, sms_sender)
        )
        
        for l_msg in sms_list:

                try:

                    l_msg.withdraw()

                    log(
                        LogLevel.DEBUG,
                        "Message Deleted! Content:{}, From:{}".format(l_msg.message,l_msg.phone_number)
                    )

                except Exception as e:

                    log(
                        LogLevel.ERROR,
                        "Error occurred : {} | Deleting Message:{}".format(e,l_msg)
                    )

        return sms_content
    else:

        log(
            LogLevel.INFO,
            "No messages in inbox."
        )

    await asyncio.sleep(10)

    return None


# Read incoming messages from SIM card memory and handle them using a callback function. 
async def sms_reader(sms_event : callable):

    try:
        # Register a callback function for handling incoming messages using on_sms().
        reader = cellular.on_sms(sms_event)
        log(
            LogLevel.INFO,
            "Reader Value : {}".format(reader)
            )
    except Exception as e:
            pass



