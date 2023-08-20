# Wearer Lab

## Necklace Firmware

This code is the firmware for the wearer necklace product.
The device is built on top of an A9G GPS/GPRS device program with micro python.
for more details, visit our *Website* : <https://www.wearer.xyz>

The code has been written in micro python based on PULKIN *main micro python on A9G repo* : <https://github.com/pulkin/micropython>
If you want to learn more about *micro python* : <https://micropython.org/>

### Detailed Algorithm

#### main.py

1. Import necessary libraries
   1. json
   2. asyncio
2. Import helper_utils.py functions
   1. get_imei
   2. generate_id
   3. device_auth
   4. log
   5. LogLevel
3. Import battery_utils.py functions
   1. monitor_voltage
   2. low_voltage
4. Import gsm_utils.py functions
   1. check_sim
   2. check_network
   3. make_call
   4. sms_event
5. Load config variables from json file
6. Initiate main function as async
7. Declare function variable
   1. user_phone_number as **USER_PHONE_NUMBER** from config.json
   2. server_phone_number as **SERVER_PHONE_NUMBER** from config.json
   3. sleep_time as **SLEEP_TIME** from config.json
   4. device_imei
   5. device_id
   6. user_password
   7. sim_status
   8. network_status
   9. authentication_status
   10. voltage_status
   11. monitor_voltage_task
   12. low_voltage_task
   13. call_task
   14. sms_task
8. **log** Initialization with all variables as *DEBUG* level
9. Execute **get_imei** function from *helper_utils.py*
10. Pass the value of **get_imei** to **device_imei**
11. Execute **check_sim** function from *gsm_utils.py*
12. Pass the value of **check_sim** to **sim_status**
    1. While **sim_status** is "True"
       1. Execute **check_network** function from *gsm_utils.py*
       2. Pass the value of **check_network** to **network_status**
          1. While **network_status** is "True"
             1. If **authentication_status** is "False"
                1. Execute **device_auth** function from *helper_utils.py*
                   1. Return **authentication_status** and **user_password**
             2. If **authentication_status** is "True" and **user_password** is not "None"
                1. Execute **generate_id** function from *helper_utils.py*
                2. Define an async task **monitor_voltage_task**
                   1. Execute **monitor_voltage** function from *battery_utils.py*
                3. Define an async task **call_task**
                   1. Execute **make_call** function from *gsm_utils.py*
                4. Define an async task **sms_task**
                   1. Execute **sms_event** function from *gsm_utils.py*
                5. Define an async task **low_voltage_task**
                   1. Execute **low_voltage** function from *battery_utils.py*
                   2. Pass the value of **low_voltage_task** to **voltage_status**
                   3. While **low_voltage_task** is "True"
                      1. Stop **monitor_voltage_task**, **call_task**, **sms_task**
13. While "True"
    1. Sleep for 1/10 of **sleep_time**
14. Run *main* function async

---

#### helper_utils.py

1. Import necessary libraries
   1. machine
   2. json
   3. hashlib
   4. re
   5. asyncio
2. Declare function variable
   1. sleep_time as **SLEEP_TIME** from config.json
   2. led_pin as **LED_PIN** from config.json
   3. device_id
   4. user_password
3. Import gsm_utils.py functions
   1. send_sms
   2. sms_event
4. Import gps_utils.py functions
   1. get_gps
5. Import battery_utils.py functions
   1. get_voltage
6. Define class **LogLevel**
   1. DEBUG = 0
   2. INFO = 1
   3. WARNING = 2
   4. ERROR = 3
7. Define class **LedTime**
   1. SIM = 5
   2. NETWORK = 4
   3. AUTH = 3
   4. BATTERY = 2
8. Define **log** function
    """
    Log a message at the given log level.

    :param level: Log level (e.g., LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, or LogLevel.ERROR)
    :param msg: Message to be logged
    """  
9. Define **blink_led** function
    """
    Blink the LED a specified number of times with a given delay.

    :param pin: An integer representing the GPIO pin number for the LED
    :param times: Blink time (e.g., LedTime.SIM, LedTime.NETWORK, LedTime.AUTH, or LedTime.BATTERY)
    :param delay: Factor of **sleep_time** between each blink
    """
10. Define **get_imei** function
    """
    Retrieve Network Module unique IMEI number.

    :**log**: device_imei as *INFO* level
    :return: **device_imei** as a string
    """
11. Define **generate_id** function
    """
    Generate a unique device ID (hash function) based on the device's IMEI and a given password.

    :param **device_imei**: The unique device's IMEI
    :param **user_password**: The password for the device as a string
    :**log**: device_id as *INFO* level
    :return: **device_id** as a string
    """
12. Define **extract_bulk** function
    """
    Extract specified key values pairs from an input message using regular expressions.

    :param **sms_msg**: The input message as a string
    :**log**: bulk_values as *INFO* level
    :return **values**: A dictionary containing the extracted values as key-value pairs
    """
13. Define **extract_values** function
    """
    Extract the specified values from an input message using regular expressions.

    :param **sms_msg**: The input message as a string
    :**log**: extract_values as *INFO* level
    :return **type**, **password**, **id**, **values** : as a tuple
    """
14. Define **device_auth** function
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

---

#### battery_utils.py
1. Import necessary libraries
   1. machine
   2. json
   3. asyncio
2. Declare function variable
   1. sleep_time as **SLEEP_TIME** from config.json
   2. threshold_value as **THRESHOLD_VALUE** from config.json
3. Import helper_utils.py functions
   1. log
   2. LogLevel
   3. blink_led
4. Import gsm_utils.py functions
   1. send_sms
   2. sms_event
5. Import gps_utils.py functions
   1. get_gps
6. Define **get_voltage** function
    """
    Read device battery voltage and percentage.

    :**log**: *CURRENT VOLTAGE | battery_voltage, battery_percentage* as *INFO* level
    :return: **battery_voltage**, **Battery_percentage** as a tuple
    """
7. Define **monitor_voltage** function
    """
    - Get **Battery_percentage** value from **get_voltage** function
    - Compute **voltage_difference** = **previous_voltage** - **current_voltage**.
    - If **voltage_difference** >= 2x **threshold_value**
      - Get **device_location** and **device_satellites** from **get_gps** function from *gps_utils.py*
      - Get **Battery_percentage** value from **get_voltage** function
      - Send *VOLTAGE DECREASE* | **device_id**, **Battery_percentage**, **device_location** and **device_satellites** values back to server via SMS using **send_sms** function from *gsm_utils.py*

    :param: **device_id**, **previous_voltage**, **threshold_value**
    :**log**: *VOLTAGE DECREASE | battery_percentage* as *INFO* level
    :return: *boolean* value
    """
8. Define **low_voltage** function
    """
    - Get **Battery_percentage** value from **get_voltage** function
    - If **Battery_percentage** <= **threshold_value**
      - Get **device_location** and **device_satellites** from **get_gps** function from *gps_utils.py*
      - Send *LOW BATTERY* | **device_id**, **Battery_percentage**, **device_location** and **device_satellites** values back to server via SMS using **send_sms** function from *gsm_utils.py*

    :param: **device_id**, **threshold_value**
    :**log**: *LOW BATTERY | battery_percentage* as *INFO* level
    :return: *boolean* value
    """

---

#### gps_utils.py

1. Import necessary libraries
   1. gps
   2. json
   3. asyncio
2. Declare function variable
   1. sleep_time as **SLEEP_TIME** from config.json
3. Import helper_utils.py functions
   1. log
   2. LogLevel
4. Define class **GpsContext**
   1. __aenter__ -> gps.pn
   2. __aexit__ -> gps.off
5. Define **get_gps** function
    """
    - Initiate **GpsContext** as **gps_instance**
    - Declare **device_location**, **device_satellites** and **gps_time** as variables
    - Read these variables with get_location function while passing gps_instance class from gps.

    :**log**: *GPS DATA | device_location, device_satellites, gps_time* as *INFO* level
    :return: **device_location**, **device_satellites** and **gps_time** as a tuple
    """

---

#### gsm_utils.py

1. Import necessary libraries
   1. machine
   2. cellular
   3. json
   4. asyncio
2. Declare function variable
   1. sleep_time as **SLEEP_TIME** from config.json
   2. led_pin as **LED_PIN** from config.json
3. Import helper_utils.py functions
   1. log
   2. LogLevel
4. Define **check_sim** function
    """
    - Initiate **sim** variable
    - Retrieve sim card status from is_sim_present function from cellular.
    - Pass it to **sim**
    - If **sim** is "False"
      - **blink_led** on **led_pin** with **LedTime.SIM** and 1/10 of **sleep_time**
      - **log**: *NO SIM CARD* as *ERROR* level
    - If **sim** is "True"
      - **log**: *SIM CARD PRESENT* as *INFO* level

    :return: **sim** value
    """
5. Define **check_network** function
    """
    - Initiate **network** variable
    - Retrieve sim card status from is_network_status function from cellular.
    - Pass it to **network**
    - If **network** is "False"
      - **blink_led** on **led_pin** with **LedTime.NETWORK** and 1/10 of **sleep_time**
      - **log**: *NO NETWORK COVERAGE* as *ERROR* level
    - If **network** is "True"
      - **log**: *GOOD NETWORK COVERAGE* as *INFO* level

    :return: **network** value
    """
6. Define **sms_event** function
    """
    :param: **evt_sms**
    - If **evt_sms** == cellular.SMS_SENT
        :**log**: *SMS EVENT, evt_sms* as *INFO* level
        :return: **evt_sms**
    - If **evt_sms** == 1
        :**log**: *SMS SENT, evt_sms* as *INFO* level
        :return: **evt_sms**
    - If **evt_sms** is equal to something else
        - Initiate **message** and pass evt_sms.message
        - initiate **sender** and pass evt_sms.phone_number
        - :**log**: *SMS RECEIVED, from: sender, content: message* as *INFO* level
        - Try
          - Initiate **type**, **password**, **id**, **values**
          - Execute **extract_values** from *helper_utils.py*
          - Pass the response of **extract_values** to **type**, **password**, **id**, **values**
          - :**log**: *EXTRACTED VALUES: type, password, id, values* as *INFO* level
          - :return: **type**, **password**, **id**, **values** as tuple
        - Error
          - :**log**: *ERROR READING SMS MESSAGE* as *ERROR* level
          - :return: **evt_sms**
    """
7. Define **send_sms** function
    """
    :param: **sms_event** as callable function, **phone_number**as "string", **message** as "string"
    - Try
      - :**log**: *SENDING SMS: phone_number, message* as *INFO* level
      - Initiate **t_sms** variable equal to SMS from *cellular* with **phone_number** and **message** 
      - Execute **send** function from *cellular* on **t_sms**
      - Execute **sms_event**
    - Error
      - :**log**: *ERROR SENDING SMS* as *ERROR* level
    """
8. Define **make_call** function
    """
    :param: **call_event** as callable function, **phone_number** as "string"
    - Try
      - :**log**: *CALL IN PRGRESS: phone_number* as *INFO* level
      - Execute **dial** function with **phone_number** from *cellular*
      - Execute **call_event**
    - Error
      - :**log**: *ERROR CALLING* as *ERROR* level
    """
9. Define **call_event** function
    """
    :param: **evt_call**
    :**log**: *CALLING: evt_call* as *INFO* level
    :return: **evt_call**
    """

---

#### config.json

1. Set **USER_PHONE_NUMBER** = 7266008987
2. Set **SERVER_PHONE_NUMBER** = +17266008987
3. Set **THRESHOLD_VALUE** = 5
4. Set **SLEEP_TIME** = 10
5. Set **LED_PIN** = 27
