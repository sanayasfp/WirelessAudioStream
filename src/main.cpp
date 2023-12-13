//*
//* Program Name: Audio Recording Program
//*
//* Description:
//* This Arduino program is designed to record audio data from a microphone using the ESP32's I2S interface.
//* The recorded audio data is then transmitted via a WebSocket connection to a remote server.
//* The program also monitors the battery status and responds to control button events.
//*
//* License:
//* This program is licensed under the MIT License. You are free to use, modify, and redistribute it
//* in accordance with the terms of the license.
//*
//* Ownership:
//* This program was developed by Sana Yasfp. All rights are reserved to Sana Yasfp.
//*
//* Author: YAVO Abouho Sana Franklin Prince
//* Date of Creation: October 19th, 2023 10:15 PM
//*

#include <Arduino.h>
#include <I2S.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoWebsockets.h>
#include <AceButton.h>

//*****************************************Variable and Constants Declarations******************************************//

#define USE_SERIAL 1

// Variables to be used in the recording program, do not change for best
#define SAMPLE_RATE 16000U
#define BITS_PER_SAMPLE 16
#define VOLUME_GAIN 2
// #define RECORD_TIME 0.5 // in seconds, The maximum value is 240
#define NUM_BUFFERS 3
#define BUFFER_SIZE 2048

#define MONITORING_LED_PIN GPIO_NUM_1
#define CONTROLL_BUTTON_PIN GPIO_NUM_5
#define BATTERY_MONITORING_LED_PIN GPIO_NUM_3
#define BATTERY_VOLTAGE_PIN GPIO_NUM_7
#define WAKEUP_ON_RISING_EDGE 1
// #define WAKEUP_ON_FALLING_EDGE 0
#define OFF_DELAY 2000
#define ON_DELAY 2500
#define MIN_BATTERY_VOLTAGE 0
#define MAX_BATTERY_VOLTAGE 3.3

const char *ssid = "TECNO SPARK 10 Pro";
const char *password = "1234567890qwertY";
// const char *ssid = "DIP RDC 2GHZ";
// const char *password = "cool8888";
// const char *ssid = "FAMILLE KAMAGATE";
// const char *password = "23042001";

const char *webSocketServerAddress = "192.168.251.3";
const int webSocketServerPort = 8080;
const char *webSocketServerPath = "/ws/v1/test";

// Number of bytes required for the recording buffer
// uint32_t record_size = (SAMPLE_RATE * BITS_PER_SAMPLE / 8) * RECORD_TIME;

uint8_t recBuffers[NUM_BUFFERS][BUFFER_SIZE] = {0};
volatile int currentRecBuffer = 0;
volatile int readyRecBuffer = -1;
volatile bool isWIFIConnected;
volatile bool isWebSocketConnected;
volatile bool isRecording = false;
volatile bool isReadyForRecording = false;
volatile uint64_t inactiveTime;
volatile uint32_t readyRecBufferSampleSize = 0;
RTC_DATA_ATTR bool isSystemON = false;

WiFiClientSecure client;

using namespace websockets;
WebsocketsClient websocket;

using namespace ace_button;
AceButton controllButton(CONTROLL_BUTTON_PIN);

TaskHandle_t TaskHandle_xTaskWifiConnect;
TaskHandle_t TaskHandle_xTaskWebSocketConnect;
TaskHandle_t TaskHandle_xTaskAudioCapture;
TaskHandle_t TaskHandle_xTaskTransmitAudio;
TaskHandle_t TaskHandle_xTaskSystemMonitoring;

//*****************************************Functions Definitions******************************************//

void cfInitI2S(void);
void cfSetupControllButton(void);
void cfSetupDeepSleep(void);
void cfSetupMonitoring(void);
void xTaskWifiConnect(void *pvParameters);
void xTaskWebSocketConnect(void *pvParameters);
void xTaskAudioCapture(void *pvParameters);
void xTaskTransmitAudio(void *pvParameters);
void xTaskSystemMonitoring(void *pvParameters);
void webSocketEventHandler(WebsocketsEvent event, String data);
void controllButtonEventHandler(AceButton *, uint8_t, uint8_t);
void controllButtonClickedEventHandler(void);
void controllButtonDoubleClickedEventHandler(void);
void controllButtonRepeatPressedEventHandler(void);
void controllButtonPressedRawEventHandler(void);
void increaseVolumeGain(uint8_t *recBuffer, uint32_t sampleSize);
// void transmitDataViaWebSocket(uint8_t *data, uint32_t size);
void transmitLinear16DataViaWebSocket(const int16_t *data, size_t size);
void transmitLinear16DataViaWebSocketPerChunk(const int16_t *data, size_t size, const int chunkSize = 1024);
bool isTaskInStateUtil(TaskHandle_t task, eTaskState stateToCheck);
void systemOffUtil(int offDelay = OFF_DELAY);
void systemOnUtil(void);
void waitForSystemOnUtil(void);
void printWakeupReasonUtil(void);
void blinkLEDUtil(uint8_t LED_PIN, uint8_t times, TickType_t onDuration, TickType_t offDuration);
int mesureBatteryPercentageUtil(float voltage, float minVoltage = 0, float maxVoltage = 3.3);
float mesureBatteryVoltageUtil(int analogVoltage, float referenceVoltage = 3.3, float referenceVoltageInAnalogValue = 4095.0);
bool isBufferEmptyUtil(const uint8_t *buffer, size_t bufferSize, uint8_t emptyValue = 0);
void suspendAudioTaskUtil();
void resumeAudioTaskUtil();
void pcmToLinear16Util(const uint8_t *pcmBuffer, int16_t *linear16Buffer, size_t pcmBufferSize);

//*****************************************Arduino Base******************************************//

void setup()
{
  // #ifndef USE_SERIAL
  Serial.begin(115200);
  while (!Serial)
    ;
  // #endif

  // Print the wakeup reason for ESP32
  // printWakeupReasonUtil(); // TODO: uncomment for deep sleep mode debugging

  cfSetupControllButton();
  // cfSetupDeepSleep();

  controllButtonPressedRawEventHandler();

  cfSetupMonitoring();
  cfInitI2S();

  xTaskCreatePinnedToCore(xTaskSystemMonitoring, "SystemMonitoring", 4096, NULL, 1, &TaskHandle_xTaskSystemMonitoring, 1);
  delay(500);
  xTaskCreatePinnedToCore(xTaskWifiConnect, "WifiConnect", 4096, NULL, 2, &TaskHandle_xTaskWifiConnect, 1);
  vTaskDelay(500);
  xTaskCreatePinnedToCore(xTaskWebSocketConnect, "WebSocketConnect", 4096, NULL, 2, &TaskHandle_xTaskWebSocketConnect, 1);
  delay(500);
  xTaskCreatePinnedToCore(xTaskAudioCapture, "I2sAdc", 1024 * 8, NULL, 1, &TaskHandle_xTaskAudioCapture, 0);
  delay(500);
  xTaskCreatePinnedToCore(xTaskTransmitAudio, "I2sAdc", 1024 * 8, NULL, 3, &TaskHandle_xTaskTransmitAudio, 1);
}

void loop()
{
  controllButton.check();
}

//*****************************************Configuration******************************************//

void cfInitI2S(void)
{
  I2S.setAllPins(-1, 42, 41, -1, -1);

  // The transmission mode is PDM_MONO_MODE, which means that PDM (pulse density modulation)
  // mono mode is used for transmission
  if (!I2S.begin(PDM_MONO_MODE, SAMPLE_RATE, BITS_PER_SAMPLE))
  {
    Serial.println("ERROR: Failed to initialize I2S!");
    while (1)
      ;
  }
}

void cfSetupControllButton(void)
{
  pinMode(CONTROLL_BUTTON_PIN, INPUT_PULLUP);

  // Configure the ButtonConfig with the event handler, and enable all higher
  // level events.
  ButtonConfig *controllButtonConfig = controllButton.getButtonConfig();
  controllButtonConfig->setEventHandler(controllButtonEventHandler);
  controllButtonConfig->setFeature(ButtonConfig::kFeatureClick);
  controllButtonConfig->setFeature(ButtonConfig::kFeatureDoubleClick);
  controllButtonConfig->setFeature(ButtonConfig::kFeatureRepeatPress);
  controllButtonConfig->setFeature(ButtonConfig::kFeatureSuppressClickBeforeDoubleClick);
  controllButtonConfig->setFeature(ButtonConfig::kFeatureSuppressAfterDoubleClick);
  controllButtonConfig->setFeature(ButtonConfig::kFeatureSuppressAfterClick);
}

void cfSetupDeepSleep(void)
{
  // Setup wakeup with ext0 on a rising edge (button press)
  esp_sleep_enable_ext0_wakeup(CONTROLL_BUTTON_PIN, WAKEUP_ON_RISING_EDGE);
}

void cfSetupMonitoring(void)
{
  pinMode(MONITORING_LED_PIN, OUTPUT);
  pinMode(BATTERY_MONITORING_LED_PIN, OUTPUT);
  digitalWrite(BATTERY_MONITORING_LED_PIN, HIGH);

  inactiveTime = micros();
}

//*****************************************RTOS Task******************************************//

void xTaskSystemMonitoring(void *pvParameters)
{
  while (true)
  {
    waitForSystemOnUtil();

    // Battery monitoring
    int analogVoltage = analogRead(BATTERY_VOLTAGE_PIN);
    // Serial.print("analogVoltage: ");
    // Serial.println(analogVoltage);
    const float voltage = mesureBatteryVoltageUtil(analogVoltage);
    // Serial.print("voltage: ");
    // Serial.println(voltage);
    int dutyCycle = map(voltage, MIN_BATTERY_VOLTAGE * 1.0, MAX_BATTERY_VOLTAGE * 1.0, 0.0, 255.0);
    dutyCycle = constrain(dutyCycle, 0, 255);
    // Serial.print("dutyCycle: ");
    // Serial.println(dutyCycle);

    if (!isWebSocketConnected || !isWIFIConnected)
    {
      blinkLEDUtil(BATTERY_MONITORING_LED_PIN, 3, 1000, 1000);
      blinkLEDUtil(BATTERY_MONITORING_LED_PIN, 1, 0, 2000);
      digitalWrite(MONITORING_LED_PIN, LOW);
    }
    else
    {
      // analogWrite(BATTERY_MONITORING_LED_PIN, dutyCycle); // TODO: uncomment this line
      digitalWrite(BATTERY_MONITORING_LED_PIN, LOW); // TODO: remove this line
    }

    // Recording monitoring
    if (isRecording)
    {
      blinkLEDUtil(MONITORING_LED_PIN, 3, 1000, 1000); // Blink 3 times every two seconds
      blinkLEDUtil(MONITORING_LED_PIN, 1, 0, 5000);    // Stay LOW for 5 seconds
      inactiveTime = micros();
    }
    else
    {
      if (isWebSocketConnected)
        digitalWrite(MONITORING_LED_PIN, HIGH);

      uint64_t elapsedTime = micros() - inactiveTime;

      if (elapsedTime >= 60000000UL)
      {
        Serial.println("Inactivity for more than 60 seconds!");
        systemOffUtil();
      }

      vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
  }
}

void xTaskWifiConnect(void *pvParameters)
{
  isWIFIConnected = false;
  bool reconnection = false;

  while (true)
  {
    waitForSystemOnUtil();

    // Check Wi-Fi connection state
    if (WiFi.status() != WL_CONNECTED)
    {
      isWIFIConnected = false;

      if (reconnection)
      {
        Serial.print("Wi-Fi Disconnected. Trying to reconnect to ");
      }
      else
      {
        Serial.print("Trying to connect to ");
      }

      Serial.println(ssid);
      WiFi.begin(ssid, password);
      int connectionAttempts = 0;

      while (WiFi.status() != WL_CONNECTED && connectionAttempts < 30)
      {
        vTaskDelay(500 / portTICK_PERIOD_MS);
        connectionAttempts++;
        Serial.print(".");
      }

      if (WiFi.status() == WL_CONNECTED)
      {
        Serial.println("\nWi-Fi Connected!");
        isWIFIConnected = true;
        reconnection = true;
      }
      else
      {
        if (reconnection)
        {
          Serial.print("\nFailed to reconnect to Wi-Fi. SSID: ");
        }
        else
        {
          Serial.print("\nFailed to connect to Wi-Fi. SSID: ");
        }
        Serial.println(ssid);

        // 30 tentative de connection infructueuse pendnat 15 secondes, entré en mode veille
      }
    }

    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
}

void xTaskWebSocketConnect(void *pvParameters)
{
  isWebSocketConnected = false;
  bool reconnection = false;

  while (true)
  {
    waitForSystemOnUtil();

    isWebSocketConnected = websocket.available();

    // Check WebSocket connection state
    if (!isWebSocketConnected && isWIFIConnected)
    {
      isWebSocketConnected = false;

      if (reconnection)
      {
        Serial.println("WebSocket Disconnected. Trying to reconnect to ");
      }
      else
      {
        Serial.print("Trying to connect to ");
      }
      Serial.print("ws://");
      Serial.print(webSocketServerAddress);
      Serial.print(":");
      Serial.print(webSocketServerPort);
      Serial.println(webSocketServerPath);

      websocket.onEvent(webSocketEventHandler);
      int connectionAttempts = 0;

      while (!websocket.connect(webSocketServerAddress, webSocketServerPort, webSocketServerPath) && connectionAttempts < 30)
      {
        vTaskDelay(500 / portTICK_PERIOD_MS);
        connectionAttempts++;
        Serial.print(".");
      }

      if (websocket.available())
      {
        Serial.println("WebSocket Connected!");
        isWebSocketConnected = true;
        reconnection = true;
      }
      else
      {
        if (reconnection)
        {
          Serial.print("Failed to reconnect to WebSocket server. Address: ");
        }
        else
        {
          Serial.print("Failed to connect to WebSocket server. Address: ");
        }
        Serial.print("ws://");
        Serial.print(webSocketServerAddress);
        Serial.print(":");
        Serial.print(webSocketServerPort);
        Serial.println(webSocketServerPath);
      }
    }

    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
}

void xTaskAudioCapture(void *pvParameters)
{
  while (true)
  {
    waitForSystemOnUtil();

    // Check if capture can begin
    if (!isReadyForRecording)
    {
      isRecording = false;
      suspendAudioTaskUtil();
    }

    // Using the current buffer for audio capture
    uint8_t *recBuffer = recBuffers[currentRecBuffer];
    uint32_t sampleSize = 0;

    // Start of capture
    esp_err_t result = esp_i2s::i2s_read(esp_i2s::I2S_NUM_0, recBuffer, BUFFER_SIZE, &sampleSize, 500 / portTICK_PERIOD_MS);

    if (result != ESP_OK || sampleSize == 0)
    {
      Serial.printf("ERROR: Record Failed!\n");
      isRecording = false;
    }
    else
    {
      Serial.printf("Record %d bytes\n", sampleSize);
      isRecording = true;

      // Volume increase
      increaseVolumeGain(recBuffer, sampleSize);

      if (isTaskInStateUtil(TaskHandle_xTaskTransmitAudio, eSuspended))
        vTaskResume(TaskHandle_xTaskTransmitAudio);

      readyRecBufferSampleSize = sampleSize;
      readyRecBuffer = currentRecBuffer; // Indicates that the buffer is ready

      // Change of current buffer
      currentRecBuffer = (currentRecBuffer + 1) % NUM_BUFFERS;
    }
  }
}

void xTaskTransmitAudio(void *pvParameters)
{
  while (true)
  {
    waitForSystemOnUtil();

    if (readyRecBuffer == -1)
      vTaskSuspend(TaskHandle_xTaskTransmitAudio);

    if (!isWIFIConnected)
    {
      Serial.printf("ERROR: Wi-Fi signal lost!\n");
    }
    else if (!isWebSocketConnected)
    {
      Serial.printf("ERROR: WebSocket disconnected!\n");
    }
    else if (readyRecBuffer != -1)
    {
      // Check if there is a ready buffer
      const int savedReadyRecBuffer = readyRecBuffer;
      uint8_t *pcmBuffer = recBuffers[readyRecBuffer];

      size_t linear16BufferSize = readyRecBufferSampleSize / 2;
      int16_t linear16Buffer[linear16BufferSize] = {0};

      pcmToLinear16Util(pcmBuffer, linear16Buffer, readyRecBufferSampleSize);

      // Data transmission via WebSocket
      transmitLinear16DataViaWebSocket(linear16Buffer, linear16BufferSize);
      // transmitLinear16DataViaWebSocketPerChunk(linear16Buffer, linear16BufferSize);

      // Reset the ready buffer
      memset(pcmBuffer, 0, BUFFER_SIZE);

      if (readyRecBuffer == savedReadyRecBuffer)
        readyRecBuffer = -1;
    }
  }
}

//*****************************************Event Handler******************************************//

void webSocketEventHandler(WebsocketsEvent event, String data)
{
  if (event == WebsocketsEvent::ConnectionOpened)
  {
    Serial.println("Connnection Opened");
    isWebSocketConnected = true;
  }
  else if (event == WebsocketsEvent::ConnectionClosed)
  {
    Serial.println("Connnection Closed");
    isWebSocketConnected = false;
  }
  else if (event == WebsocketsEvent::GotPing)
  {
    Serial.println("Got a Ping!");
  }
  else if (event == WebsocketsEvent::GotPong)
  {
    Serial.println("Got a Pong!");
  }
}

void controllButtonEventHandler(AceButton * /*button*/, uint8_t eventType, uint8_t buttonState)
{
  inactiveTime = micros();

  // Print out a message for all events.
  Serial.print(F("Control button: eventType: "));
  Serial.print(AceButton::eventName(eventType));
  Serial.print(F("; buttonState: "));
  Serial.println(buttonState);

  switch (eventType)
  {
  case AceButton::kEventClicked:
    controllButtonClickedEventHandler();
    break;
  case AceButton::kEventDoubleClicked:
    controllButtonDoubleClickedEventHandler();
    break;
  case AceButton::kEventRepeatPressed:
    controllButtonRepeatPressedEventHandler();
    break;
  }
}

void controllButtonClickedEventHandler(void)
{
  Serial.println("Controll Button Clicked!");
}

void controllButtonDoubleClickedEventHandler(void)
{
  Serial.println("Controll Button Double Clicked!");

  if (isSystemON)
  {
    // if (isTaskInStateUtil(TaskHandle_xTaskAudioCapture, eSuspended) || isTaskInStateUtil(TaskHandle_xTaskTransmitAudio, eSuspended))
    if (!isReadyForRecording || !isRecording)
    {
      Serial.println("Resume audio task. Recording ON.");
      isReadyForRecording = true;
      isRecording = true;
      resumeAudioTaskUtil();
    }
    else
    {
      Serial.println("Suspend audio task. Recording OFF.");
      isReadyForRecording = false;
      isRecording = false;
      vTaskSuspend(TaskHandle_xTaskAudioCapture);
    }
  }
}

void controllButtonRepeatPressedEventHandler(void)
{
  Serial.println("Controll Button Held Down!");

  if (isSystemON)
  {
    systemOffUtil();
  }
  else
  {
    systemOnUtil();
  }
}

void controllButtonPressedRawEventHandler(void)
{
  // Delay to check if the button was pressed during boot
  delay(2500);
  bool buttonPressedOnBooting = controllButton.isPressedRaw();

  // Check if the button was pressed during boot
  if (buttonPressedOnBooting && !isSystemON)
  {
    Serial.println("Button pressed on booting");
    systemOnUtil();
  }
  else
  {
    Serial.println("Bad wake up!");
    systemOffUtil(500);
  }
}

//*****************************************Audio Process******************************************//

void increaseVolumeGain(uint8_t *recBuffer, uint32_t sampleSize)
{
  for (uint32_t i = 0; i < sampleSize; i += BITS_PER_SAMPLE / 8)
  {
    (*(uint16_t *)(recBuffer + i)) <<= VOLUME_GAIN;
  }
}

// void transmitDataViaWebSocket(uint8_t *data, uint32_t size)
// {
//   // Avoid sending large amounts of data all at once
//   int chunkSize = 1024;
//
//   for (int i = 0; i < size; i += chunkSize)
//   {
//     int remaining = size - i;
//     int thisChunkSize = min(chunkSize, remaining);
//     // Convert data to a const char pointer to send as binary
//     const char *dataChar = reinterpret_cast<const char *>(data + i);
//     // Transmit this chunk of data as binary
//     websocket.sendBinary(dataChar, thisChunkSize);
//   }
// }

void transmitLinear16DataViaWebSocket(const int16_t *data, size_t size)
{
  const char *dataChar = reinterpret_cast<const char *>(data);

  websocket.sendBinary(dataChar, size * sizeof(int16_t));
}

void transmitLinear16DataViaWebSocketPerChunk(const int16_t *data, size_t size, const int chunkSize)
{
  for (size_t i = 0; i < size; i += chunkSize)
  {
    size_t remaining = size - i;
    size_t thisChunkSize = (remaining > chunkSize) ? chunkSize : remaining;

    transmitLinear16DataViaWebSocket(&data[i], thisChunkSize);
  }
}

//*****************************************Utils******************************************//

bool isTaskInStateUtil(TaskHandle_t task, eTaskState stateToCheck)
{
  eTaskState taskState = eTaskGetState(task);

  return (taskState == stateToCheck);
}

void systemOffUtil(int offDelay)
{
  Serial.println("System OFF");
  isSystemON = false;
  isReadyForRecording = false;
  isRecording = false;
  digitalWrite(MONITORING_LED_PIN, LOW);
  digitalWrite(BATTERY_MONITORING_LED_PIN, HIGH);
  // delay to allow the system not to capture the release of the button
  delay(offDelay);
  // Enter deep sleep mode to save power
  // esp_deep_sleep_start();
  // Serial.println("Never printed!");
}

void systemOnUtil(void)
{
  Serial.println("System ON");
  isSystemON = true;
  digitalWrite(BATTERY_MONITORING_LED_PIN, LOW); // TODO: remove this line
  // delay to allow the system not to capture the release of the button
  delay(ON_DELAY);
}

void waitForSystemOnUtil(void)
{
  while (!isSystemON)
  {
    Serial.println("System OFF");
    delay(1000);
  }
}

void printWakeupReasonUtil(void)
{
  esp_sleep_wakeup_cause_t wakeup_reason;

  // Get the wakeup reason
  wakeup_reason = esp_sleep_get_wakeup_cause();

  // Print the wakeup reason
  switch (wakeup_reason)
  {
  case ESP_SLEEP_WAKEUP_EXT0:
    Serial.println("Wakeup caused by an external signal using RTC_IO");
    break;
  case ESP_SLEEP_WAKEUP_EXT1:
    Serial.println("Wakeup caused by an external signal using RTC_CNTL");
    break;
  case ESP_SLEEP_WAKEUP_TIMER:
    Serial.println("Wakeup caused by a timer");
    break;
  case ESP_SLEEP_WAKEUP_TOUCHPAD:
    Serial.println("Wakeup caused by a touchpad");
    break;
  case ESP_SLEEP_WAKEUP_ULP:
    Serial.println("Wakeup caused by a ULP program");
    break;
  default:
    Serial.printf("Wakeup was not caused by deep sleep: %d\n", wakeup_reason);
    break;
  }
}

void blinkLEDUtil(uint8_t LED_PIN, uint8_t times, TickType_t onDuration, TickType_t offDuration)
{
  for (int i = 0; i < times; i++)
  {
    if (onDuration > 0)
    {
      digitalWrite(LED_PIN, HIGH);
      vTaskDelay(onDuration / portTICK_PERIOD_MS);
    }

    if (offDuration > 0)
    {
      digitalWrite(LED_PIN, LOW);
      vTaskDelay(offDuration / portTICK_PERIOD_MS);
    }
  }
}

float mesureBatteryVoltageUtil(int analogVoltage, float referenceVoltage, float referenceVoltageInAnalogValue)
{
  float voltage = ((float)analogVoltage * referenceVoltage) / referenceVoltageInAnalogValue;
  return voltage;
}

int mesureBatteryPercentageUtil(float voltage, float minVoltage, float maxVoltage)
{
  int batteryPercentage = map(voltage, minVoltage, maxVoltage, 0, 100);
  return batteryPercentage;
}

bool isBufferEmptyUtil(const uint8_t *buffer, size_t bufferSize, uint8_t emptyValue)
{
  for (size_t i = 0; i < bufferSize; ++i)
  {
    if (buffer[i] != emptyValue)
    {
      return false;
    }
  }
  return true;
}

void suspendAudioTaskUtil()
{
  vTaskSuspend(TaskHandle_xTaskAudioCapture);
  vTaskSuspend(TaskHandle_xTaskTransmitAudio);
}

void resumeAudioTaskUtil()
{
  vTaskResume(TaskHandle_xTaskAudioCapture);
  vTaskResume(TaskHandle_xTaskTransmitAudio);
}

void pcmToLinear16Util(const uint8_t *pcmBuffer, int16_t *linear16Buffer, size_t pcmBufferSize)
{
  for (int i = 0, j = 0; i < pcmBufferSize; i += 2, ++j)
  {
    linear16Buffer[j] = (pcmBuffer[i + 1] << 8) | pcmBuffer[i];
  }
}
