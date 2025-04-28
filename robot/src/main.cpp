#include <Arduino.h>
#include <ArduinoOTA.h>

#include "position_ctrl.h"
#include "wheels.h"
#include "wireless.h"

void setup() {
  Serial.begin(9600);
  delay(1000);

  pinMode(LED_BUILTIN, OUTPUT);
  setup_wifi();

  init_position_ctrl();
  set_desired_position({0,0,0});
}

void loop() {
  ArduinoOTA.handle();
  udp_receive(); 

  update_position_ctrl();
}

