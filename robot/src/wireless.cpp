#include <ArduinoOTA.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoMDNS.h>
#include <ArduinoJson.h>

#include "wireless.h"
#include "position_ctrl.h"

bool wifi_connected = false;

WiFiUDP Udp;
MDNS mdns(Udp);

bool setup_wifi(){
    wifi_connected = wifi_connect();
    if(wifi_connected){
        digitalWrite(LED_BUILTIN, HIGH);
        setup_ota();
        mdns.begin(WiFi.localIP(), hostname);
        Udp.begin(UDP_PORT);
    }
    return wifi_connected;
}

bool wifi_connect(){
  Serial.println("-----");

  WiFi.mode(WIFI_STA);
  WiFi.setHostname(hostname);

  WiFi.begin(ssid, pwd);
  int i = 0;
  while (WiFi.waitForConnectResult() != WL_CONNECTED) {
    WiFi.begin(ssid, pwd);
    Serial.println("Retrying connection...");
    Serial.print(i&1);

    if(i++ >= 5){
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

bool is_wifi_connected(){
    return wifi_connected;
}


char packetBuffer[255];
void udp_receive(){
  // receive robot position, target setpoints from Wifi (UDP)
  // Formatted in JSON, dictionary with keys "robot", "target"
  // Each value is a 3x1 array of floats, in order X,Y,Theta of the point
  int packetSize = Udp.parsePacket();
  if(packetSize){
    int len = Udp.read(packetBuffer, 255);
    if(len > 0) packetBuffer[len] = '\0';
    Serial.println(packetBuffer);

    //JSON parsing
    JsonDocument doc;       // Create a JSON document
    DeserializationError error = deserializeJson(doc, packetBuffer);

    if (error) {
      Serial.print(F("deserializeJson() failed: "));
      Serial.println(error.c_str());
      return;
    }
    
    if(doc["robot"]){
      // Extract the JSON objects
      double robot_x = doc["robot"]["x"];
      double robot_y = doc["robot"]["y"];
      double robot_theta = doc["robot"]["theta"];

      // Serial.println(robot_x);
      // Serial.println(robot_y);
      // Serial.println(robot_theta);     
      set_robot_position({robot_x, robot_y, robot_theta, micros()});
    }
  
    if(doc["target"]){
      double target_x = doc["target"]["x"];
      double target_y = doc["target"]["y"];
      double target_theta = doc["target"]["theta"];
      
      Serial.println(target_x);
      Serial.println(target_y);
      Serial.println(target_theta);
      set_desired_position({target_x, target_y, target_theta});      
    //   udp_send_debug_string("Message", packetBuffer, false);
    }
  }
}


void udp_send_string(const char ip[], int port, const char msg[]){
    Udp.beginPacket(ip, port);
    Udp.write(msg);
    Udp.endPacket();
}

void udp_send_string(const char ip[], int port, String msg){
    int l = msg.length() + 1;
    char arr[l];
    msg.toCharArray(arr, l);
    udp_send_string(ip, port, arr);
}

void udp_send_debug_string(String name, String value, bool plot){
    String msg = name + ":" + value + "|" + plot ? "g" : "";
    udp_send_string(DEBUG_IP, DEBUG_PORT, msg);
}

void udp_send_debug_string(String name, String timestamp, String value, bool plot){
    String msg = name + ":" + timestamp + ":" + value + "|" + (plot ? "g" : "");
    Serial.println(msg);
    udp_send_string(DEBUG_IP, DEBUG_PORT, msg);
}