#ifndef WIRELESS_H
#define WIRELESS_H

#include <Arduino.h>

#define UDP_PORT 4242
#define DEBUG_IP "10.42.0.1"
#define MY_IP "10.42.0.18"
#define DEBUG_PORT 47269

const char ssid[] = "ifab-hotspot";
const char pwd[] = "ifabifab";
const char hostname[] = "ifab";
const IPAddress ip(10,42,0,18);    

bool setup_wifi();
bool is_wifi_connected();
bool wifi_connect();
void setup_ota();
void udp_receive();
void udp_send_string(const char[], int, const char[]);
void udp_send_string(const char[], int, String);
// debug string formatted for teleplot
// void udp_send_debug_string(const char[] const char[]);
void udp_send_debug_string(String, String, bool);
void udp_send_debug_string(String, String, String, bool);

#endif