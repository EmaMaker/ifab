#include <Arduino.h>
#include <ArduinoOTA.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoMDNS.h>

#include "motors.h"
#include "position_ctrl.h"
#include "wheels.h"

#define UDP_PORT 4242

const char* ssid = "Radiomarelli";
const char* password = "Magnadyn3Radiomarell1Philip5@";
bool wifi_connected = false;

void setup_ota();
bool setup_wifi();
void wifi_receive();

WiFiUDP udp;
MDNS mdns(udp);

void setup() {
  Serial.begin(9600);
  delay(1000);

  pinMode(LED_BUILTIN, OUTPUT);
  wifi_connected = setup_wifi();
  if(wifi_connected){
    digitalWrite(LED_BUILTIN, HIGH);
    setup_ota();
    mdns.begin(WiFi.localIP(), "ifab");
    udp.begin(4242);
  }

  init_position_ctrl();
  set_desired_position(0.66, 0.33);
}

void loop() {
  ArduinoOTA.handle();
  wifi_receive(); 
  update_position_ctrl();
}


char packetBuffer[255];
void wifi_receive(){
  // receive robot position, target setpoints from Wifi (UDP)
  // Formatted in JSON, dictionary with keys "setpoint", "target", "target2"
  // Each value is a 3x1 array of floats, in order X,Y,Theta of the point
  int packetSize = udp.parsePacket();
  if(packetSize){
    int len = udp.read(packetBuffer, 255);
    if(len > 0) packetBuffer[len] = '\0';
    Serial.println(packetBuffer);
  }
  
}

bool setup_wifi(){
  Serial.println("-----");

  WiFi.mode(WIFI_STA);
  WiFi.setHostname("ifab");

  WiFi.begin(ssid, password);
  int i = 0;
  while (WiFi.waitForConnectResult() != WL_CONNECTED) {
    WiFi.begin(ssid, password);
    Serial.println("Retrying connection...");
    Serial.print(i&1);

    if(i++ >= 2){
      digitalWrite(LED_BUILTIN, LOW);
      return false;
    }
  }
  Serial.print("Connected! IP: ");
  Serial.println(WiFi.localIP());
  digitalWrite(LED_BUILTIN, HIGH);
  return true;
}

void setup_ota(){
  ArduinoOTA.onStart([]() {
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH) {
      type = "sketch";
    } else {  // U_FS
      type = "filesystem";
    }

    // NOTE: if updating FS this would be the place to unmount FS using FS.end()
    Serial.println("Start updating " + type);
  });
  ArduinoOTA.onEnd([]() {
    Serial.println("\nEnd");
  });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) {
      Serial.println("Auth Failed");
    } else if (error == OTA_BEGIN_ERROR) {
      Serial.println("Begin Failed");
    } else if (error == OTA_CONNECT_ERROR) {
      Serial.println("Connect Failed");
    } else if (error == OTA_RECEIVE_ERROR) {
      Serial.println("Receive Failed");
    } else if (error == OTA_END_ERROR) {
      Serial.println("End Failed");
    }
  });

  ArduinoOTA.setHostname("ifab");
  ArduinoOTA.begin();
}