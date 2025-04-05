#ifndef ODO_LOC_H
#define ODO_LOC_H


constexpr double ODO_DISTANCE_BETWEEN_WHEELS_MM = 0.245;
constexpr double ODO_WHEEL_RADIUS_MM = 0.055;

typedef struct{
    double x{0};
    double y{0};
    double theta{0};
    unsigned long tk{0}; // in micros
} position_t;

void odometric_localization(position_t*, position_t*);
double linear_v(double w_l, double w_r);
double angular_w(double w_l, double w_r);

#endif