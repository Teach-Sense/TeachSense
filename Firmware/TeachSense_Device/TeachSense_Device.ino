/*
  TeachSense ESP32 Classroom Device Firmware

  Hardware:
    - ESP32 DevKit
    - INMP441 I2S microphone (WS GPIO25, SCK GPIO26, SD GPIO32)
    - MAX98357A I2S DAC (BCLK GPIO26, LRC GPIO25, DIN GPIO22)

  Required Libraries (install via Arduino Library Manager or PlatformIO):
    - WebSockets by Markus Sattler
    - ArduinoJson by Benoit Blanchon
    - HTTPClient (built-in ESP32 core)

  State Machine:
    DISCONNECTED -> WIFI_CONNECTING -> WIFI_CONNECTED ->
    DEVICE_REGISTERED -> WS_CONNECTED -> IDLE ->
    RECORDING -> SPEAKING -> LISTENING
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <driver/i2s.h>

// WiFi configuration
const char *SSID = "YOUR_WIFI_SSID";
const char *PASSWORD = "YOUR_WIFI_PASSWORD";

// Device configuration (replace with provisioned values or use register endpoint)
const char *DEVICE_NAME = "Lecture Hall Mic";
const char *DEVICE_TYPE = "audio_input";
const char *DEVICE_KEY = "device_secret_123";
const char *API_BASE = "https://teachsense.up.railway.app";

// I2S microphone pins
#define I2S_WS_PIN 25
#define I2S_SCK_PIN 26
#define I2S_SD_PIN 32
#define I2S_PORT I2S_NUM_0

// I2S DAC pins
#define I2S_BCLK_PIN 26
#define I2S_LRC_PIN 25
#define I2S_DIN_PIN 22

#define SAMPLE_RATE 16000
#define READ_BUF_LEN 512

WebSocketsClient webSocket;
HTTPClient http;

String device_token;
String device_id;
int current_session_id = 0;
int current_question_id = 0;
bool is_recording = false;
bool is_listening = false;
bool is_speaking = false;

enum DeviceState {
  STATE_DISCONNECTED,
  STATE_WIFI_CONNECTING,
  STATE_WIFI_CONNECTED,
  STATE_DEVICE_REGISTERED,
  STATE_WS_CONNECTED,
  STATE_IDLE,
  STATE_RECORDING,
  STATE_SPEAKING,
  STATE_LISTENING
};

DeviceState current_state = STATE_DISCONNECTED;
unsigned long last_heartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL = 30000;
unsigned long listen_timeout = 0;
const unsigned long LISTEN_DURATION = 30000;

void setup() {
  Serial.begin(115200);
  delay(500);
  setupI2SMic();
  setupI2SDac();
  current_state = STATE_WIFI_CONNECTING;
  connectWiFi();
}

void loop() {
  webSocket.loop();
  if (WiFi.status() != WL_CONNECTED && current_state != STATE_WIFI_CONNECTING) {
    current_state = STATE_WIFI_CONNECTING;
    connectWiFi();
  }
  handleState();
  sendHeartbeatIfNeeded();
}

void connectWiFi() {
  WiFi.begin(SSID, PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi connected");
    current_state = STATE_WIFI_CONNECTED;
    registerDevice();
  }
}

void registerDevice() {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  http.begin(String(API_BASE) + "/api/devices/register/");
  http.addHeader("Content-Type", "application/json");
  String body = "{\"name\":\"" + String(DEVICE_NAME) + "\",\"type\":\"" + String(DEVICE_TYPE) + "\",\"device_key\":\"" + String(DEVICE_KEY) + "\"}";
  int code = http.POST(body);
  if (code == 201) {
    String payload = http.getString();
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, payload);
    device_token = doc["device_token"].as<String>();
    device_id = doc["device_id"].as<String>();
    Serial.println("Device registered: " + device_id);
    current_state = STATE_DEVICE_REGISTERED;
    connectWebSocket();
  } else {
    Serial.println("Device registration failed: " + String(code));
  }
  http.end();
}

void connectWebSocket() {
  String url = String(API_BASE) + "/ws/devices/" + device_id + "/?token=" + device_token;
  webSocket.beginSSL(API_BASE, 443, "/ws/devices/" + device_id + "/?token=" + device_token);
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);
  webSocket.enableHeartbeat(15000, 3000, 2);
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      Serial.println("WebSocket connected");
      current_state = STATE_WS_CONNECTED;
      sendHandshake();
      break;
    case WStype_DISCONNECTED:
      Serial.println("WebSocket disconnected");
      current_state = STATE_IDLE;
      break;
    case WStype_TEXT:
      handleWebSocketMessage(String((char *)payload));
      break;
    case WStype_ERROR:
      Serial.println("WebSocket error");
      break;
    default:
      break;
  }
}

void handleWebSocketMessage(String message) {
  DynamicJsonDocument doc(2048);
  deserializeJson(doc, message);
  const char *msg_type = doc["type"];
  if (strcmp(msg_type, "handshake_response") == 0) {
    Serial.println("Handshake accepted");
    sendRegisterSession();
  } else if (strcmp(msg_type, "session_confirmed") == 0) {
    current_session_id = doc["session_id"];
    Serial.println("Session confirmed: " + String(current_session_id));
    current_state = STATE_IDLE;
  } else if (strcmp(msg_type, "start_recording") == 0) {
    current_session_id = doc["parameters"]["session_id"];
    current_state = STATE_RECORDING;
    is_recording = true;
    sendAck("start_recording", "executed");
  } else if (strcmp(msg_type, "stop_recording") == 0) {
    is_recording = false;
    current_state = STATE_IDLE;
    sendAck("stop_recording", "executed");
  } else if (strcmp(msg_type, "new_question") == 0) {
    current_question_id = doc["question_id"];
    const char *text = doc["text"];
    const char *voice = doc["voice"] | "natural_female";
    float speed = doc["speed"] | 1.0;
    speakText(text, voice, speed);
    current_state = STATE_SPEAKING;
    sendAck("new_question", "speaking");
  } else if (strcmp(msg_type, "listen_for_answers") == 0) {
    current_session_id = doc["parameters"]["session_id"];
    current_question_id = doc["parameters"]["question_id"];
    unsigned long duration = doc["parameters"]["duration_seconds"] | 30;
    current_state = STATE_LISTENING;
    is_listening = true;
    listen_timeout = millis() + (duration * 1000);
    sendAck("listen_for_answers", "listening");
  }
}

void sendHandshake() {
  String msg = "{\"type\":\"handshake\",\"device_id\":\"" + device_id + "\",\"device_type\":\"" + String(DEVICE_TYPE) + "\",\"protocol_version\":\"1.0\",\"timestamp\":\"" + getTimestamp() + "\"}";
  webSocket.sendTXT(msg);
}

void sendRegisterSession() {
  String msg = "{\"type\":\"register_session\",\"session_id\":1}";
  webSocket.sendTXT(msg);
}

void sendAck(const char *command, const char *status) {
  String msg = "{\"type\":\"command_result\",\"command\":\"" + String(command) + "\",\"status\":\"" + String(status) + "\",\"timestamp\":\"" + getTimestamp() + "\"}";
  webSocket.sendTXT(msg);
}

void sendHeartbeatIfNeeded() {
  if (millis() - last_heartbeat > HEARTBEAT_INTERVAL) {
    last_heartbeat = millis();
    String msg = "{\"type\":\"device_status\",\"status\":\"active\",\"cpu_usage\":0,\"memory_usage\":0,\"timestamp\":\"" + getTimestamp() + "\"}";
    webSocket.sendTXT(msg);
  }
}

void handleState() {
  if (current_state == STATE_RECORDING || current_state == STATE_LISTENING) {
    streamAudioFrame();
  }
  if (current_state == STATE_LISTENING && millis() > listen_timeout) {
    is_listening = false;
    current_state = STATE_IDLE;
    sendAck("listen_for_answers", "stopped");
  }
}

void streamAudioFrame() {
  if (!is_recording && !is_listening) return;
  size_t bytesRead = 0;
  int32_t rawBuffer[READ_BUF_LEN];
  esp_err_t result = i2s_read(I2S_PORT, (void *)rawBuffer, READ_BUF_LEN * sizeof(int32_t), &bytesRead, portMAX_DELAY);
  if (result == ESP_OK && bytesRead > 0) {
    int samplesRead = bytesRead / sizeof(int32_t);
    for (int i = 0; i < samplesRead; i++) {
      rawBuffer[i] = rawBuffer[i] >> 8;
    }
    String base64 = base64Encode((uint8_t *)rawBuffer, samplesRead * sizeof(int16_t));
    String msg = "{\"type\":\"audio_frame\",\"session_id\":" + String(current_session_id) + ",\"question_id\":" + String(current_question_id) + ",\"frame_number\":" + String(samplesRead) + ",\"timestamp\":\"" + getTimestamp() + "\",\"sample_rate\":16000,\"channels\":1,\"bit_depth\":16,\"data_base64\":\"" + base64 + "\"}";
    webSocket.sendTXT(msg);
  }
}

void speakText(const char *text, const char *voice, float speed) {
  if (WiFi.status() != WL_CONNECTED) return;
  String escaped = String(text);
  escaped.replace("\"", "\\\"");
  String body = "{\"text\":\"" + escaped + "\",\"language\":\"en-US\",\"voice\":\"" + String(voice) + "\",\"speed\":" + String(speed, 1) + ",\"output_device_id\":\"" + device_id + "\"}";
  http.begin(String(API_BASE) + "/api/devices/" + device_id + "/speak/");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", "Bearer " + device_token);
  int code = http.POST(body);
  if (code == 200) {
    String payload = http.getString();
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, payload);
    const char *audio_url = doc["audio_url"];
    playAudioFromUrl(audio_url);
  }
  http.end();
}

void playAudioFromUrl(const char *url) {
  if (WiFi.status() != WL_CONNECTED) return;
  http.begin(url);
  int code = http.GET();
  if (code == 200) {
    WiFiClient *stream = http.getStreamPtr();
    size_t totalRead = 0;
    uint8_t buffer[1024];
    while (http.connected() && (totalRead < 64 * 1024)) {
      size_t available = stream->available();
      if (available) {
        int read = stream->readBytes(buffer, min((size_t)sizeof(buffer), available));
        if (read > 0) {
          i2s_write(I2S_PORT, buffer, read, NULL, portMAX_DELAY);
          totalRead += read;
        }
      }
      delay(1);
    }
  }
  http.end();
  is_speaking = false;
  if (current_state == STATE_SPEAKING) {
    current_state = STATE_IDLE;
  }
}

String getTimestamp() {
  struct timeval tv;
  gettimeofday(&tv, NULL);
  time_t now = tv.tv_sec;
  struct tm *tm_info = localtime(&now);
  char buf[25];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S", tm_info);
  return String(buf) + "Z";
}

String base64Encode(const uint8_t *data, size_t len) {
  const char *chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  String encoded = "";
  uint32_t triple = 0;
  int i = 0;
  while (i < len) {
    triple = (triple << 8) | data[i++];
    if (i % 3 == 0) {
      encoded += chars[(triple >> 18) & 0x3F];
      encoded += chars[(triple >> 12) & 0x3F];
      encoded += chars[(triple >> 6) & 0x3F];
      encoded += chars[triple & 0x3F];
    }
  }
  int remainder = len % 3;
  if (remainder > 0) {
    triple = triple << (6 - remainder * 8);
    encoded += chars[(triple >> 18) & 0x3F];
    encoded += chars[(triple >> 12) & 0x3F];
    encoded += (remainder == 1) ? "=" : chars[(triple >> 6) & 0x3F];
    encoded += "=";
  }
  return encoded;
}

void setupI2SMic() {
  i2s_config_t i2sConfig = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = READ_BUF_LEN,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };
  i2s_pin_config_t pinConfig = {
    .bck_io_num = I2S_SCK_PIN,
    .ws_io_num = I2S_WS_PIN,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD_PIN
  };
  i2s_driver_install(I2S_PORT, &i2sConfig, 0, NULL);
  i2s_set_pin(I2S_PORT, &pinConfig);
  i2s_zero_dma_buffer(I2S_PORT);
}

void setupI2SDac() {
  i2s_config_t i2sConfig = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = READ_BUF_LEN,
    .use_apll = false,
    .tx_desc_auto_clear = true,
    .fixed_mclk = 0
  };
  i2s_pin_config_t pinConfig = {
    .bck_io_num = I2S_BCLK_PIN,
    .ws_io_num = I2S_LRC_PIN,
    .data_out_num = I2S_DIN_PIN,
    .data_in_num = I2S_PIN_NO_CHANGE
  };
  i2s_driver_install(I2S_NUM_1, &i2sConfig, 0, NULL);
  i2s_set_pin(I2S_NUM_1, &pinConfig);
  i2s_zero_dma_buffer(I2S_NUM_1);
}
