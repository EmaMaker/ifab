#ifndef WHEELS_H
#define WHEELS_H

#define WHEELS_KP 1.5
#define WHEELS_KI 15.0

void init_wheels(void);
void update_wheels(void);

void init_encoders(void);
void update_encoders(void);
void reset_encoders(void);

float get_angspd_sx(void);
float get_angspd_dx(void);

void set_left_wheel_angspd(float);
void set_right_wheel_angspd(float);

#endif