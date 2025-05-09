#ifndef POSITION_CTRL_H
#define POSITION_CTRL_H

#include "odo_loc.h"

#define CTRL_PHASE_INIT_POSITION -1
// #define CTRL_PHASE_INIT_ORIENT_START -2
#define CTRL_PHASE_INIT_ORIENT_FINAL -3
#define CTRL_PHASE_POSITION 1
#define CTRL_PHASE_IDLE 0
// #define CTRL_PHASE_ORIENT_START 2
#define CTRL_PHASE_ORIENT_FINAL 3

#define KP_X 0.65
#define KI_X 0
#define KD_X 0
#define KP_Y 0.65
#define KI_Y 0
#define KD_Y 0
#define KP_ORIENT 1.25
#define KI_ORIENT 0
#define KD_ORIENT 0

constexpr float MAX_ANGULAR_SPEED = 3; // rad/s
// constexpr float V_MAX = 0.35;
constexpr float V_MAX = 0.18;
constexpr float A_MAX = 0.08;
constexpr float Ts = V_MAX / A_MAX;

constexpr float B_FROM_CENTER = 0.02;

constexpr float VALID_DIST_FROM_TARGET_POS = 0.035;
constexpr float VALID_DIST_FROM_TARGET_ORIENT = radians(5);
constexpr float CAMERA_HISTERESIS_POSITION = 0.025;
constexpr float CAMERA_HISTERESIS_ORIENT = radians(5);

void init_position_ctrl(void);
void update_position_ctrl(void);
void set_desired_position(position_t);
void set_robot_position(position_t);

void controller_position(double[]);
void controller_orient(double[]);
void decouple_t(double[], double[]);
void decouple_w(double[], double[]);

double dst(position_t, position_t);
double dst_sq(position_t, position_t);
double err_orient(position_t, position_t);

double angle_diff(double, double);
double angle_diff_min(double, double);


#endif