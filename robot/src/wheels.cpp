#include <Arduino.h>
#include <QuickPID.h>
#include <PicoEncoder.h>

#include "pins.h"
#include "motors.h"
#include "wheels.h"

PicoEncoder enc_dx, enc_sx;

unsigned long t = time_us_32();
unsigned long old_t = time_us_32();

constexpr unsigned long sample_time_micros = 5000;
constexpr int mobileavg_nelems = 200;
constexpr float alpha = 1.0 / mobileavg_nelems;
constexpr float resolution_rad = 0.0057;

long pos_sx = 0;
long pos_dx = 0;
long old_pos_sx = 0;
long old_pos_dx = 0;
float old_spd_sx = 0;
float old_spd_dx = 0;

float mobileavg_window_sx[mobileavg_nelems]{};
float mobileavg_window_dx[mobileavg_nelems]{};

// PI Controllers
float spd_sx{0}, spd_dx{0};

float output_sx{0}, setpoint_sx{0}; //setpoint in substep/s for now
float output_dx{0}, setpoint_dx{0};

QuickPID ctrl_sx(&spd_sx, &output_sx, &setpoint_sx, WHEELS_KP, WHEELS_KI, 0, ctrl_sx.pMode::pOnError, ctrl_sx.dMode::dOnMeas, ctrl_sx.iAwMode::iAwCondition, ctrl_sx.Action::direct);
QuickPID ctrl_dx(&spd_dx, &output_dx, &setpoint_dx, WHEELS_KP, WHEELS_KI, 0, ctrl_dx.pMode::pOnError, ctrl_dx.dMode::dOnMeas, ctrl_dx.iAwMode::iAwCondition, ctrl_dx.Action::direct);

void init_wheels(){
    init_motors();
    init_encoders();

    ctrl_sx.SetSampleTimeUs(sample_time_micros);
    ctrl_dx.SetSampleTimeUs(sample_time_micros);

    ctrl_sx.SetOutputLimits(-12, 12);
    ctrl_dx.SetOutputLimits(-12, 12);

    ctrl_sx.SetMode(ctrl_sx.Control::automatic);
    ctrl_dx.SetMode(ctrl_dx.Control::automatic);

}

void init_encoders(){
  enc_sx.begin(PIN_ENCD_L);
  enc_dx.begin(PIN_ENCD_R);
}

void update_wheels(){
    update_encoders();

    if(ctrl_sx.Compute()) drive_motor_volt(MOT_L, output_sx);
    if(ctrl_dx.Compute()) drive_motor_volt(MOT_R, output_dx);
} 

void update_encoders(){
  enc_sx.update();
  enc_dx.update();

  t = time_us_32();
  unsigned long dt = t-old_t;
  if(dt < sample_time_micros) return;

  pos_sx = enc_sx.step;
  pos_dx = enc_dx.step;

  double spd_tmp_sx = (pos_sx - old_pos_sx)*resolution_rad/(dt*1e-6);
  double spd_tmp_dx = (pos_dx - old_pos_dx)*resolution_rad/(dt*1e-6);

  mobileavg_window_sx[0] = spd_tmp_sx;
  mobileavg_window_dx[0] = spd_tmp_dx;
  
  spd_sx = mobileavg_window_sx[1] + alpha*(spd_tmp_sx - mobileavg_window_sx[mobileavg_nelems - 1]);
  spd_dx = mobileavg_window_dx[1] + alpha*(spd_tmp_dx - mobileavg_window_dx[mobileavg_nelems - 1]);

  for(int i = mobileavg_nelems-1; i > 0; i--){
    mobileavg_window_sx[i] = mobileavg_window_sx[i-1];
    mobileavg_window_dx[i] = mobileavg_window_dx[i-1];
  }
  old_t = t;
  old_pos_sx = pos_sx;
  old_pos_dx = pos_dx;
  
#ifdef PRINT_VELOCITY
  Serial.print("Angular velocity (sx): ");
  Serial.println(spd_sx);
  Serial.print("Angular velocity (dx): ");
  Serial.println(spd_dx);
#endif //PRINT_VELOCITY
}

void set_left_wheel_angspd(float vl_d){
  setpoint_sx = vl_d;
}

void set_right_wheel_angspd(float vr_d){
  setpoint_dx = vr_d;
}

float get_angspd_sx(){
  return spd_sx;
}

float get_angspd_dx(){
  return spd_dx;
}