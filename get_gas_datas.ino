#include <M5Display.h>
#include <M5StickCPlus.h>
#include "bme68xLibrary.h"

#define NEW_GAS_MEAS (BME68X_GASM_VALID_MSK | BME68X_HEAT_STAB_MSK | BME68X_NEW_DATA_MSK)
#define MEAS_DUR 250

#define SDA_PIN 0
#define SCL_PIN 26

#define BME688_I2C_ADDR 0x76

#include <math.h>
Bme68x bme;

void setup(void)
{
  M5.begin();
  M5.Lcd.setRotation(1);
  M5.Lcd.setTextFont(4);
  M5.Lcd.fillScreen(BLACK);
  delay(50);
    
  Serial.begin(19200);
  Wire.begin(SDA_PIN, SCL_PIN);

  while (!Serial)
  {
    delay(10);
  }

  bme.begin(BME688_I2C_ADDR, Wire);

  if(bme.checkStatus())
  {
    if (bme.checkStatus() == BME68X_ERROR)
    {
      Serial.println("Sensor error:" + bme.statusString());
      return;
    }
    else if (bme.checkStatus() == BME68X_WARNING)
    {
      Serial.println("Sensor Warning:" + bme.statusString());
    }
  }
  
  bme.setTPH();

  int feature_length = 6;
  uint16_t tempProf[feature_length] = { 200, 300, 400, 200, 300, 400};
  uint16_t mulProf[feature_length] = { 3, 3, 3, 3, 3, 3};
  uint16_t sharedHeatrDur = MEAS_DUR - (bme.getMeasDur(BME68X_PARALLEL_MODE) / 1000);

  bme.setHeaterProf(tempProf, mulProf, sharedHeatrDur, feature_length);
  bme.setOpMode(BME68X_PARALLEL_MODE);
}

float last = 0;

void loop(void)
{
  bme68xData data;
  uint8_t nFieldsLeft = 0;
  
  delay(MEAS_DUR);

  if (bme.fetchData())
  {
    do
    {
      nFieldsLeft = bme.getData(data);
      if (data.status == NEW_GAS_MEAS)
      { 
        M5.Lcd.setCursor(0, 0);
        M5.Lcd.setTextColor(WHITE, BLACK);
        M5.Lcd.printf("Gas Index: %d\n", data.gas_index);
        M5.Lcd.printf("Temperature: %.2f\n", data.temperature);
        M5.Lcd.printf("Humidity: %.2f\n", data.humidity);
        M5.Lcd.printf("Gas Resistance: %.2f\n", log(data.gas_resistance));
        
        Serial.print(String(data.gas_index)+",");
        Serial.print(String(millis()) + ",");
        Serial.print(String(data.temperature) + ","); 
        Serial.print(String(data.humidity) + ",");
        float current = log(data.gas_resistance);
        Serial.print(String(current,3)+",");
        Serial.println();
        last = current;
        delay(20);
      }
    } while (nFieldsLeft);
  }
}
