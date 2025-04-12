#include <Arduino.h>
#include "odo_loc.h"
#include "wheels.h"


void odometric_localization(position_t* new_position, position_t* old_position){
    // exact linearization
    // when omega circa 0 fall back to runge kutta
    unsigned long t = micros();
    unsigned long dt = t - old_position->tk;
    double dt_f = dt*1e-6;
    double omega = angular_w(get_angspd_sx(), get_angspd_dx());
    double v = linear_v(get_angspd_sx(), get_angspd_dx());

    new_position->tk = t;
    new_position->theta = old_position->theta + omega*dt_f;

    if (omega <= 1e-4){
        // fall back to runge kutta/euler
        new_position->x = old_position->x + v*dt_f*cos(old_position->theta);
        new_position->y = old_position->y + v*dt_f*sin(old_position->theta);
    }else{
        // exact integration
        new_position->x = old_position->x + v/omega * (sin(new_position->theta) - sin(old_position->theta));
        new_position->y = old_position->y - v/omega * (cos(new_position->theta) - cos(old_position->theta));
    }
}

double linear_v(double w_l, double w_r){
    return ODO_WHEEL_RADIUS*(w_l + w_r)*0.5;
}

double angular_w(double w_l, double w_r){
    return ODO_WHEEL_RADIUS*(w_r - w_l)/ODO_DISTANCE_BETWEEN_WHEELS;
}