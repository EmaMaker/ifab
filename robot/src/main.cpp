#include <Arduino.h>
#include <ArduinoOTA.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoMDNS.h>

#include "motors.h"
#include "position_ctrl.h"
#include "wheels.h"

const char* ssid = "FMD";
const char* password = "Innovation_Phyrtual473";
bool wifi_connected = false;

void setup_ota();
bool setup_wifi();

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
  }

  init_position_ctrl();
  set_desired_position(0.66, 0.33);
}

void loop() {
  ArduinoOTA.handle();
  update_position_ctrl();
}

bool setup_wifi(){
  Serial.println("-----");

  WiFi.mode(WIFI_STA);
  WiFi.setHostname("aifab");

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