#include <AccelStepper.h>
#include <Servo.h>


// ============================================================
// Pin Configuration
// ============================================================

// IR Sensor
#define IR_SENSOR_PIN 13

// LEDs
#define LED_1_PIN 6
#define LED_2_PIN 9
#define LED_3_PIN 10

// Buzzer
#define BUZZER_PIN 7

// Servo
#define SERVO_PIN 12

// Stepper Motor
#define MOTOR_EN_PIN 8
#define MOTOR_STEP_PIN 5
#define MOTOR_DIR_PIN 2


// ============================================================
// Servo Configuration
// ============================================================

Servo sortingServo;

#define CHOCO_ANGLE 0
#define CANDY_ANGLE 45


// ============================================================
// Stepper Motor Configuration
// ============================================================

#define MOTOR_INTERFACE_TYPE 1

// ------------------------------------------------------------
// Speed Level
// ------------------------------------------------------------

#define SPEED_LEVEL_MIN 1
#define SPEED_LEVEL_MAX 10

// 기본 속도 단계
#define DEFAULT_SPEED_LEVEL 6


// ------------------------------------------------------------
// Speed Table
// ------------------------------------------------------------
//
// AccelStepper speed
//
// 1  -> 1000
// 2  -> 1200
// 3  -> 1400
// 4  -> 1600
// 5  -> 1800
// 6  -> 2000
// 7  -> 2200
// 8  -> 2400
// 9  -> 2600
// 10 -> 2800
//
// ------------------------------------------------------------

const int motorSpeedTable[11] = {

  0,      // index 0 사용하지 않음

  1000,   // 1단계
  1200,   // 2단계
  1400,   // 3단계
  1600,   // 4단계
  1800,   // 5단계
  2000,   // 6단계
  2200,   // 7단계
  2400,   // 8단계
  2600,   // 9단계
  3000    // 10단계
};


// 현재 속도 단계
int motorSpeedLevel =
  DEFAULT_SPEED_LEVEL;


// 현재 실제 모터 속도
int motorSpeed =
  motorSpeedTable[DEFAULT_SPEED_LEVEL];


// ============================================================
// AccelStepper
// ============================================================

AccelStepper stepperx(
  MOTOR_INTERFACE_TYPE,
  MOTOR_STEP_PIN,
  MOTOR_DIR_PIN
);


// ============================================================
// Conveyor Direction
// ============================================================

#define MOTOR_DIRECTION 1


// ============================================================
// Timing Configuration
// ============================================================

// 기준 속도
#define BASE_SPEED 2000


// ------------------------------------------------------------
// IR Sensor -> Camera
// ------------------------------------------------------------
//
// 속도 2000 기준 1000ms
//
// 실제 시간은 현재 motorSpeed에 따라 자동 계산
//
// speed 1000 -> 2000ms
// speed 2000 -> 1000ms
// speed 2800 -> 약 714ms
//
// ------------------------------------------------------------

#define IR_TO_CAMERA_BASE_TIME_MS 1000


// Camera -> sorting position
#define CAMERA_TO_SORTING_BASE_TIME_MS 1000


// Servo movement time
#define SERVO_MOVE_TIME_MS 300


// Servo reset time
#define SERVO_RESET_TIME_MS 200


// Small delay after stopping motor
#define MOTOR_STOP_DELAY_MS 100

// ============================================================
// IR Sensor Configuration
// ============================================================

// Most IR obstacle sensors output LOW
// when an object is detected.
#define IR_DETECTED LOW


// Sensor signal must remain detected
// for this time before confirmation.
#define IR_DEBOUNCE_MS 50


// Prevent the same object from being detected
// multiple times.
#define IR_COOLDOWN_MS 1000


// ============================================================
// Buzzer Configuration
// ============================================================

#define BUZZER_FREQUENCY 1000

#define BUZZER_DURATION_MS 1000


// ============================================================
// System State
// ============================================================

bool motorRunning = false;


// ============================================================
// IR Sensor State
// ============================================================

// Raw sensor state
bool irRawState = false;


// Confirmed object state
bool irConfirmedState = false;


// Time when IR first became active
unsigned long irDetectionStartTime = 0;


// Last confirmed object detection time
unsigned long lastIRDetectionTime = 0;


// ============================================================
// Camera Waiting State
// ============================================================

// True while object is moving
// from IR sensor to camera position.
bool waitingForCamera = false;


// Time when camera travel started
unsigned long cameraWaitStartTime = 0;


// Calculated travel time
unsigned long cameraWaitTime = 0;


// ============================================================
// Arduino Responses
// ============================================================

#define SYSTEM_READY_RESPONSE "SYSTEM_READY"

#define SERVO_0_RESPONSE "SERVO_0"

#define SERVO_45_RESPONSE "SERVO_45"

#define MOTOR_RESTART_RESPONSE "MOTOR_RESTART"

#define BUZZER_START_RESPONSE "BUZZER_START"

#define BUZZER_DONE_RESPONSE "BUZZER_DONE"


// ============================================================
// Speed Responses
// ============================================================

#define SPEED_CHANGED_RESPONSE "SPEED_CHANGED"

#define SPEED_ERROR_RESPONSE "SPEED_ERROR"


// ============================================================
// Function Prototypes
// ============================================================

void startMotor();

void stopMotor();

void handleCommand(String command);

void handleChoco();

void handleCandy();

void handleBuzzer();

void handleProcessDone();

void checkIRSensor();

void checkCameraTimer();

void setMotorSpeedLevel(
  int level
);

unsigned long calculateTimeBySpeed(
  unsigned long baseTime
);


// ============================================================
// Setup
// ============================================================

void setup() {

  // ----------------------------------------------------------
  // Serial Communication
  // ----------------------------------------------------------

  Serial.begin(9600);


  // ----------------------------------------------------------
  // IR Sensor
  // ----------------------------------------------------------

  pinMode(
    IR_SENSOR_PIN,
    INPUT
  );

  // ----------------------------------------------------------
  // LEDs
  // ----------------------------------------------------------

  pinMode(
    LED_1_PIN,
    OUTPUT
  );

  pinMode(
    LED_2_PIN,
    OUTPUT
  );

  pinMode(
    LED_3_PIN,
    OUTPUT
  );


  digitalWrite(
    LED_1_PIN,
    LOW
  );

  digitalWrite(
    LED_2_PIN,
    LOW
  );

  digitalWrite(
    LED_3_PIN,
    LOW
  );


  // ----------------------------------------------------------
  // Buzzer
  // ----------------------------------------------------------

  pinMode(
    BUZZER_PIN,
    OUTPUT
  );

  digitalWrite(
    BUZZER_PIN,
    LOW
  );


  // ----------------------------------------------------------
  // Motor Enable
  // ----------------------------------------------------------

  pinMode(
    MOTOR_EN_PIN,
    OUTPUT
  );


  // ----------------------------------------------------------
  // Motor Direction
  // ----------------------------------------------------------

  pinMode(
    MOTOR_DIR_PIN,
    OUTPUT
  );


  // ----------------------------------------------------------
  // Stepper Configuration
  // ----------------------------------------------------------

  stepperx.setMaxSpeed(
    motorSpeedTable[SPEED_LEVEL_MAX]
  );


  stepperx.setSpeed(
    MOTOR_DIRECTION * motorSpeed
  );


  // ----------------------------------------------------------
  // Enable Motor Driver
  // ----------------------------------------------------------

  // LOW = Enable
  digitalWrite(
    MOTOR_EN_PIN,
    LOW
  );


  // ----------------------------------------------------------
  // Servo
  // ----------------------------------------------------------

  sortingServo.attach(
    SERVO_PIN
  );


  sortingServo.write(
    CHOCO_ANGLE
  );


  // ----------------------------------------------------------
  // Start Conveyor
  // ----------------------------------------------------------

  startMotor();


  // ----------------------------------------------------------
  // Initial LED
  // ----------------------------------------------------------

  digitalWrite(
    LED_1_PIN,
    HIGH
  );

  digitalWrite(
    LED_2_PIN,
    LOW
  );

  digitalWrite(
    LED_3_PIN,
    LOW
  );


  // ----------------------------------------------------------
  // System Ready
  // ----------------------------------------------------------

  delay(500);


  Serial.println(
    SYSTEM_READY_RESPONSE
  );


  // ----------------------------------------------------------
  // Send initial speed information
  // ----------------------------------------------------------

  Serial.print(
    SPEED_CHANGED_RESPONSE
  );

  Serial.print(
    ":"
  );

  Serial.println(
    motorSpeedLevel
  );
}


// ============================================================
// Main Loop
// ============================================================

void loop() {

  // ----------------------------------------------------------
  // Run Stepper
  // ----------------------------------------------------------

  if (motorRunning) {

    stepperx.runSpeed();
  }


  // ----------------------------------------------------------
  // Raspberry Pi Serial Command
  // ----------------------------------------------------------

  if (Serial.available() > 0) {

    String command =
      Serial.readStringUntil('\n');


    command.trim();


    if (command.length() > 0) {

      handleCommand(
        command
      );
    }
  }


  // ----------------------------------------------------------
  // Check IR Sensor
  // ----------------------------------------------------------

  checkIRSensor();


  // ----------------------------------------------------------
  // Check Camera Timer
  // ----------------------------------------------------------

  checkCameraTimer();
}

// ============================================================
// Handle Raspberry Pi Command
// ============================================================

void handleCommand(
  String command
) {

  // ----------------------------------------------------------
  // CHOCO
  // ----------------------------------------------------------

  if (command == "CHOCO") {

    handleChoco();

    return;
  }


  // ----------------------------------------------------------
  // CANDY
  // ----------------------------------------------------------

  if (command == "CANDY") {

    handleCandy();

    return;
  }


  // ----------------------------------------------------------
  // BUZZER_ON
  // ----------------------------------------------------------

  if (command == "BUZZER_ON") {

    handleBuzzer();

    return;
  }


  // ----------------------------------------------------------
  // PROCESS_DONE
  // ----------------------------------------------------------

  if (command == "PROCESS_DONE") {

    handleProcessDone();

    return;
  }


  // ----------------------------------------------------------
  // SET_SPEED
  // ----------------------------------------------------------
  //
  // Raspberry Pi:
  //
  // SET_SPEED:1
  // SET_SPEED:2
  // ...
  // SET_SPEED:10
  //
  // ----------------------------------------------------------

  if (
    command.startsWith(
      "SET_SPEED:"
    )
  ) {

    String levelString =
      command.substring(
        10
      );


    int level =
      levelString.toInt();


    setMotorSpeedLevel(
      level
    );


    return;
  }


  // ----------------------------------------------------------
  // Unknown Command
  // ----------------------------------------------------------

  Serial.print(
    "UNKNOWN_COMMAND:"
  );


  Serial.println(
    command
  );
}


// ============================================================
// Set Motor Speed Level
// ============================================================

void setMotorSpeedLevel(
  int level
) {

  // ----------------------------------------------------------
  // Validate speed level
  // ----------------------------------------------------------

  if (
    level < SPEED_LEVEL_MIN
    ||
    level > SPEED_LEVEL_MAX
  ) {

    Serial.print(
      SPEED_ERROR_RESPONSE
    );

    Serial.print(
      ":INVALID_LEVEL="
    );

    Serial.println(
      level
    );

    return;
  }


  // ----------------------------------------------------------
  // Update speed level
  // ----------------------------------------------------------

  motorSpeedLevel =
    level;


  // ----------------------------------------------------------
  // Get actual motor speed
  // ----------------------------------------------------------

  motorSpeed =
    motorSpeedTable[
      motorSpeedLevel
    ];


  // ----------------------------------------------------------
  // Apply speed
  // ----------------------------------------------------------

  stepperx.setSpeed(
    MOTOR_DIRECTION * motorSpeed
  );


  // ----------------------------------------------------------
  // Recalculate camera travel time
  // ----------------------------------------------------------

  if (waitingForCamera) {

    cameraWaitTime =
      calculateTimeBySpeed(
        IR_TO_CAMERA_BASE_TIME_MS
      );
  }

  // ----------------------------------------------------------
  // Send response
  // ----------------------------------------------------------

  Serial.print(
    SPEED_CHANGED_RESPONSE
  );

  Serial.print(
    ":"
  );

  Serial.print(
    motorSpeedLevel
  );

  Serial.print(
    ":"
  );

  Serial.println(
    motorSpeed
  );


  // ----------------------------------------------------------
  // Debug
  // ----------------------------------------------------------

  Serial.print(
    "MOTOR_SPEED_LEVEL="
  );

  Serial.println(
    motorSpeedLevel
  );

  Serial.print(
    "MOTOR_SPEED="
  );

  Serial.println(
    motorSpeed
  );
}


// ============================================================
// Start Motor
// ============================================================

void startMotor() {

  // ----------------------------------------------------------
  // Enable Motor Driver
  // ----------------------------------------------------------

  digitalWrite(
    MOTOR_EN_PIN,
    LOW
  );


  // ----------------------------------------------------------
  // Set Motor Speed
  // ----------------------------------------------------------

  stepperx.setSpeed(
    MOTOR_DIRECTION * motorSpeed
  );


  // ----------------------------------------------------------
  // Motor Running State
  // ----------------------------------------------------------

  motorRunning =
    true;


  // ----------------------------------------------------------
  // Debug
  // ----------------------------------------------------------

  Serial.print(
    "MOTOR_STARTED:SPEED="
  );


  Serial.println(
    motorSpeed
  );
}


// ============================================================
// Stop Motor
// ============================================================

void stopMotor() {

  // ----------------------------------------------------------
  // Stop Stepper
  // ----------------------------------------------------------

  stepperx.setSpeed(
    0
  );


  // ----------------------------------------------------------
  // Disable Motor Driver
  // ----------------------------------------------------------

  digitalWrite(
    MOTOR_EN_PIN,
    HIGH
  );


  // ----------------------------------------------------------
  // Motor State
  // ----------------------------------------------------------

  motorRunning =
    false;


  // ----------------------------------------------------------
  // Debug
  // ----------------------------------------------------------

  Serial.println(
    "MOTOR_STOPPED"
  );
}


// ============================================================
// Calculate Travel Time
// ============================================================

unsigned long calculateTimeBySpeed(
  unsigned long baseTime
) {

  int currentSpeed =
    motorSpeed;


  // ----------------------------------------------------------
  // Safety check
  // ----------------------------------------------------------

  if (
    currentSpeed <= 0
  ) {

    return baseTime;
  }


  // ----------------------------------------------------------
  // Calculate
  // ----------------------------------------------------------
  //
  // BASE_SPEED = 2000
  //
  // speed 1000 -> 2000ms
  // speed 2000 -> 1000ms
  // speed 2800 -> 714ms
  //
  // ----------------------------------------------------------

  unsigned long calculatedTime =
    (
      baseTime
      * (unsigned long)BASE_SPEED
    )
    /
    (unsigned long)currentSpeed;


  return calculatedTime;
}

// ============================================================
// CHOCO Processing
// ============================================================

void handleChoco() {

  Serial.println(
    "CHOCO_RECEIVED"
  );


  // ----------------------------------------------------------
  // Stop Motor
  // ----------------------------------------------------------

  stopMotor();


  delay(
    MOTOR_STOP_DELAY_MS
  );


  // ----------------------------------------------------------
  // Move Servo to 0 degrees
  // ----------------------------------------------------------

  sortingServo.write(
    CHOCO_ANGLE
  );


  delay(
    SERVO_MOVE_TIME_MS
  );


  // ----------------------------------------------------------
  // ACK
  // ----------------------------------------------------------

  Serial.println(
    SERVO_0_RESPONSE
  );
}


// ============================================================
// CANDY Processing
// ============================================================

void handleCandy() {

  Serial.println(
    "CANDY_RECEIVED"
  );


  // ----------------------------------------------------------
  // Stop Motor
  // ----------------------------------------------------------

  stopMotor();


  delay(
    MOTOR_STOP_DELAY_MS
  );


  // ----------------------------------------------------------
  // Move Servo to 45 degrees
  // ----------------------------------------------------------

  sortingServo.write(
    CANDY_ANGLE
  );


  delay(
    SERVO_MOVE_TIME_MS
  );


  // ----------------------------------------------------------
  // ACK
  // ----------------------------------------------------------

  Serial.println(
    SERVO_45_RESPONSE
  );
}


// ============================================================
// Buzzer Processing
// ============================================================

void handleBuzzer() {

  Serial.println(
    BUZZER_START_RESPONSE
  );


  // ----------------------------------------------------------
  // LEDs ON
  // ----------------------------------------------------------

  digitalWrite(
    LED_1_PIN,
    HIGH
  );

  digitalWrite(
    LED_2_PIN,
    HIGH
  );

  digitalWrite(
    LED_3_PIN,
    HIGH
  );


  // ----------------------------------------------------------
  // Buzzer ON
  // ----------------------------------------------------------

  tone(
    BUZZER_PIN,
    BUZZER_FREQUENCY
  );


  delay(
    BUZZER_DURATION_MS
  );


  // ----------------------------------------------------------
  // Buzzer OFF
  // ----------------------------------------------------------

  noTone(
    BUZZER_PIN
  );


  // ----------------------------------------------------------
  // LEDs OFF
  // ----------------------------------------------------------

  digitalWrite(
    LED_1_PIN,
    LOW
  );

  digitalWrite(
    LED_2_PIN,
    LOW
  );

  digitalWrite(
    LED_3_PIN,
    LOW
  );


  // ----------------------------------------------------------
  // Buzzer Complete
  // ----------------------------------------------------------

  Serial.println(
    BUZZER_DONE_RESPONSE
  );
}


// ============================================================
// PROCESS_DONE Processing
// ============================================================

void handleProcessDone() {

  Serial.println(
    "PROCESS_DONE_RECEIVED"
  );

  // ----------------------------------------------------------
  // Do NOT reset servo here.
  //
  // CANDY     -> 45 degrees 유지
  // CHOCOLATE -> 0 degrees 유지
  // ----------------------------------------------------------


  // ----------------------------------------------------------
  // Reset IR State
  // ----------------------------------------------------------

  irRawState =
    false;

  irConfirmedState =
    false;

  irDetectionStartTime =
    0;


  // ----------------------------------------------------------
  // Restart Conveyor
  // ----------------------------------------------------------

  startMotor();


  Serial.println(
    MOTOR_RESTART_RESPONSE
  );
}


// ============================================================
// IR Sensor Processing
// ============================================================

void checkIRSensor() {

  int sensorValue =
    digitalRead(
      IR_SENSOR_PIN
    );


  bool detected =
    (
      sensorValue ==
      IR_DETECTED
    );


  unsigned long now =
    millis();


  // ==========================================================
  // Object is detected
  // ==========================================================

  if (detected) {

    // --------------------------------------------------------
    // Start debounce timer
    // --------------------------------------------------------

    if (!irRawState) {

      irRawState =
        true;


      irDetectionStartTime =
        now;
    }


    // --------------------------------------------------------
    // Confirm detection
    // --------------------------------------------------------

    if (
      !irConfirmedState
      &&
      (
        now -
        irDetectionStartTime
        >=
        IR_DEBOUNCE_MS
      )
      &&
      (
        now -
        lastIRDetectionTime
        >=
        IR_COOLDOWN_MS
      )
      &&
      !waitingForCamera
    ) {

      // ------------------------------------------------------
      // Confirm object
      // ------------------------------------------------------

      irConfirmedState =
        true;


      lastIRDetectionTime =
        now;


      Serial.println(
        "OBJECT_DETECTED"
      );


      // ------------------------------------------------------
      // Start travel timer
      // ------------------------------------------------------

      cameraWaitStartTime =
        now;


      cameraWaitTime =
        calculateTimeBySpeed(
          IR_TO_CAMERA_BASE_TIME_MS
        );


      waitingForCamera =
        true;


      Serial.print(
        "IR_TO_CAMERA_TIME_MS="
      );


      Serial.println(
        cameraWaitTime
      );


      // ------------------------------------------------------
      // Make sure motor is running
      // ------------------------------------------------------

      if (!motorRunning) {

        startMotor();
      }
    }
  }


  // ==========================================================
  // Object is no longer detected
  // ==========================================================

  else {

    irRawState =
      false;


    irConfirmedState =
      false;


    irDetectionStartTime =
      0;
  }
}


// ============================================================
// Camera Timer
// ============================================================
//
// IR 감지 후 일정 시간이 지나면
// 컨베이어를 정지하고 PHOTO를 보냅니다.
//
// PHOTO 이후에는 모터를 다시 시작하지 않습니다.
//
// Raspberry Pi에서 PROCESS_DONE을 보내면
// handleProcessDone()에서 모터를 재시작합니다.
//
// ============================================================

void checkCameraTimer() {

  // ----------------------------------------------------------
  // Nothing to do
  // ----------------------------------------------------------

  if (!waitingForCamera) {

    return;
  }


  unsigned long now =
    millis();

  // ----------------------------------------------------------
  // Camera position reached
  // ----------------------------------------------------------

  if (
    now -
    cameraWaitStartTime
    >=
    cameraWaitTime
  ) {

    // --------------------------------------------------------
    // Stop motor
    // --------------------------------------------------------

    stopMotor();


    delay(
      MOTOR_STOP_DELAY_MS
    );


    // --------------------------------------------------------
    // Send PHOTO
    // --------------------------------------------------------

    Serial.println(
      "PHOTO"
    );


    // --------------------------------------------------------
    // Keep motor stopped
    // --------------------------------------------------------

    waitingForCamera =
      false;
  }
}