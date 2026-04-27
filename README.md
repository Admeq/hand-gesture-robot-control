# Hand Gesture Robot Control

A computer-vision robot control system that uses a laptop webcam to recognize hand gestures and send real-time commands to a robot over Wi-Fi. The main project point highlighted in the repo is the laptop-to-ESP-to-Nano communication chain, so the custom circuit is not included, but was made. 
## Overview

This project lets a user control a mobile robot using hand gestures captured by a laptop camera. Python uses OpenCV and MediaPipe Hand Landmarker to classify gestures such as forward, reverse, left, right, stop, Morse hold, and SOS mode. The laptop sends a command over TCP to an ESP8266 configured as a Wi-Fi access point and TCP server. The ESP8266 forwards validated commands over serial to an Arduino Nano Every, which handles robot movement and Morse/SOS output.

The main focus of this project is the communication chain:

**Laptop webcam vision -> Wi-Fi TCP -> ESP8266 -> UART serial -> Arduino Nano Every -> robot action**

## Features

- Real-time hand gesture recognition using a laptop webcam
- Gesture-to-command mapping for robot movement
- Wi-Fi command transmission through ESP8266
- UART forwarding from ESP8266 to Arduino Nano Every
- Movement commands: forward, reverse, left, right, stop
- Extra output modes: Morse hold and SOS mode
- Stable-frame filtering to reduce noisy gesture switching
- On-screen live feedback for gesture and transmitted command

## System Architecture

### Laptop
- Runs Python with OpenCV and MediaPipe
- Detects one hand from webcam video
- Determines finger states and gesture class
- Sends a single-character command over TCP

### ESP8266
- Creates Wi-Fi access point
- Accepts TCP connection from laptop
- Validates received command characters
- Forwards valid commands over serial

### Arduino Nano Every
- Receives serial commands from ESP8266
- Controls robot movement
- Runs buzzer and LED Morse/SOS behavior

## Hardware Setup

The hardware is organized around the communication path rather than the full motor driver details.
The robot used a custom-built motor interface/control circuit integrated with the Arduino Nano Every. While the repository focuses on the laptop-to-ESP-to-Nano communication path, the motor/control circuitry was designed and assembled specifically for this robot.

### Main connections
- Power the ESP8266
- Power the Arduino Nano Every
- Connect **ESP8266 TX -> Nano RX**
- Connect **common GND between ESP8266 and Nano**

The laptop connects wirelessly to the ESP8266 access point. The ESP8266 receives command characters from the laptop and forwards them to the Nano using serial communication. The Nano then controls the robot behavior.

## Repository Structure

```text
hand-gesture-robot-control/
├── requirements.txt
├── python/
│   └── gesture_control.py
├── esp8266/
│   └── esp_bridge.ino
├── arduino_nano/
│   └── robot_controller.ino

```

## Gestures

- Open palm -> Stop
- Index finger -> Forward
- Index + middle -> Reverse
- Thumb only -> Left
- Closed fist -> Right
- Four fingers, no thumb -> Morse hold
- Thumb + index + middle -> SOS mode

## Software Stack

- Python 3
- OpenCV
- MediaPipe Tasks Vision
- Socket communication
- ESP8266 Arduino framework
- Arduino Nano Every
- Embedded C/C++

## Setup

### 1. Python side

Install dependencies:

```bash
pip install -r requirements.txt
```

Place the `hand_landmarker.task` model file in the same folder as `python/gesture_control.py` or update the path inside the script.

Run:

```bash
python python/gesture_control.py
```

### 2. ESP8266 side

- Open `esp8266/esp_bridge.ino` in Arduino IDE
- Select the correct ESP8266 board
- Upload the code

### 3. Arduino Nano Every side

- Open `arduino_nano/robot_controller.ino` in Arduino IDE
- Select Arduino Nano Every
- Upload the code

## Demo

Add the following when you can:
- one clear photo of the robot
- one screenshot of the hand landmark detection window
- one short demo video link

You can put the video link inside `media/demo_link.txt`.

## Challenges Solved

- Converted webcam hand gestures into robot commands in real time
- Reduced accidental command switching using stable-frame filtering
- Created a reliable laptop-to-ESP-to-Nano communication chain
- Added extra interaction modes beyond simple motion control
- Coordinated computer vision, networking, and embedded control in one system
