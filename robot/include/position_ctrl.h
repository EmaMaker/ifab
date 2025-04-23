#ifndef POSITION_CTRL_H
#define POSITION_CTRL_H

#include "odo_loc.h"

#define CTRL_PHASE_INIT_POSITION -1
#define CTRL_PHASE_INIT_ORIENT_FINAL -2
#define CTRL_PHASE_POSITION 0
#define CTRL_PHASE_IDLE -10
#define CTRL_PHASE_ORIENT_FINAL 1

#define KP_X 0.35
#define KI_X 0
#define KD_X 0
#define KP_Y 0.35
#define KI_Y 0
#define KD_Y 0
#define KP_ORIENT 0.5
#define KI_ORIENT 0
#define KD_ORIENT 0
constexpr float V_MAX = 0.2;
constexpr float A_MAX = 0.1;
constexpr float Ts = V_MAX / A_MAX;

constexpr float B_FROM_CENTER = 0.02;

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


#endif