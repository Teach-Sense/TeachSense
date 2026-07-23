/*
  INMP441 <-> ESP32 I2S Microphone Interface
  Arduino IDE, ESP32 core (legacy driver/i2s.h)

  Wiring:
    INMP441 VDD  -> ESP32 3.3V
    INMP441 GND  -> ESP32 GND
    INMP441 L/R  -> ESP32 GND   (selects left channel slot)
    INMP441 SD   -> ESP32 GPIO32
    INMP441 WS   -> ESP32 GPIO25
    INMP441 SCK  -> ESP32 GPIO26
*/

/////INCLUDES///
#include <driver/i2s.h>   //gives us all the i2s_ functions and types, comes bundled with the esp32 core


////DEFINES
#define I2S_WS_PIN   25   //Word Select pin (L/R clock)
#define I2S_SCK_PIN  26   //Bit clock pin
#define I2S_SD_PIN   32   //Serial data pin, mic output comes in here

#define I2S_PORT     I2S_NUM_0   //esp32 has 2 i2s peripherals, we're using the first one

#define SAMPLE_RATE     16000                       //16khz, standard for speech
#define SAMPLE_BITS     I2S_BITS_PER_SAMPLE_32BIT    //inmp441 sends 24 bit data padded into a 32 bit frame
#define READ_BUF_LEN    512                          //how many samples we pull per i2s_read() call


/////GLOBAL BUFFER
int32_t rawBuffer[READ_BUF_LEN];   //holds one block of raw samples straight from the mic


/////FUNCTION PROTOTYPES
void setupI2SMic();


///SETUP
void setup() {
  Serial.begin(115200);
  delay(500);   //give serial monitor time to connect before we print anything

  Serial.println("Initializing INMP441 I2S mic...");
  setupI2SMic();   //installs the driver and wires it to our pins
  Serial.println("I2S mic ready.");
}

void loop() {
  // put your main code here, to run repeatedly: reads one block of audio and prints its loudness

  size_t bytesRead = 0;

  esp_err_t result = i2s_read(I2S_PORT, (void*)rawBuffer, READ_BUF_LEN * sizeof(int32_t), &bytesRead, portMAX_DELAY);
  //blocks here (portMAX_DELAY = no timeout) until a full buffer's worth of samples is ready

  if (result == ESP_OK && bytesRead > 0)   //only process if the read actually worked and gave us data
  {
    int samplesRead = bytesRead / sizeof(int32_t);   //convert byte count back into a sample count

    int64_t sumSquares = 0;   //64 bit so it can't overflow across hundreds of squared samples

    for (int i = 0; i < samplesRead; i++)
    {
      // inmp441 gives 24 bit signed data left-justified in the 32 bit word
      // shifting right by 8 drops the empty low bits and gives us a usable signed value
      int32_t sample = rawBuffer[i] >> 8;
      sumSquares += (int64_t)sample * (int64_t)sample;
    }

    double meanSquare = (double)sumSquares / samplesRead;
    double rms = sqrt(meanSquare);   //rough loudness indicator for this block

    Serial.print("RMS: ");
    Serial.println(rms);
  }
}


///////////FUNCTIONS////////////////////////////////

void setupI2SMic()  // This function configures and starts the i2s driver, then wires it to our pins
{
  i2s_config_t i2sConfig = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),   //makes the esp32 the master and makes it receive signals from the inmp
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = SAMPLE_BITS,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,   //L/R pin tied to GND = left channel
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,   //interrupt priority level for the dma-complete interrupt
    .dma_buf_count = 8,    //number of dma buffers in the ring, more = more cushion against timing hiccups
    .dma_buf_len = READ_BUF_LEN,   //samples per dma buffer, tied to our read chunk size
    .use_apll = false,   //not needed at this sample rate
    .tx_desc_auto_clear = false,   //irrelevant here, we're rx only
    .fixed_mclk = 0
  };

  i2s_pin_config_t pinConfig = {
    .bck_io_num = I2S_SCK_PIN,
    .ws_io_num = I2S_WS_PIN,
    .data_out_num = I2S_PIN_NO_CHANGE,   //no output pin, we're only listening
    .data_in_num = I2S_SD_PIN
  };

  esp_err_t err;   //every esp-idf driver call reports back through this type

  err = i2s_driver_install(I2S_PORT, &i2sConfig, 0, NULL);   //0 = no event queue, NULL = don't need a queue handle
  if (err != ESP_OK)
  {
    Serial.printf("I2S driver install failed: %d\n", err);
    return;
  }

  err = i2s_set_pin(I2S_PORT, &pinConfig);   //applies our pin mapping to the driver we just installed
  if (err != ESP_OK)
  {
    Serial.printf("I2S set pin failed: %d\n", err);
    return;
  }

  i2s_zero_dma_buffer(I2S_PORT);   //clears out any garbage sitting in the dma buffers before our first real read
}
