#include <Arduino.h>
#include <QuickPID.h>

#include "position_ctrl.h"
#include "odo_loc.h"
#include "wheels.h"

constexpr unsigned long sample_time_position_micros = 15000;

position_t position{0};
position_t position_init{0};
position_t position_fin{0};

unsigned long timer_position = 0;
float pos_x{0}, output_x{0}, setpoint_x{0};
float pos_y{0}, output_y{0}, setpoint_y{0};
float s{0.0};
float s_dot{0.0};
float traj_start_time{0.0};

double angspd[] = {0.0, 0.0};

QuickPID ctrl_x(&pos_x, &output_x, &setpoint_x, KP_X, KI_X, KD_X, ctrl_x.pMode::pOnError, ctrl_x.dMode::dOnMeas, ctrl_x.iAwMode::iAwCondition, ctrl_x.Action::direct);
QuickPID ctrl_y(&pos_y, &output_y, &setpoint_y, KP_Y, KI_Y, KD_Y, ctrl_y.pMode::pOnError, ctrl_y.dMode::dOnMeas, ctrl_y.iAwMode::iAwCondition, ctrl_y.Action::direct);

void init_position_ctrl(void){
    init_wheels();

    ctrl_x.SetSampleTimeUs(sample_time_position_micros);
    ctrl_y.SetSampleTimeUs(sample_time_position_micros);

    // motors are rated at about 200RPM -> 20 rad/s
    ctrl_x.SetOutputLimits(-25*ODO_WHEEL_RADIUS, 25*ODO_WHEEL_RADIUS);
    ctrl_y.SetOutputLimits(-25*ODO_WHEEL_RADIUS, 25*ODO_WHEEL_RADIUS);

    ctrl_x.SetMode(ctrl_x.Control::automatic);
    ctrl_y.SetMode(ctrl_y.Control::automatic);

    timer_position = micros();
    position.tk = timer_position;
}

void update_position_ctrl(){
  update_wheels();
  controller_position(angspd);

  set_left_wheel_angspd(angspd[1]);
  set_right_wheel_angspd(angspd[0]);
}

void controller_position(double output[]){
  unsigned long t = micros();
  float tf = t*1e-6;

  if( t - timer_position >= sample_time_position_micros) // 2 times the sampling time of encoders.  Good enough as far as mister Nyquist is concerned
  {
    // odometric localization with encoders
    position_t new_position{0};
    odometric_localization(&new_position, &position);
    position = new_position;

    // position feedback with "off center" points
    pos_x = position.x + B_FROM_CENTER*cos(position.theta);
    pos_y = position.y + B_FROM_CENTER*sin(position.theta);

    // Time-based interpolation factor for bang-coast-bang trajectory
    float dx = position_fin.x - position_init.x;
    float dy = position_fin.y - position_init.y;

    float L= std::sqrt(dx*dx + dy*dy);
    float T = (L*A_MAX + V_MAX*V_MAX)/(V_MAX*A_MAX);

    // A_MAX = V_MAX / Ts;
    if (tf - traj_start_time <= Ts && tf - traj_start_time >= 0){

      s_dot = A_MAX*(tf - traj_start_time)/L;
      s = A_MAX * (tf - traj_start_time) * (tf - traj_start_time) / (2*L);
    }
    else if (tf - traj_start_time <= T -Ts && tf - traj_start_time > Ts){
      s_dot = A_MAX * Ts / L;
      s = A_MAX * Ts * (tf - traj_start_time - Ts)/L + A_MAX * Ts * Ts / (2*L);
    }
    else if (tf - traj_start_time <= T && tf - traj_start_time > T - Ts){
      s_dot = A_MAX*(T - tf + traj_start_time)/L;
      s = A_MAX*T * (tf - traj_start_time - T + Ts)/L - A_MAX * (((tf-traj_start_time)*(tf-traj_start_time) - (T-Ts)*(T-Ts)) / (2*L)) + A_MAX * Ts *(T-Ts - Ts)/L + A_MAX * Ts * Ts / (2*L);
    }
    else s_dot = 0;

    setpoint_x = position_init.x + s * (position_fin.x - position_init.x); //x_des
    setpoint_y = position_init.y + s * (position_fin.y - position_init.y); //y_des

    // Serial.println("==========");
    // Serial.print("s: ");
    // Serial.println(s);
    // Serial.print("s_dot: ");
    // Serial.println(s_dot);
    // Serial.print("setpoint_x: ");
    // Serial.println(setpoint_x);
    // Serial.print("setpoint_y: ");
    // Serial.println(setpoint_y);

    ctrl_x.Compute();
    ctrl_y.Compute();

    // Add feedforward term to output of P feedback controller
    double output_x_ff = output_x + (position_fin.x - position_init.x)*s_dot;
    double output_y_ff = output_y + (position_fin.y - position_init.y)*s_dot;

    double in_t[] = {output_x_ff, output_y_ff};
    double out_t[] = {0, 0};
    double out_w[] = {0, 0};
    decouple_t(out_t, in_t);
    decouple_w(output, out_t);

    timer_position = t;

    // Serial.print("X: ");
    // Serial.print(position.x);
    // Serial.print(" | Y: ");
    // Serial.print(position.y);
    // Serial.print(" | T: ");
    // Serial.println(position.theta);  
  }
}

void decouple_t(double output[], double input[]){
    constexpr double d = ODO_DISTANCE_BETWEEN_WHEELS;
    constexpr double r = ODO_WHEEL_RADIUS;
    constexpr double b = B_FROM_CENTER;
    constexpr double det = 2*b*r;

    double t_11 = cos(position.theta);
    double t_12 = sin(position.theta);
    double t_21 = -sin(position.theta)/b;
    double t_22 = cos(position.theta)/b;

    output[0] = t_11 * input[0] + t_12*input[1];
    output[1] = t_21 * input[0] + t_22*input[1];
}

void decouple_w(double output[], double input[]){
  constexpr double d = ODO_DISTANCE_BETWEEN_WHEELS;
  constexpr double r = ODO_WHEEL_RADIUS;
  constexpr double b = B_FROM_CENTER;
  constexpr double det = 2*b*r;
  double w_11 = 1/r;
  double w_12 = d/(2*r);
  double w_21 = 1/r;
  double w_22 = -d/(2*r);

  output[0] = w_11*input[0] + w_12*input[1];
  output[1] = w_21*input[0] + w_22*input[1];

}

void set_desired_position(float xg, float yg){
  // Store the current position as the start of trajectory
  position_init = position;

  // Store the final goal
  position_fin.x = xg;
  position_fin.y = yg;

  // Reset trajectory progress
  s = 0.0;
  traj_start_time = micros()*1e-6; // Start time of the movement
}