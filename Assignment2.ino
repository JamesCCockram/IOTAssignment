#include <CCS811.h> //Air Quality Sensor
#include <Wire.h>
#include <U8glib.h> //OLED screen Library
#include <ArduinoJson.h>

CCS811 AQsensor;

//Setup OLED screen
U8GLIB_SH1106_128X64 u8g(13, 11, 10, 9); // SCK = 13, MOSI = 11, CS = 10, A0 = 9

//Initialize JSON Variable
StaticJsonDocument<200> aqData;
StaticJsonDocument<200> buzzerData;

//Initialize Sensor Variables
int co2, tvoc;
int mode = 0;
int buzzerTriggerValue = 500;
bool buzzer = false;
String command;

void setup() {
  // put your setup code here, to run once:
  Wire.begin();
  Serial.begin(9600);
  pinMode(2, OUTPUT); //Buzzer Pin
  

  while(AQsensor.begin() != 0)
  {
    Serial.println("failed to init chip, please check if the chip connection is fine");
    delay(1000);
  }
  //SPL_init();
  AQsensor.setMeasCycle(AQsensor.eCycle_250ms);

  //OLED SCREEN SETUP
  u8g.setRot180(); //Rotate the screen so it looks right
  // assign default color value
  if ( u8g.getMode() == U8G_MODE_R3G3B2 ) {
  u8g.setColorIndex(255); // white
  }
  else if ( u8g.getMode() == U8G_MODE_GRAY2BIT ) {
  u8g.setColorIndex(3); // max intensity
  }
  else if ( u8g.getMode() == U8G_MODE_BW ) {
  u8g.setColorIndex(1); // pixel on
  }
  else if ( u8g.getMode() == U8G_MODE_HICOLOR ) {
  u8g.setHiColorByRGB(255,255,255);
  }
}

void draw_temp(float temp, int humid)
{
  u8g.firstPage();
  do
  {
    u8g.setFont(u8g_font_unifont);
    u8g.drawStr(0, 20, "Temp:");
    //u8g.drawStr(50, 20, get_temp_c());
    u8g.setPrintPos(75, 20);
    u8g.print(temp);
    u8g.setPrintPos(115, 20);
    u8g.print("C");
    u8g.drawStr(0, 50, "Humidity:");
    u8g.setPrintPos(75, 50);
    u8g.print(humid);
    u8g.setPrintPos(115, 50);
    u8g.print("%");
  }
  while(u8g.nextPage());
}

void draw_aq(int co2, int tvoc)
{
  u8g.firstPage();
  do
  {
    u8g.setFont(u8g_font_unifont);
    u8g.drawStr(0, 20, "Co2:");
    u8g.setPrintPos(50, 20);
    u8g.print(co2);
    u8g.setPrintPos(90, 20);
    u8g.print("ppm");
    u8g.drawStr(0, 50, "TVOC:");
    u8g.setPrintPos(50, 50);
    u8g.print(tvoc);
    u8g.setPrintPos(90, 50);
    u8g.print("ppb");
  }
  while(u8g.nextPage());
}

void draw_pressure(float pressure)
{
  u8g.firstPage();
  do
  {
    u8g.setFont(u8g_font_unifont);
    u8g.drawStr(0, 20, "Pressure:");
    u8g.setPrintPos(0, 35);
    u8g.print(pressure);
    u8g.setPrintPos(60, 35);
    u8g.print("mb");
  }
  while(u8g.nextPage());
}

void loop() {
  //Ensure that the sensors are ready
  if(AQsensor.checkDataReady() == true)
  {
    co2 = AQsensor.getCO2PPM();
    tvoc = AQsensor.getTVOCPPB();
  }

  //Ensure Screen loops back to first page
  if (mode > 2)
  {
    mode = 0;
  }


  //Format into JSON
  aqData["co2"] = co2;
  aqData["tvoc"] = tvoc;
  buzzerData["buzzerTriggerValue"] = buzzerTriggerValue;
  buzzerData["buzzerEnabled"] = buzzer;

  //Send to Serial
  if(Serial.available() > 0)
  {
    command = Serial.readStringUntil('\n');
    if(command.equals("getData"))
    {
      serializeJson(aqData, Serial);
      Serial.println("");
    }
    else if(command.equals("changeBuzzer"))
    {
      Serial.println("Enter CO2 Buzzer Variable");
      //Wait for a response
      while(!Serial.available())
      {}
      int input = Serial.parseInt();
      //Ensure that the input is valid
      if(input > 0)
      {
        buzzerTriggerValue = input;
      }
    }
    else if(command.equals("buzzerDetails"))
    {
      serializeJson(buzzerData, Serial);
      Serial.println("");
    }
    else if(command.equals("disableBuzzer"))
    {
      buzzer = false;
      Serial.println("Buzzer Disabled");
    }
    else if(command.equals("enableBuzzer"))
    {
      buzzer = true;
      Serial.println("Buzzer Enabled");
    }
  }

  if(co2 > buzzerTriggerValue && buzzer == true)
  {
      digitalWrite(2,HIGH); 
      delay(100);
      digitalWrite(2, LOW);
  }
  
  //Update Screen
  draw_aq(co2, tvoc);
}
