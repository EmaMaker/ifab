#include <Arduino.h>
#include <QuickPID.h>

#include "position_ctrl.h"
#include "odo_loc.h"
#include "wheels.h"

constexpr unsigned long sample_time_position_micros = 15000;

position_t position{0};
unsigned long timer_position = 0;

float pos_x{0}, output_x{0}, setpoint_x{0};
float pos_y{0}, output_y{0}, setpoint_y{0};

QuickPID ctrl_x(&pos_x, &output_x, &setpoint_x, KP_X, KI_X, KD_X, ctrl_x.pMode::pOnError, ctrl_x.dMode::dOnMeas, ctrl_x.iAwMode::iAwCondition, ctrl_x.Action::reverse);
QuickPID ctrl_y(&pos_y, &output_y, &setpoint_y, KP_Y, KI_Y, KD_Y, ctrl_y.pMode::pOnError, ctrl_y.dMode::dOnMeas, ctrl_y.iAwMode::iAwCondition, ctrl_y.Action::reverse);

void init_position_ctrl(void){
    init_wheels();

    ctrl_x.SetSampleTimeUs(sample_time_position_micros);
    ctrl_y.SetSampleTimeUs(sample_time_position_micros);

    ctrl_x.SetOutputLimits(-25*ODO_WHEEL_RADIUS_MM, 25*ODO_WHEEL_RADIUS_MM);
    ctrl_y.SetOutputLimits(-25*ODO_WHEEL_RADIUS_MM, 25*ODO_WHEEL_RADIUS_MM);

    ctrl_x.SetMode(ctrl_x.Control::automatic);
    ctrl_y.SetMode(ctrl_y.Control::automatic);

    timer_position = micros();
    position.tk = timer_position;
}

void update_position_ctrl(void){
  update_wheels();

  unsigned long t = micros();
  if( t - timer_position >= sample_time_position_micros) // 2 times the sampling time of encoders.  Good enough as far as mister Nyquist is concerned
  {
    // odometric localization with encoders
    position_t new_position{0};
    odometric_localization(&new_position, &position);
    position = new_position;

    // position feedback with "off center points
    pos_x = position.x + B_FROM_CENTER*cos(position.theta);
    pos_y = position.y + B_FROM_CENTER*sin(position.theta);

    ctrl_x.Compute();
    ctrl_y.Compute();

    float wt_11 = 2*cos(position.theta) + ODO_DISTANCE_BETWEEN_WHEELS_MM*sin(position.theta);
    float wt_12 = -B_FROM_CENTER*(2*sin(position.theta) - ODO_DISTANCE_BETWEEN_WHEELS_MM*cos(position.theta));
    float wt_21 = 2*cos(position.theta) - ODO_DISTANCE_BETWEEN_WHEELS_MM*sin(position.theta);
    float wt_22 = -B_FROM_CENTER*(2*sin(position.theta) + ODO_DISTANCE_BETWEEN_WHEELS_MM*cos(position.theta));

    // motors go in the reverse direction
    set_right_wheel_angspd(- wt_11 * output_x - wt_12*output_y);
    set_left_wheel_angspd(- wt_21 * output_x - wt_22*output_y);

    timer_position = t;

    Serial.print("X: ");
    Serial.print(position.x);
    Serial.print(" | Y: ");
    Serial.print(position.y);
    Serial.print(" | T: ");
    Serial.println(position.theta);
  }
}


void set_desired_position(float xd, float yd){
  setpoint_x = xd;
  setpoint_y = yd;
}