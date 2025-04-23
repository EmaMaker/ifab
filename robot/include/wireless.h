#ifndef WIRELESS_H
#define WIRELESS_H

#include <Arduino.h>

#define UDP_PORT 4242
#define DEBUG_IP "192.168.1.236"
#define DEBUG_PORT 47269

const char ssid[] = "Radiomarelli";
const char pwd[] = "Magnadyn3Radiomarell1Philip5@";
const char hostname[] = "ifab";

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