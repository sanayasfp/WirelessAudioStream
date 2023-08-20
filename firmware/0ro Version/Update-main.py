import machine
import time
import gps
import cellular
import hashlib
import uasyncio as asyncio

# Variables
call_phone_number = "6573788850"
server_phone_number = "+16573788850"
password = "your_password"
message = None
device_id = None
led = machine.Pin(27, machine.Pin.OUT)
previous_voltage = None
status = None
authentication = False
flag = False
breaking_line = "#--------------------------------------#"

# Generate a unique device ID based on the device's IMEI and a given password
def generate_device_id(imei, password):
    m = hashlib.sha256()
    m.update(imei.encode('utf-8'))
    m.update(password.encode('utf-8'))
    hash_bytes = m.digest()[:5]
    device_id_int = int.from_bytes(hash_bytes, 'big')
    return "{:010d}".format(device_id_int)

# Check if the battery voltage has decreased by 10% or more
def voltage_decreased_by_10_percent():
    global previous_voltage
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

# Handle SMS events
def sms_handler(evt_sms):
    if evt_sms == cellular.SMS_SENT:
        print("SMS SENT: ", evt_sms)
        return evt_sms
    else:
        print("SMS RECEIVED: ", evt_sms)
        return evt_sms

# Handle call events
def call_handler(evt_call):
    print("CALL EVENT:", evt_call)
    return evt_call

# Get the device's IMEI and generate a unique device ID
imei = cellular.get_imei()
device_id = generate_device_id(imei, password)
print("Device ID:", device_id)
print(breaking_line)

# Check if a SIM card is present in the device
#sim = cellular.is_sim_present()

# Initialize SMS and call objects
#t_sms = cellular.SMS(server_phone_number, message)
#call = cellular.dial(call_phone_number)

# Get the current cellular network status
#network_status = cellular.get_network_status()

# Initiate GSM events (sending SMS and making calls) based on different conditions
async def make_GSM_event():
    global message
    global flag
    global status
    while True:
        print("Status: ", status)
        print("Flag: ", flag)
        print(breaking_line)
        if device_id == "0000000000":
            print("GSM EVENT INITIATED: ", server_phone_number)
            location, satellites, gtime = await get_gps()
            current_voltage = machine.get_input_voltage()[1]
            print("SMS INITIATED")
            # Update the message here
            message = "INIT | ID: {}; Voltage: {}; Location: {}; Satellites: {}".format(device_id, current_voltage, location, satellites)
            cellular.on_sms(sms_handler)
            t_sms = cellular.SMS(server_phone_number, message)
            try:
                t_sms.send()
            except Exception as e:
                print("Error occurred while Sending SMS: ", e)
            await asyncio.sleep(5)
            print("SMS EXECUTED: ", message)
            print(breaking_line)
            await asyncio.sleep(1)

            print("CALL INITIATED")
            cellular.on_call(call_handler)
            try:
                cellular.dial(call_phone_number)
            except Exception as e:
                print("Error occurred while dialing: ", e)
            print("CALL EXECUTED")
            print(breaking_line)
            await asyncio.sleep(1)

        else:
            await blink_led(2, 1)
            print("WAITING FOR CONNECTION...")
            print(breaking_line)
            await asyncio.sleep(1)

# Retrieve GPS location, satellite information, and time
async def get_gps():
    gps.on()
    location = gps.get_location()
    satellites = gps.get_satellites()
    gtime = gps.time()
    gps.off()
    return location, satellites, gtime

# Blink the LED a specified number of times with a given delay
async def blink_led(times, delay):
    for _ in range(times):
        led.value(1)
        await asyncio.sleep(delay)
        led.value(0)
        await asyncio.sleep(delay)

# Check if a SIM card is present and perform actions accordingly
async def check_sim_card():
    global message
    global device_id
    global authentication
    
    while True:
        location, satellites, gtime = await get_gps()
        current_voltage = machine.get_input_voltage()[1]
        network_status = cellular.get_network_status()
        sim = cellular.is_sim_present()
        if sim == 0:
            print("NO SIM Inserted")
            print("LOCATION: ", location)
            print("SATELLITES (tracked, visible): ", satellites)
            print("EPOCH TIME: ", gtime)
            print("VOLTAGE: ", machine.get_input_voltage())
            print(breaking_line)
            await blink_led(3, 1)
            await asyncio.sleep(10)
        else:
            print("SIM PRESENT")
            print("ICCID: ", cellular.get_iccid())
            print("IMSI: ", cellular.get_imsi())
            print(breaking_line)
            if network_status != 1:
                print("NO NETWORK COVERAGE")
                print("SIM REGISTER: ", cellular.is_network_registered())
                print("STATIONS: ", cellular.stations())
                print("NETWORK STATUS: ", network_status)
                print("SIGNAL: ", cellular.get_signal_quality())
                print(breaking_line)
                await blink_led(5, 1)
                await asyncio.sleep(10)
            else:
                print("GOOD NETWORK")
                print("SIM REGISTER: ", cellular.is_network_registered())
                print("STATIONS: ", cellular.stations())
                print("NETWORK STATUS: ", network_status)
                print("SIGNAL: ", cellular.get_signal_quality())
                print(breaking_line)
                print("AUTHENTICATION STATUS: ", authentication)
                if authentication != True:
                    # Update the message here
                    message = "AUTH | IMEI: {}; Voltage: {}; Location: {}; Satellites: {}".format(imei, current_voltage, location, satellites)
                    cellular.on_sms(sms_handler)
                    t_sms = cellular.SMS(server_phone_number, message)
                    try:
                        t_sms.send()
                    except Exception as e:
                        print("Error occurred while Sending SMS: ", e)
                    await asyncio.sleep(5)
                    print("AUTHENTICATION SMS SENT")
                    print("MESSAGE: ", message)
                    authentication = True
                print("AUTHENTICATION COMPLETED: ", authentication)
                print(breaking_line)
                device_id = "0000000000"
                print("ID UPDATED")
                print("DEVICE ID: ", device_id)
                print(breaking_line)
                await asyncio.sleep(10)

# Monitor the battery voltage and perform actions depending on the voltage level
async def monitor_battery_voltage():
    global message
    
    while True:
        location, satellites, gtime = await get_gps()
        current_voltage = machine.get_input_voltage()[1]
        network_status = cellular.get_network_status()
        if machine.get_input_voltage()[1] <= 5:
            await blink_led(1, 2)
            print("BATTERY LOW!", machine.get_input_voltage())
            print("LOCATION: ", location)
            print("SATELLITES (tracked, visible): ", satellites)
            print("EPOCH TIME: ", gtime)
            print(breaking_line)
            await asyncio.sleep(10)
            if network_status != 0:
                print("LOW VOLTAGE SMS")
                # Update the message here
                message = "LOW BAT| ID: {}; Voltage: {}; Location: {}; Satellites: {}".format(device_id, current_voltage, location, satellites)
                cellular.on_sms(sms_handler)
                t_sms = cellular.SMS(server_phone_number, message)
                try:
                    t_sms.send()
                except Exception as e:
                    print("Error occurred while Sending SMS: ", e)
                await asyncio.sleep(5)
                print("MESSAGE: ", message)
                print(breaking_line)
                if flag == True:
                    cellular.hangup()
                await asyncio.sleep(10)
        else:
            print("VOLTAGE: ", current_voltage)
            print("LOCATION: ", location)
            print("SATELLITES (tracked, visible): ", satellites)
            print("EPOCH TIME: ", gtime)
            print(breaking_line)
            await asyncio.sleep(10)
            if voltage_decreased_by_10_percent():
                print("VOLTAGE DECREASED: ", previous_voltage)
                print("VOLTAGE: ", current_voltage)
                if network_status != 0:
                    print("VOLTAGE DECREASED SMS")
                    # Update the message here
                    message = "VOLT | ID: {}; Voltage: {}; Location: {}; Satellites: {}".format(device_id, current_voltage, location, satellites)
                    cellular.on_sms(sms_handler)
                    t_sms = cellular.SMS(server_phone_number, message);
                    try:
                        t_sms.send()
                    except Exception as e:
                        print("Error occurred while Sending SMS: ", e)
                    await asyncio.sleep(5)
                    print("MESSAGE: ", message)
                    print(breaking_line)

# Main function to run the tasks asynchronously
async def main():
    asyncio.create_task(monitor_battery_voltage())
    asyncio.create_task(check_sim_card())
    asyncio.create_task(make_GSM_event())

    while True:
        await asyncio.sleep(1)

# Run the main function
asyncio.run(main())
