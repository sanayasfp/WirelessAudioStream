import machine
import math
import time

# Configuration
threshold = 750  # Adjust this threshold value according to your environment

# Set the microphone as the input source
mic = machine.Pin(25, machine.Pin.IN)

# Initialize ADC (Analog-to-Digital Converter)
adc = machine.ADC(0)  # Use ADC channel 0 (assuming it's connected to the microphone)

# Function to perform voice detection
def tresh_voice():
    while True:
        # Read ADC value
        adc_value = adc.read()

        # Check if ADC value is above the threshold
        if adc_value > threshold:
            print("Voice detected!")
            # Additional code for voice detection action
    time.sleep(3)
# Call the voice detection function
tresh_voice()

def detect_voice():
    mic.on()
    # Start listening for speech
    while True:
        # Wait for the user to say something
        if mic.value():
            # Start a timer
            start = time.time()

            # Listen for speech for 2 seconds
            while time.time() - start < 2:
                if mic.value():
                    pass
                else:
                    break

            # If the user was speaking for 2 seconds, then they probably said something
            if time.time() - start >= 2:
                print("You said something!")
        time.sleep(0.1)
        # Turn off the microphone
        mic.off()
detect_voice()


