#ifndef ODO_LOC_H
#define ODO_LOC_H

#include <elapsedMillis.h>

constexpr double ODO_DISTANCE_BETWEEN_WHEELS = 0.2;
constexpr double ODO_WHEEL_RADIUS = 0.071;

typedef struct{
    double x{0};
    double y{0};
    double theta{0};
    elapsedMillis tk{0}; // in micros
} position_t;

void odometric_localization(position_t*, position_t*);
double linear_v(double w_l, double w_r);
double angular_w(double w_l, double w_r);

#endif