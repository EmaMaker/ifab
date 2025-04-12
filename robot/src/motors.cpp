#include <Arduino.h>
#include "pins.h"
#include "motors.h"
#include "wheels.h"

int mot_pins[][3] = {
    {PIN_MOTR_A, PIN_MOTR_B, PIN_MOTR_PWM},
    {PIN_MOTL_A, PIN_MOTL_B, PIN_MOTL_PWM}
};
// account for motor PWM deadzone
// might as well hardcode them, maybe better as parameter in .h?
int start_pwm[] = { 78, 78};

void init_motors(){
    for (int i = 0; i < 2; i++){
        pinMode(mot_pins[i][0], OUTPUT);
        pinMode(mot_pins[i][1], OUTPUT);
    }
    analogWriteFreq(15000);
}

void drive_motor(int motor, int pwm){
  motor = constrain(motor, 0, 1);
  pwm = constrain(pwm, -255, 255);
  digitalWrite(mot_pins[motor][0], pwm >= 0 ? HIGH : LOW);
  digitalWrite(mot_pins[motor][1], pwm >= 0 ? LOW : HIGH);
  analogWrite(mot_pins[motor][2], abs(pwm));
}

// Convert voltage input into PWM command, accounting for motor deadzone
void drive_motor_volt(int motor, double voltage){
    motor = constrain(motor, 0, 1);
    int pwm = map(abs(voltage), 0, 12, start_pwm[motor], 255); // also account for motor deadzone
  
    digitalWrite(mot_pins[motor][0], voltage >= 0 ? HIGH : LOW);
    digitalWrite(mot_pins[motor][1], voltage >= 0 ? LOW : HIGH);
    analogWrite(mot_pins[motor][2], pwm);
}

void test_motors(void){  
  int dir = 1;
    while(true){
      for(int m = 0; m < 2; m++){
        for(int i = 0; i < 255; i++){
          Serial.print("PWM: ");
          Serial.println(dir*i);
          drive_motor(m,  dir*i);
          delay(25);
    
          update_encoders();
        }
        delay(1000);
        drive_motor(m, 0);
    }
    dir = -dir;
  }
}