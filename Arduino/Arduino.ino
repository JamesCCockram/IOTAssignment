#include <Adafruit_Sensor.h> //Temp/Humidity Sensor
#include <DHT.h> //Temp/Humidity Sensor
#include <DHT_U.h> //Temp/Humidity Sensor
#include <Wire.h>
#include <U8glib.h> //OLED screen Library
#include <ArduinoJson.h>

//Define Temp/Humid Sensor
#define DHTPIN 8
#define DHTTYPE DHT11
DHT_Unified dht(DHTPIN, DHTTYPE);

//Set Fan Pin
const int fanPin = 2;

//Setup OLED screen
U8GLIB_SH1106_128X64 u8g(13, 11, 10, 9); // SCK = 13, MOSI = 11, CS = 10, A0 = 9

//Initialize JSON Variable
StaticJsonDocument<200> aqData;
StaticJsonDocument<200> fanData;

//Initialize Sensor Variables
float temp;
int humid;
float fanTriggerValue = 21.0;
bool fanOn = false;
String command;

void setup() {
  // put your setup code here, to run once:
  Wire.begin();

  Serial.begin(9600);
  pinMode(fanPin, OUTPUT); //Fan Pin
  dht.begin();

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

void loop() {
  //Ensure that the sensors are ready
  sensors_event_t event;
  dht.temperature().getEvent(&event);
  temp = event.temperature;
  dht.humidity().getEvent(&event);
  humid = event.relative_humidity;

  //Format into JSON
  aqData["temp"] = temp;
  aqData["humid"] = humid;
  fanData["fanTriggerValue"] = fanTriggerValue;
  fanData["fanOn"] = fanOn;

  //Send to Serial
  if(Serial.available() > 0)
  {
    command = Serial.readStringUntil('\n');
    if(command.equals("getData"))
    {
      serializeJson(aqData, Serial);
      Serial.println("");
    }
    else if(command.equals("changeFan"))
    {
      Serial.println("Enter new temperature to activate fan");
      //Wait for a response
      while(!Serial.available())
      {}
      int input = Serial.parseInt();
      //Ensure that the input is valid
      if(input > 0)
      {
        fanTriggerValue = input;
      }
    }
    else if(command.equals("fanDetails"))
    {
      serializeJson(fanData, Serial);
      Serial.println("");
    }
    else if(command.equals("disableFan"))
    {
      fanOn = false;
      Serial.println("Fan Disabled");
    }
    else if(command.equals("enableFan"))
    {
      fanOn = true;
      Serial.println("Fan Enabled");
    }
  }

  if(temp > fanTriggerValue && fanOn == true)
  {
      digitalWrite(fanPin, HIGH); 
  }

  else
  {
      digitalWrite(fanPin, LOW); 
  }
  
  //Update Screen
  draw_temp(temp, humid);
}
