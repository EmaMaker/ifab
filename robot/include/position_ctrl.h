#ifndef POSITION_CTRL_H
#define POSITION_CTRL_H

#define KP_X 1
#define KI_X 0
#define KD_X 0
#define KP_Y 1
#define KI_Y 0
#define KD_Y 0

constexpr float B_FROM_CENTER = 0.02;

void init_position_ctrl(void);
void update_position_ctrl(void);
void set_desired_position(float, float);

#endif