const int button = 6;
const int RF = 7;
const int RB = 8;
const int RPWM = 9;
const int LPWM = 10;
const int LF = 11;
const int LB = 12;
const int rightEnc = 2;
const int leftEnc = 4;
const int buzzerPin = 3;
const int morseLed = 5;

const int moveSpeed = 220;
const int turnSpeed = 200;

const unsigned long dotTime = 300;
const unsigned long dashTime = 900;
const unsigned long gapTime = 300;
const unsigned long letterGap = 900;
const unsigned long wordGap = 2100;
const int morseFreq = 2000;

volatile unsigned long rightCount = 0;
volatile unsigned long leftCount = 0;

char currentCmd = 'S';
bool sosMode = false;
bool morseOutputOn = false;
unsigned long morseTimer = 0;
int sosStep = 0;

void countRight() { rightCount++; }
void countLeft() { leftCount++; }

void stopMotors() {
  analogWrite(RPWM, 0);
  analogWrite(LPWM, 0);
  digitalWrite(RF, LOW);
  digitalWrite(RB, LOW);
  digitalWrite(LF, LOW);
  digitalWrite(LB, LOW);
}

void driveBackward() {
  digitalWrite(RF, HIGH);
  digitalWrite(RB, HIGH);
  digitalWrite(LF, LOW);
  digitalWrite(LB, LOW);
  analogWrite(RPWM, moveSpeed);
  analogWrite(LPWM, moveSpeed);
}

void driveForward() {
  digitalWrite(RF, LOW);
  digitalWrite(RB, LOW);
  digitalWrite(LF, HIGH);
  digitalWrite(LB, HIGH);
  analogWrite(RPWM, moveSpeed);
  analogWrite(LPWM, moveSpeed);
}

void turnRight() {
  digitalWrite(RF, HIGH);
  digitalWrite(RB, LOW);
  digitalWrite(LF, HIGH);
  digitalWrite(LB, LOW);
  analogWrite(RPWM, turnSpeed);
  analogWrite(LPWM, turnSpeed);
}

void turnLeft() {
  digitalWrite(RF, LOW);
  digitalWrite(RB, HIGH);
  digitalWrite(LF, LOW);
  digitalWrite(LB, HIGH);
  analogWrite(RPWM, turnSpeed);
  analogWrite(LPWM, turnSpeed);
}

void applyDriveCommand(char cmd) {
  if (cmd == 'F') driveForward();
  else if (cmd == 'B') driveBackward();
  else if (cmd == 'R') turnRight();
  else if (cmd == 'L') turnLeft();
  else stopMotors();
}

void morseOn() {
  if (!morseOutputOn) {
    digitalWrite(morseLed, HIGH);
    tone(buzzerPin, morseFreq);
    morseOutputOn = true;
  }
}

void morseOff() {
  if (morseOutputOn) {
    digitalWrite(morseLed, LOW);
    noTone(buzzerPin);
    morseOutputOn = false;
  }
}

void stopSosMode() {
  sosMode = false;
  sosStep = 0;
  morseOff();
}

void startSosMode() {
  sosMode = true;
  sosStep = 0;
  morseTimer = millis();
  morseOff();
}

void updateSos() {
  if (!sosMode) return;
  unsigned long now = millis();

  switch (sosStep) {
    case 0: morseOn(); morseTimer = now; sosStep = 1; break;
    case 1: if (now - morseTimer >= dotTime) { morseOff(); morseTimer = now; sosStep = 2; } break;
    case 2: if (now - morseTimer >= gapTime) { morseOn(); morseTimer = now; sosStep = 3; } break;
    case 3: if (now - morseTimer >= dotTime) { morseOff(); morseTimer = now; sosStep = 4; } break;
    case 4: if (now - morseTimer >= gapTime) { morseOn(); morseTimer = now; sosStep = 5; } break;
    case 5: if (now - morseTimer >= dotTime) { morseOff(); morseTimer = now; sosStep = 6; } break;
    case 6: if (now - morseTimer >= letterGap) { morseOn(); morseTimer = now; sosStep = 7; } break;
    case 7: if (now - morseTimer >= dashTime) { morseOff(); morseTimer = now; sosStep = 8; } break;
    case 8: if (now - morseTimer >= gapTime) { morseOn(); morseTimer = now; sosStep = 9; } break;
    case 9: if (now - morseTimer >= dashTime) { morseOff(); morseTimer = now; sosStep = 10; } break;
    case 10: if (now - morseTimer >= gapTime) { morseOn(); morseTimer = now; sosStep = 11; } break;
    case 11: if (now - morseTimer >= dashTime) { morseOff(); morseTimer = now; sosStep = 12; } break;
    case 12: if (now - morseTimer >= letterGap) { morseOn(); morseTimer = now; sosStep = 13; } break;
    case 13: if (now - morseTimer >= dotTime) { morseOff(); morseTimer = now; sosStep = 14; } break;
    case 14: if (now - morseTimer >= gapTime) { morseOn(); morseTimer = now; sosStep = 15; } break;
    case 15: if (now - morseTimer >= dotTime) { morseOff(); morseTimer = now; sosStep = 16; } break;
    case 16: if (now - morseTimer >= gapTime) { morseOn(); morseTimer = now; sosStep = 17; } break;
    case 17: if (now - morseTimer >= dotTime) { morseOff(); morseTimer = now; sosStep = 18; } break;
    case 18: if (now - morseTimer >= wordGap) { sosStep = 0; } break;
  }
}

void setup() {
  pinMode(button, INPUT_PULLUP);
  pinMode(RF, OUTPUT);
  pinMode(RB, OUTPUT);
  pinMode(RPWM, OUTPUT);
  pinMode(LF, OUTPUT);
  pinMode(LB, OUTPUT);
  pinMode(LPWM, OUTPUT);
  pinMode(rightEnc, INPUT);
  pinMode(leftEnc, INPUT);
  pinMode(13, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
  pinMode(morseLed, OUTPUT);

  attachInterrupt(digitalPinToInterrupt(rightEnc), countRight, RISING);
  attachInterrupt(digitalPinToInterrupt(leftEnc), countLeft, RISING);

  Serial.begin(115200);
  Serial1.begin(115200);
  stopMotors();
  morseOff();
  Serial.println("Nano Every ready");
}

void loop() {
  if (Serial1.available()) {
    char cmd = Serial1.read();
    if (cmd == 'F' || cmd == 'B' || cmd == 'L' || cmd == 'R' ||
        cmd == 'S' || cmd == 'M' || cmd == 'O') {
      if (cmd != currentCmd) {
        currentCmd = cmd;
        Serial.print("VALID CMD: ");
        Serial.println(currentCmd);

        if (cmd == 'M') {
          stopMotors();
          stopSosMode();
          morseOn();
          digitalWrite(13, HIGH);
        } else if (cmd == 'O') {
          stopMotors();
          startSosMode();
          digitalWrite(13, HIGH);
        } else {
          stopSosMode();
          morseOff();
          if (cmd == 'S') digitalWrite(13, LOW);
          else digitalWrite(13, HIGH);
          applyDriveCommand(cmd);
        }
      }
    }
  }

  updateSos();
}
