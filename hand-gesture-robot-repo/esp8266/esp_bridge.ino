#include <ESP8266WiFi.h>

const char* ssid = "RobotESP8266";
const char* password = "robot1234";

WiFiServer server(5000);
WiFiClient client;
String cmd = "";

void setup() {
  Serial.begin(115200);
  delay(2000);
  WiFi.mode(WIFI_AP);
  WiFi.softAP(ssid, password);
  server.begin();
}

void loop() {
  if (!client || !client.connected()) {
    client = server.available();
    if (client) {
      client.println("CONNECTED");
    }
  }

  if (client && client.connected()) {
    while (client.available()) {
      char c = client.read();
      if (c == '\n') {
        cmd.trim();
        if (cmd.length() > 0) {
          char robotCmd = cmd.charAt(0);
          if (robotCmd != 'F' && robotCmd != 'L' && robotCmd != 'R' &&
              robotCmd != 'B' && robotCmd != 'S' && robotCmd != 'M' &&
              robotCmd != 'O') {
            robotCmd = 'S';
          }
          Serial.write(robotCmd);
          client.print("Got: ");
          client.println(robotCmd);
        }
        cmd = "";
      } else {
        cmd += c;
      }
    }
  }
}
