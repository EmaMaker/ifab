#include <Arduino.h>

#include "motors.h"
#include "position_ctrl.h"
#include "wheels.h"

void setup() {
  Serial.begin(115200);

  delay(2000);
  init_position_ctrl();

  // Just to signal it is working
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);
  set_desired_position(0.35, 0);
}

void loop() {
  update_position_ctrl();
}