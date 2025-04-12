#ifndef MOTORS_H
#define MOTORS_H

void init_motors(void);
void test_motors(void);
void drive_motor(int, int);
void drive_motor_volt(int, double);
#endif