#include <Arduino.h>
#include <QuickPID.h>
#include <elapsedMillis.h>

#include "position_ctrl.h"
#include "wheels.h"

elapsedMillis timer_position_update{0};
elapsedMillis timer_position_ctrl{0};
constexpr unsigned long sample_time_position_millis = 15;

position_t position_robot{0};
position_t position_init{0};
position_t position_fin{0};

unsigned long timer_position = 0;
float pos_x{0}, output_x{0}, setpoint_x{0};
float pos_y{0}, output_y{0}, setpoint_y{0};
float pos_orient{0}, output_orient{0}, setpoint_orient{0};
float s{0.0};
float s_dot{0.0};
float traj_start_time{0.0};

double angspd[] = {0.0, 0.0};

int ctrl_phase{CTRL_PHASE_IDLE};

QuickPID ctrl_x(&pos_x, &output_x, &setpoint_x, KP_X, KI_X, KD_X, ctrl_x.pMode::pOnError, ctrl_x.dMode::dOnMeas, ctrl_x.iAwMode::iAwCondition, ctrl_x.Action::direct);
QuickPID ctrl_y(&pos_y, &output_y, &setpoint_y, KP_Y, KI_Y, KD_Y, ctrl_y.pMode::pOnError, ctrl_y.dMode::dOnMeas, ctrl_y.iAwMode::iAwCondition, ctrl_y.Action::direct);
QuickPID ctrl_orient(&pos_orient, &output_orient, &setpoint_orient, KP_ORIENT, KI_ORIENT, KD_ORIENT, ctrl_orient.pMode::pOnError, ctrl_orient.dMode::dOnMeas, ctrl_orient.iAwMode::iAwCondition, ctrl_orient.Action::direct);

void init_position_ctrl(void){
    init_wheels();

    ctrl_x.SetSampleTimeUs(sample_time_position_millis*1e3);
    ctrl_y.SetSampleTimeUs(sample_time_position_millis*1e3);
    ctrl_orient.SetSampleTimeUs(sample_time_position_millis*1e3);

    // motors are rated at about 200RPM -> 20 rad/s
    ctrl_x.SetOutputLimits(-25*ODO_WHEEL_RADIUS, 25*ODO_WHEEL_RADIUS);
    ctrl_y.SetOutputLimits(-25*ODO_WHEEL_RADIUS, 25*ODO_WHEEL_RADIUS);
    ctrl_orient.SetOutputLimits(-25*ODO_WHEEL_RADIUS, 25*ODO_WHEEL_RADIUS);

    timer_position_update = 0;
    timer_position_ctrl = 0;
    position_robot.tk = 0;
    ctrl_phase = CTRL_PHASE_IDLE;
}

void update_position_ctrl(){
  update_wheels();
  
  // 2 times the sampling time of encoders.  Good enough as far as mister Nyquist is concerned
  if(timer_position_update < sample_time_position_millis) return;

  // odometric localization with encoders
  position_t new_position{0};
  odometric_localization(&new_position, &position_robot);
  position_robot = new_position;

  Serial.print("X: ");
  Serial.print(position_robot.x);
  Serial.print(" | Y: ");
  Serial.print(position_robot.y);
  Serial.print(" | T: ");
  Serial.println(position_robot.theta);  

  if(ctrl_phase == CTRL_PHASE_IDLE){
      ctrl_x.SetMode(ctrl_x.Control::manual);
      ctrl_y.SetMode(ctrl_y.Control::manual);
      ctrl_orient.SetMode(ctrl_orient.Control::manual);

      angspd[0] = 0;
      angspd[1] = 0;
      // Serial.println("IDLE");
  }
  if(ctrl_phase == CTRL_PHASE_INIT_POSITION){
    ctrl_x.Initialize();
    ctrl_y.Initialize();
    ctrl_x.SetMode(ctrl_x.Control::automatic);
    ctrl_y.SetMode(ctrl_y.Control::automatic);

    // Reset trajectory progress
    s = 0.0;
    traj_start_time = 0; // Start time of the movement
    timer_position_ctrl = 0;

    Serial.println("INIT POS");
    ctrl_phase = CTRL_PHASE_POSITION;  
  }
  if(ctrl_phase == CTRL_PHASE_POSITION){
    if(dst(position_robot, position_fin) <= 0.05){
      ctrl_x.SetMode(ctrl_x.Control::manual);
      ctrl_y.SetMode(ctrl_y.Control::manual);

      ctrl_phase = CTRL_PHASE_INIT_ORIENT_FINAL;
    }else controller_position(angspd);
  }
      // Serial.println("POS");
  if (ctrl_phase == CTRL_PHASE_INIT_ORIENT_FINAL){
    ctrl_orient.Initialize();
    ctrl_orient.SetMode(ctrl_orient.Control::automatic);

    ctrl_phase = CTRL_PHASE_ORIENT_FINAL;
      Serial.println("INIT ORIENT");
  }
  if (ctrl_phase == CTRL_PHASE_ORIENT_FINAL){
      // Serial.println("ORIENT");
      
    double d1 = angle_diff(position_robot.theta, position_fin.theta);
    double d2 = TWO_PI - d1;
    double d = -min(d1, d2);
    
    pos_orient = d;
    setpoint_orient = 0;
    if(abs(d) <= radians(5)){
      ctrl_orient.SetMode(ctrl_orient.Control::manual);
      ctrl_phase = CTRL_PHASE_IDLE;

      // Turn off motors when becoming idle
      angspd[0] = 0;
      angspd[1] = 0;
    } else controller_orient(angspd); 
  }
  
  set_left_wheel_angspd(angspd[1]);
  set_right_wheel_angspd(angspd[0]);
  timer_position_update = 0;
}

void controller_position(double output[]){
  float tf = timer_position_ctrl*1e-3;

  // position feedback with "off center" points
  pos_x = position_robot.x + B_FROM_CENTER*cos(position_robot.theta);
  pos_y = position_robot.y + B_FROM_CENTER*sin(position_robot.theta);

  // Time-based interpolation factor for bang-coast-bang trajectory
  float dx = position_fin.x - position_init.x;
  float dy = position_fin.y - position_init.y;

  float L= std::sqrt(dx*dx + dy*dy);
  float T = (L*A_MAX + V_MAX*V_MAX)/(V_MAX*A_MAX);

  // A_MAX = V_MAX / Ts;
  if (tf<= Ts && tf>= 0){

    s_dot = A_MAX*(tf - traj_start_time)/L;
    s = A_MAX * tf*tf / (2*L);
  }
  else if (tf<= T -Ts && tf> Ts){
    s_dot = A_MAX * Ts / L;
    s = A_MAX * Ts * (tf- Ts)/L + A_MAX * Ts * Ts / (2*L);
  }
  else if (tf<= T && tf> T - Ts){
    s_dot = A_MAX*(T - tf)/L;
    s = A_MAX*T * (tf- T + Ts)/L - A_MAX * ((tf*tf - (T-Ts)*(T-Ts)) / (2*L)) + A_MAX * Ts *(T-Ts - Ts)/L + A_MAX * Ts * Ts / (2*L);
  }
  else s_dot = 0;

  setpoint_x = position_init.x + s * (position_fin.x - position_init.x); //x_des
  setpoint_y = position_init.y + s * (position_fin.y - position_init.y); //y_des

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
}

void controller_orient(double output[]){
  ctrl_orient.Compute();
  double inw[] = {0, output_orient};
  decouple_w(output, inw);
}

void decouple_t(double output[], double input[]){
    constexpr double d = ODO_DISTANCE_BETWEEN_WHEELS;
    constexpr double r = ODO_WHEEL_RADIUS;
    constexpr double b = B_FROM_CENTER;
    constexpr double det = 2*b*r;

    double t_11 = cos(position_robot.theta);
    double t_12 = sin(position_robot.theta);
    double t_21 = -sin(position_robot.theta)/b;
    double t_22 = cos(position_robot.theta)/b;

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

void set_robot_position(position_t p){
  position_robot = p;
  position_robot.tk = 0;
}

void set_desired_position(position_t goal){
  position_init = position_robot;
  position_fin = goal;

  if (ctrl_phase != CTRL_PHASE_POSITION) ctrl_phase = CTRL_PHASE_INIT_POSITION;
}

double dst(position_t p1, position_t p2){
  return sqrt(dst_sq(p1, p2));
}

double dst_sq(position_t p1, position_t p2){
  double ex = p1.x - p2.x;
  double ey = p2.y - p2.y;
  return ex*ex + ey*ey;
}

double angle_diff(double a1, double a2){
  double n1x = cos(a1);
  double n1y = sin(a1);
  double n1z = 0;
  double n2x = cos(a2);
  double n2y = sin(a2);
  double n2z = 0;

  double sprod = n1x*n2x + n1y*n2y + n1z*n2z;
  double cprod_z = -n1y*n2x + n1x*n2y;
  double sign = cprod_z >= 0 ? 1 : -1;
  return sign * acos(sprod);
}