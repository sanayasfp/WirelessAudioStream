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
import machine
import time
import gps
import cellular
import hashlib

# Variables
call_phone_number = "6573788850"
server_phone_number = "+16573788850"
password = "your_password"
device_id = ""
led = machine.Pin(27, machine.Pin.OUT)
previous_voltage = None

# Hash device_id as a 10 digits number
def generate_device_id(imei, password):
    m = hashlib.sha256()
    m.update(imei.encode('utf-8'))
    m.update(password.encode('utf-8'))
    hash_bytes = m.digest()[:5]  
    device_id_int = int.from_bytes(hash_bytes, 'big')  
    return "{:010d}".format(device_id_int)

# Voltage Decrease function
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

# SMS Handler Event
def sms_handler(evt):
    if evt == cellular.SMS_SENT:
        print("SMS SENT", evt)

    #elif evt == cellular.SMS_RECEIVE:
    #    print("SMS RECEIVED")
    #    print("READING...")
    #    ls = cellular.SMS.list()
    #    print(ls[-1])
    else:
        print("SMS RECEIVED:", evt)

# CALL Handler Event
def call_handler(evt):
    print("CALL EVENT:", evt)

    # if evt == cellular.CALL_ACTIVE:
    #     print("CALL ACTIVE")
    # elif evt == cellular.CALL_INCOMING:
    #     print("CALL INCOMING")
    # elif evt == cellular.CALL_NO_ANSWER:
    #     print("CALL NO ANSWER")
    # elif evt == cellular.CALL_BUSY:
    #     print("CALL BUSY")
    # elif evt == cellular.CALL_CONNECT:
    #     print("CALL CONNECTED")
    # elif evt == cellular.CALL_DISCONNECT:
    #     print("CALL DISCONNECTED")
    # else:
    #     print("UNKNOWN CALL EVENT:", evt)


def get_gps():
    gps.on()
    location = gps.get_location()
    satellites = gps.get_satellites()
    gtime = gps.time()
    gps.off()
    return location, satellites, gtime

imei = cellular.get_imei()
device_id = generate_device_id(imei, password)
print("Device ID:", device_id)

# Check if SIM card inserted
sim = cellular.is_sim_present()

if sim == 0:
    # Update every 10 seconds
    while True:
        # Print SIM Status
        location, satellites, gtime = get_gps()
        print("NO SIM Inserted")
        print("LOCATION: ", location)
        print("SATELLITES (tracked, visible): ", satellites)
        print("EPOCH TIME: ", gtime)
        print("VOLTAGE: ", machine.get_input_voltage())
        print("#--------------------------------------#")

        # Blink LED three times
        for _ in range(3):
            led.value(1)
            time.sleep(1)
            led.value(0)
            time.sleep(1)
        time.sleep(10)

# SIM Card inserted
else:

    # SIM status
    print("SIM PRESENT")
    print("ICCID: ", cellular.get_iccid())
    print("IMSI: ", cellular.get_imsi())
    #print("ROAMING: ", cellular.is_roaming())
    #print("FLIGHT MODE: ", cellular.flight_mode())
    #print("SCAN: ", cellular.scan())
    #print("OPERATORS: ", cellular.register())
    
    
    while True:
        # Check Network status
        network_status = cellular.get_network_status()
        print("SIM REGISTER: ", cellular.is_network_registered())
        print("STATIONS: ", cellular.stations())
        print("#--------------------------------------#")

        # Update every 5 seconds
        if network_status != 1:
            # Print NETWORK Status
            print("NO NETWORK COVERAGE")
            print("NETWORK STATUS: ", network_status)
            print("SIGNAL: ", cellular.get_signal_quality())
            print("#--------------------------------------#")

            for _ in range(5):
                # Blink LED five times
                led.value(1)
                time.sleep(1)
                led.value(0)
                time.sleep(1)
            time.sleep(3)
        else:
            # Print NETWORK Status
            print("GOOD NETWORK")
            print("NETWORK STATUS: ", network_status)
            print("SIGNAL: ", cellular.get_signal_quality())
            print("EVENTS INITIATE: ", server_phone_number)

            # Send SMS
            cellular.on_sms(sms_handler)
            cellular.SMS(server_phone_number, password).send()
            #SMS = cellular.SMS(server_phone_number, password)

            # Make Phone Call
            cellular.on_call(call_handler)
            cellular.dial(call_phone_number)
            #call = cellular.dial(call_phone_number)

            print("EVENTS DONE")
            print("#--------------------------------------#")
            while network_status == 1:
                # Check battery voltage every 5 minutes
                time.sleep(300)

                # Check battery voltage Decrease
                if voltage_decreased_by_10_percent():
                    location, satellites, gtime = get_gps()
                    current_voltage = machine.get_input_voltage()[1]
                    print("VOLTAGE: ", current_voltage)
                    print("VOLTAGE DECREASED: ", previous_voltage)
                    print("LOCATION: ", location)
                    print("SATELLITES (tracked, visible): ", satellites)
                    print("EPOCH TIME: ", gtime)
                    print("#--------------------------------------#")
                    message = "ID: {}; Voltage: {}; Location: {}; Satellites: {}".format(device_id, current_voltage, location, satellites)
                    sms = cellular.SMS(server_phone_number, message)
                    sms.send()

                # Check battery voltage below 5%
                if machine.get_input_voltage()[1] <= 5:
                    call.hangup()

                    # Blink LED every 2 seconds
                    while True:
                        print("BATTERY LOW!", machine.get_input_voltage())
                        print("#--------------------------------------#")
                        led.value(1)
                        time.sleep(2)
                        led.value(0)
                        time.sleep(2)




