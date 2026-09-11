import serial
import time
import os
import json
from datetime import datetime

import cv2
import requests
from picamera2 import Picamera2
from ultralytics import YOLO

import paho.mqtt.client as mqtt


# ============================================================
# Configuration
# ============================================================

# ------------------------------------------------------------
# Arduino
# ------------------------------------------------------------

ARDUINO_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600

SERVO_RESPONSE_TIMEOUT = 3.0
BUZZER_RESPONSE_TIMEOUT = 3.0
SERIAL_RESPONSE_TIMEOUT = 3.0


# ------------------------------------------------------------
# Conveyor Motor Speed
# ------------------------------------------------------------

MOTOR_SPEED_LEVEL_MIN = 1
MOTOR_SPEED_LEVEL_MAX = 10

# 현재 사용할 기본 속도 단계
# Arduino DEFAULT_SPEED_LEVEL과 맞춰서 사용
MOTOR_SPEED_LEVEL = 10

SPEED_RESPONSE_TIMEOUT = 3.0


# ------------------------------------------------------------
# YOLO
# ------------------------------------------------------------

MODEL_PATH = "/home/rpi/test/best.pt"

CONFIDENCE_THRESHOLD = 0.60


# ------------------------------------------------------------
# YOLO Class Names
# ------------------------------------------------------------

YOLO_CANDY_CLASS_NAME = "CANDY"
YOLO_CHOCOLATE_CLASS_NAME = "CHOCOLATE"


# ------------------------------------------------------------
# Camera
# ------------------------------------------------------------

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720


# ------------------------------------------------------------
# Image
# ------------------------------------------------------------

PHOTO_DIR = "/home/rpi/test/photos"


# ------------------------------------------------------------
# Image Upload Server
# ------------------------------------------------------------

IMAGE_UPLOAD_URL = (
    "http://210.119.12.62:5051/api/product-images"
)

IMAGE_UPLOAD_TIMEOUT = 10.0

# ------------------------------------------------------------
# MQTT
# ------------------------------------------------------------

MQTT_BROKER_HOST = "210.119.12.62"
MQTT_BROKER_PORT = 1883

MQTT_USERNAME = "root"
MQTT_PASSWORD = "mqtt123456"

MQTT_KEEPALIVE = 60

MQTT_CLIENT_ID = "raspberry-pi-smart-sorting"

MQTT_PRODUCT_TOPIC = (
    "smart_sorting/camera/product_detection"
)

MQTT_COMPONENT_TOPIC = (
    "smart_sorting/component/status/update"
)

MQTT_QOS = 1

MQTT_PUBLISH_TIMEOUT = 3.0


# ============================================================
# Chocolate Production
# ============================================================

CHOCOLATE_UNIT_PER_SET = 10

chocolate_count = 0


# ============================================================
# Arduino Commands
# ============================================================

CHOCO_COMMAND = b"CHOCO\n"
CANDY_COMMAND = b"CANDY\n"
BUZZER_ON_COMMAND = b"BUZZER_ON\n"
PROCESS_DONE_COMMAND = b"PROCESS_DONE\n"

# Speed command
# Example:
# SET_SPEED:1
# SET_SPEED:2
# ...
# SET_SPEED:10
SET_SPEED_COMMAND = "SET_SPEED:{level}\n"

# ============================================================
# Arduino Responses
# ============================================================

SERVO_45_RESPONSE = "SERVO_45"
SERVO_0_RESPONSE = "SERVO_0"

MOTOR_RESTART_RESPONSE = "MOTOR_RESTART"

BUZZER_START_RESPONSE = "BUZZER_START"
BUZZER_DONE_RESPONSE = "BUZZER_DONE"

SYSTEM_READY_RESPONSE = "SYSTEM_READY"

OBJECT_DETECTED_RESPONSE = "OBJECT_DETECTED"

PHOTO_RESPONSE = "PHOTO"


# ------------------------------------------------------------
# Speed Responses
# ------------------------------------------------------------

SPEED_CHANGED_RESPONSE = "SPEED_CHANGED"
SPEED_ERROR_RESPONSE = "SPEED_ERROR"


# ============================================================
# Arduino Status Messages
# ============================================================

ARDUINO_STATUS_MESSAGES = {
    "CANDY_RECEIVED",
    "CHOCO_RECEIVED",
    "MOTOR_STOPPED",
    "PROCESS_DONE_RECEIVED",
    "MOTOR_RESTART",
    "SYSTEM_READY",
    "OBJECT_DETECTED",
    "PHOTO",
    "BUZZER_START",
    "BUZZER_DONE",
    "SERVO_0",
    "SERVO_45",
}


# ============================================================
# Component Codes
# ============================================================

COMPONENT_RASPBERRY_PI = "RASPBERRY_PI"
COMPONENT_ARDUINO = "ARDUINO"
COMPONENT_IR_SENSOR = "IR_SENSOR"
COMPONENT_CAMERA = "CAMERA"
COMPONENT_CONVEYOR = "CONVEYOR"
COMPONENT_SERVO = "SORTING_SERVO"
COMPONENT_BUZZER = "BUZZER"
COMPONENT_DISPLAY = "WORKER_DISPLAY"
COMPONENT_WORKER_UI = "WORKER_UI"


# ============================================================
# Component Status
# ============================================================

STATUS_NORMAL = "NORMAL"
STATUS_WARNING = "WARNING"
STATUS_ERROR = "ERROR"
STATUS_OFFLINE = "OFFLINE"


# ============================================================
# Error Codes
# ============================================================

CAMERA_ERROR = "CAMERA_ERROR"

SERVO_ACK_TIMEOUT = "SERVO_ACK_TIMEOUT"
SERVO_ACK_ERROR = "SERVO_ACK_ERROR"

STEPPER_ERROR = "STEPPER_ERROR"
IR_ERROR = "IR_ERROR"
ARDUINO_ERROR = "ARDUINO_ERROR"

BUZZER_ERROR = "BUZZER_ERROR"

SERIAL_DISCONNECTED = "SERIAL_DISCONNECTED"
SERIAL_ERROR = "SERIAL_ERROR"
SERIAL_TIMEOUT = "SERIAL_TIMEOUT"
UNKNOWN_COMMAND = "UNKNOWN_COMMAND"

YOLO_ERROR = "YOLO_ERROR"
MODEL_LOAD_ERROR = "MODEL_LOAD_ERROR"
NO_DETECTION = "NO_DETECTION"
IMAGE_SAVE_ERROR = "IMAGE_SAVE_ERROR"

NETWORK_ERROR = "NETWORK_ERROR"
NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
SERVER_ERROR = "SERVER_ERROR"
DATA_SEND_ERROR = "DATA_SEND_ERROR"

UNKNOWN_CLASS = "UNKNOWN_CLASS"

IMAGE_UPLOAD_FAILED = "IMAGE_UPLOAD_FAILED"


# ============================================================
# Create Photo Directory
# ============================================================

os.makedirs(
    PHOTO_DIR,
    exist_ok=True
)


# ============================================================
# Global Variables
# ============================================================

arduino = None
picam2 = None
model = None

mqtt_client = None
mqtt_connected = False


# ============================================================
# Logging
# ============================================================

def log(message):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    print(
        f"[{timestamp}] {message}"
    )


# ============================================================
# Create Result
# ============================================================

def create_result(
    status,
    result_type,
    confidence,
    image_path,
    error_type=None,
    error_code=None
):

    return {
        "status": status,
        "type": result_type,
        "confidence": round(
            float(confidence),
            2
        ),
        "image_path": image_path,
        "error_type": error_type,
        "error_code": error_code
    }
    
# ============================================================
# Print Result
# ============================================================

def print_result(result):

    log(
        "=========================================="
    )

    log("FINAL RESULT")

    log(
        f"STATUS     : {result['status']}"
    )

    log(
        f"TYPE       : {result['type']}"
    )

    log(
        f"CONFIDENCE : "
        f"{result['confidence']:.2f}"
    )

    log(
        f"IMAGE PATH : {result['image_path']}"
    )

    log(
        f"ERROR TYPE : {result['error_type']}"
    )

    log(
        f"ERROR CODE : {result['error_code']}"
    )

    log(
        "=========================================="
    )


# ============================================================
# Find Next Photo Number
# ============================================================

def get_next_photo_number():

    number = 1

    while True:

        filename = (
            f"photo_{number:03d}.jpg"
        )

        filepath = os.path.join(
            PHOTO_DIR,
            filename
        )

        if not os.path.exists(filepath):

            return number

        number += 1
        
# ============================================================
# Upload Image To Server
# ============================================================

def upload_image_to_server(filepath):

    if not os.path.exists(filepath):

        log(
            f"Image file does not exist: {filepath}"
        )

        return None, IMAGE_SAVE_ERROR

    try:

        log(
            "=========================================="
        )

        log(
            "Uploading image to server..."
        )

        log(
            f"Local image: {filepath}"
        )

        log(
            f"Upload URL: {IMAGE_UPLOAD_URL}"
        )

        with open(filepath, "rb") as image_file:

            files = {
                "image": (
                    os.path.basename(filepath),
                    image_file,
                    "image/jpeg"
                )
            }

            response = requests.post(
                IMAGE_UPLOAD_URL,
                files=files,
                timeout=IMAGE_UPLOAD_TIMEOUT
            )

        log(
            f"Image upload HTTP status: "
            f"{response.status_code}"
        )

        if (
            response.status_code < 200
            or
            response.status_code >= 300
        ):

            log(
                "Image upload failed."
            )

            log(
                f"Server response: "
                f"{response.text}"
            )

            if response.status_code >= 500:

                return None, SERVER_ERROR

            return None, NETWORK_ERROR

        try:

            response_data = response.json()

        except ValueError:

            log(
                "Server response is not valid JSON."
            )

            log(
                f"Response: {response.text}"
            )

            return None, SERVER_ERROR

        image_path = (
            response_data.get(
                "imagePath"
            )
        )

        if not image_path:

            log(
                "Server response does not contain imagePath."
            )

            log(
                f"Response JSON: {response_data}"
            )

            return None, SERVER_ERROR

        log(
            "Image upload successful."
        )

        log(
            f"Server imagePath: {image_path}"
        )

        log(
            "=========================================="
        )

        return image_path, None

    except requests.Timeout:

        log(
            "Image upload timeout."
        )

        return None, NETWORK_TIMEOUT

    except requests.ConnectionError as e:

        log(
            f"Image upload connection error: {e}"
        )

        return None, NETWORK_ERROR

    except requests.RequestException as e:

        log(
            f"Image upload request error: {e}"
        )

        return None, NETWORK_ERROR

    except Exception as e:

        log(
            f"Image upload error: {e}"
        )

        return None, NETWORK_ERROR
        
# ============================================================
# Normalize YOLO Class Name
# ============================================================

def normalize_class_name(class_name):

    if class_name is None:

        return None

    return str(
        class_name
    ).strip().upper()


# ============================================================
# Get YOLO Class Name
# ============================================================

def get_yolo_class_name(class_id):

    if model is None:

        return None

    try:

        names = model.names

        if isinstance(names, dict):

            class_name = names.get(
                class_id
            )

        elif isinstance(names, list):

            if (
                class_id < 0
                or
                class_id >= len(names)
            ):

                return None

            class_name = names[class_id]

        else:

            return None

        return normalize_class_name(
            class_name
        )

    except Exception as e:

        log(
            f"Failed to read YOLO class name: {e}"
        )

        return None


# ============================================================
# Convert YOLO Class To Product Type
# ============================================================

def convert_yolo_class_to_product_type(
    class_name
):

    normalized_name = normalize_class_name(
        class_name
    )

    if normalized_name is None:

        return None, None

    if normalized_name == YOLO_CANDY_CLASS_NAME:

        return "CANDY", "CANDY"

    if normalized_name in (
        "CHOCO",
        "CHOCOLATE"
    ):

        return "CHOCO", "CHOCOLATE"

    return None, None


# ============================================================
# MQTT Callback
# ============================================================

def mqtt_on_connect(
    client,
    userdata,
    flags,
    reason_code,
    properties
):

    global mqtt_connected

    if reason_code.is_failure:

        mqtt_connected = False

        log(
            f"MQTT connection failed: "
            f"{reason_code}"
        )

        return

    mqtt_connected = True

    log(
        "MQTT connected successfully."
    )
    
# ============================================================
# MQTT Disconnect
# ============================================================

def mqtt_on_disconnect(
    client,
    userdata,
    disconnect_flags,
    reason_code,
    properties
):

    global mqtt_connected

    mqtt_connected = False

    log(
        f"MQTT disconnected: "
        f"{reason_code}"
    )


# ============================================================
# Initialize MQTT
# ============================================================

def initialize_mqtt():

    global mqtt_client
    global mqtt_connected

    log(
        "Initializing MQTT..."
    )

    try:

        mqtt_client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=MQTT_CLIENT_ID,
            protocol=mqtt.MQTTv311
        )

        mqtt_client.on_connect = (
            mqtt_on_connect
        )

        mqtt_client.on_disconnect = (
            mqtt_on_disconnect
        )

        if MQTT_USERNAME:

            mqtt_client.username_pw_set(
                MQTT_USERNAME,
                MQTT_PASSWORD
            )

        mqtt_client.connect(
            MQTT_BROKER_HOST,
            MQTT_BROKER_PORT,
            MQTT_KEEPALIVE
        )

        mqtt_client.loop_start()

        start_time = time.time()

        while (
            not mqtt_connected
            and
            time.time() - start_time
            < MQTT_PUBLISH_TIMEOUT
        ):

            time.sleep(0.1)

        if mqtt_connected:

            log(
                "MQTT initialization successful."
            )

            return True

        log(
            "MQTT broker connection not established."
        )

        return False

    except Exception as e:

        mqtt_client = None
        mqtt_connected = False

        log(
            f"MQTT initialization failed: {e}"
        )

        return False


# ============================================================
# MQTT Publish
# ============================================================

def mqtt_publish(
    topic,
    payload
):

    if mqtt_client is None:

        log(
            "MQTT publish skipped: "
            "client is not initialized."
        )

        return False

    if not mqtt_connected:

        log(
            f"MQTT publish skipped: "
            f"broker disconnected. "
            f"Topic={topic}"
        )

        return False

    try:

        message = json.dumps(
            payload,
            ensure_ascii=False
        )

        log(
            f"MQTT publish -> {topic}"
        )

        log(
            f"MQTT payload -> {message}"
        )

        info = mqtt_client.publish(
            topic,
            message,
            qos=MQTT_QOS,
            retain=False
        )

        if (
            info.rc
            != mqtt.MQTT_ERR_SUCCESS
        ):

            log(
                f"MQTT publish failed. "
                f"rc={info.rc}"
            )

            return False

        try:

            info.wait_for_publish(
                timeout=MQTT_PUBLISH_TIMEOUT
            )

        except Exception as e:

            log(
                f"MQTT publish wait error: {e}"
            )

            return False

        if not info.is_published():

            log(
                "MQTT publish timeout."
            )

            return False

        log(
            "MQTT publish successful."
        )

        return True

    except Exception as e:

        log(
            f"MQTT publish error: {e}"
        )

        return False
        
# ============================================================
# Publish Component Status
# ============================================================

def publish_component_status(
    component_code,
    status,
    error_code=None
):

    payload = {
        "componentCode": component_code,
        "status": status,
        "errorCode": error_code
    }

    return mqtt_publish(
        MQTT_COMPONENT_TOPIC,
        payload
    )


# ============================================================
# Publish Product Detection
# ============================================================

def publish_product_detection(
    classification_status,
    product_type_code,
    confidence,
    image_path
):

    payload = {
        "classificationStatus":
            classification_status,

        "productTypeCode":
            product_type_code,

        "confidence":
            round(
                float(confidence),
                2
            ),

        "imagePath":
            image_path
    }

    return mqtt_publish(
        MQTT_PRODUCT_TOPIC,
        payload
    )


# ============================================================
# Send CHOCO
# ============================================================

def send_choco_command():

    if arduino is None:

        log(
            "Arduino is not connected."
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_OFFLINE,
            SERIAL_DISCONNECTED
        )

        return False

    try:

        log(
            "Sending CHOCO command..."
        )

        arduino.write(
            CHOCO_COMMAND
        )

        arduino.flush()

        log(
            "CHOCO command sent successfully."
        )

        return True

    except serial.SerialException as e:

        log(
            f"Arduino serial error: {e}"
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_ERROR,
            SERIAL_ERROR
        )

        return False

    except Exception as e:

        log(
            f"Failed to send CHOCO command: {e}"
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_ERROR,
            ARDUINO_ERROR
        )

        return False


# ============================================================
# Send CANDY
# ============================================================

def send_candy_command():

    if arduino is None:

        log(
            "Arduino is not connected."
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_OFFLINE,
            SERIAL_DISCONNECTED
        )

        return False

    try:

        log(
            "Sending CANDY command..."
        )

        arduino.write(
            CANDY_COMMAND
        )

        arduino.flush()

        log(
            "CANDY command sent successfully."
        )

        return True

    except serial.SerialException as e:

        log(
            f"Arduino serial error: {e}"
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_ERROR,
            SERIAL_ERROR
        )

        return False

    except Exception as e:

        log(
            f"Failed to send CANDY command: {e}"
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_ERROR,
            ARDUINO_ERROR
        )

        return False
        
# ============================================================
# Send BUZZER_ON
# ============================================================

def send_buzzer_on():

    if arduino is None:

        log(
            "Arduino is not connected."
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_OFFLINE,
            SERIAL_DISCONNECTED
        )

        return False

    try:

        log(
            "Sending BUZZER_ON to Arduino..."
        )

        arduino.write(
            BUZZER_ON_COMMAND
        )

        arduino.flush()

        log(
            "BUZZER_ON command sent successfully."
        )

        return True

    except serial.SerialException as e:

        log(
            f"Arduino serial error: {e}"
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_ERROR,
            SERIAL_ERROR
        )

        return False

    except Exception as e:

        log(
            f"Failed to send BUZZER_ON: {e}"
        )

        publish_component_status(
            COMPONENT_BUZZER,
            STATUS_ERROR,
            BUZZER_ERROR
        )

        return False


# ============================================================
# Send PROCESS_DONE
# ============================================================

def send_process_done():

    if arduino is None:

        log(
            "PROCESS_DONE skipped: Arduino unavailable."
        )

        return False

    try:

        log(
            "Sending PROCESS_DONE to Arduino..."
        )

        arduino.write(
            PROCESS_DONE_COMMAND
        )

        arduino.flush()

        log(
            "PROCESS_DONE sent successfully."
        )

        return True

    except serial.SerialException as e:

        log(
            f"Arduino serial error: {e}"
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_ERROR,
            SERIAL_ERROR
        )

        return False

    except Exception as e:

        log(
            f"Failed to send PROCESS_DONE: {e}"
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_ERROR,
            ARDUINO_ERROR
        )

        return False
        
# ============================================================
# Read Arduino Serial
# ============================================================

def read_arduino_line():

    if arduino is None:

        return None, SERIAL_DISCONNECTED

    try:

        data = (
            arduino.readline()
            .decode(
                "utf-8",
                errors="ignore"
            )
            .strip()
        )

        return data, None

    except serial.SerialException as e:

        log(
            f"Arduino serial exception: {e}"
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_ERROR,
            SERIAL_ERROR
        )

        return None, SERIAL_ERROR

    except OSError as e:

        log(
            f"Arduino OS communication error: {e}"
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_ERROR,
            SERIAL_ERROR
        )

        return None, SERIAL_ERROR

    except Exception as e:

        log(
            f"Arduino serial read error: {e}"
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_ERROR,
            SERIAL_ERROR
        )

        return None, SERIAL_ERROR
        
# ============================================================
# Is Normal Arduino Message
# ============================================================

def is_normal_arduino_message(data):

    if not data:

        return False

    if data in ARDUINO_STATUS_MESSAGES:

        return True

    if data.startswith(
        "MOTOR_STARTED:SPEED="
    ):

        return True

    if data.startswith(
        "CHOCOLATE_COUNT:"
    ):

        return True

    if data.startswith(
        "SPEED_CHANGED:"
    ):

        return True

    if data.startswith(
        "SPEED_ERROR:"
    ):

        return True

    if data.startswith(
        "IR_TO_CAMERA_TIME_MS="
    ):

        return True

    if data.startswith(
        "MOTOR_SPEED_LEVEL="
    ):

        return True

    if data.startswith(
        "MOTOR_SPEED="
    ):

        return True

    return False


# ============================================================
# Handle Normal Arduino Status
# ============================================================

def handle_normal_arduino_status(data):

    if data == "MOTOR_STOPPED":

        log(
            "Arduino reports: motor stopped."
        )

        publish_component_status(
            COMPONENT_CONVEYOR,
            STATUS_NORMAL,
            None
        )

        return


    if data.startswith(
        "MOTOR_STARTED:SPEED="
    ):

        log(
            f"Arduino reports: {data}"
        )

        publish_component_status(
            COMPONENT_CONVEYOR,
            STATUS_NORMAL,
            None
        )

        return


    if data == "CANDY_RECEIVED":

        log(
            "Arduino received CANDY command."
        )

        return


    if data == "CHOCO_RECEIVED":

        log(
            "Arduino received CHOCO command."
        )

        return


    if data == "PROCESS_DONE_RECEIVED":

        log(
            "Arduino received PROCESS_DONE."
        )

        return


    if data == "MOTOR_RESTART":

        log(
            "Arduino restarted conveyor."
        )

        publish_component_status(
            COMPONENT_CONVEYOR,
            STATUS_NORMAL,
            None
        )

        return


    if data == "SYSTEM_READY":

        log(
            "Arduino system ready."
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_NORMAL,
            None
        )

        return
        
    if data == "OBJECT_DETECTED":

        log(
            "Arduino IR sensor detected object."
        )

        publish_component_status(
            COMPONENT_IR_SENSOR,
            STATUS_NORMAL,
            None
        )

        return


    if data == "PHOTO":

        log(
            "Arduino PHOTO signal received."
        )

        return


    if data == "BUZZER_START":

        log(
            "Arduino buzzer started."
        )

        return


    if data == "BUZZER_DONE":

        log(
            "Arduino buzzer completed."
        )

        return


    if data.startswith(
        "CHOCOLATE_COUNT:"
    ):

        log(
            f"Arduino chocolate count: {data}"
        )

        return


    if data == "SERVO_0":

        log(
            "Arduino servo position: 0 degrees."
        )

        return


    if data == "SERVO_45":

        log(
            "Arduino servo position: 45 degrees."
        )

        return


    # --------------------------------------------------------
    # Speed Changed
    # --------------------------------------------------------

    if data.startswith(
        "SPEED_CHANGED:"
    ):

        log(
            f"Arduino motor speed changed: {data}"
        )

        publish_component_status(
            COMPONENT_CONVEYOR,
            STATUS_NORMAL,
            None
        )

        return


    # --------------------------------------------------------
    # Speed Error
    # --------------------------------------------------------

    if data.startswith(
        "SPEED_ERROR:"
    ):

        log(
            f"Arduino motor speed error: {data}"
        )

        publish_component_status(
            COMPONENT_CONVEYOR,
            STATUS_ERROR,
            STEPPER_ERROR
        )

        return


    # --------------------------------------------------------
    # IR -> Camera Travel Time
    # --------------------------------------------------------

    if data.startswith(
        "IR_TO_CAMERA_TIME_MS="
    ):

        log(
            f"Arduino camera travel time: {data}"
        )

        return
        
    # --------------------------------------------------------
    # Motor Speed Debug
    # --------------------------------------------------------

    if data.startswith(
        "MOTOR_SPEED_LEVEL="
    ):

        log(
            f"Arduino speed level: {data}"
        )

        return


    if data.startswith(
        "MOTOR_SPEED="
    ):

        log(
            f"Arduino actual motor speed: {data}"
        )

        return


# ============================================================
# Set Conveyor Motor Speed
# ============================================================

def set_motor_speed(level):

    if arduino is None:

        log(
            "Arduino is not connected."
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_OFFLINE,
            SERIAL_DISCONNECTED
        )

        return False


    if (
        level < MOTOR_SPEED_LEVEL_MIN
        or
        level > MOTOR_SPEED_LEVEL_MAX
    ):

        log(
            f"Invalid motor speed level: {level}"
        )

        return False


    try:

        command = (
            SET_SPEED_COMMAND.format(
                level=level
            )
        )


        log(
            "=========================================="
        )

        log(
            f"Setting motor speed level: {level}"
        )


        arduino.write(
            command.encode("utf-8")
        )

        arduino.flush()


        start_time = time.time()


        while (
            time.time() - start_time
            < SPEED_RESPONSE_TIMEOUT
        ):

            data, error = (
                read_arduino_line()
            )


            if error is not None:

                return False


            if not data:

                continue


            log(
                f"Arduino -> Raspberry Pi: "
                f"{data}"
            )


            # ------------------------------------------------
            # Speed change success
            # ------------------------------------------------

            if data.startswith(
                "SPEED_CHANGED:"
            ):

                log(
                    f"Motor speed level "
                    f"{level} confirmed."
                )

                publish_component_status(
                    COMPONENT_CONVEYOR,
                    STATUS_NORMAL,
                    None
                )

                log(
                    "=========================================="
                )

                return True


            # ------------------------------------------------
            # Speed change error
            # ------------------------------------------------

            if data.startswith(
                "SPEED_ERROR:"
            ):

                log(
                    f"Motor speed change failed: "
                    f"{data}"
                )

                publish_component_status(
                    COMPONENT_CONVEYOR,
                    STATUS_ERROR,
                    STEPPER_ERROR
                )

                log(
                    "=========================================="
                )

                return False

            # ------------------------------------------------
            # Other normal Arduino status
            # ------------------------------------------------

            if is_normal_arduino_message(data):

                handle_normal_arduino_status(
                    data
                )

                continue


        log(
            f"Motor speed response timeout: "
            f"level={level}"
        )

        publish_component_status(
            COMPONENT_CONVEYOR,
            STATUS_ERROR,
            SERIAL_TIMEOUT
        )

        return False


    except serial.SerialException as e:

        log(
            f"Arduino serial error: {e}"
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_ERROR,
            SERIAL_ERROR
        )

        return False


    except Exception as e:

        log(
            f"Failed to set motor speed: {e}"
        )

        publish_component_status(
            COMPONENT_CONVEYOR,
            STATUS_ERROR,
            STEPPER_ERROR
        )

        return False


# ============================================================
# Wait for Servo Confirmation
# ============================================================

def wait_for_servo_confirmation(
    expected_response
):

    log(
        f"Waiting for Arduino ACK: "
        f"{expected_response}"
    )

    start_time = time.time()

    while (
        time.time() - start_time
        < SERVO_RESPONSE_TIMEOUT
    ):

        data, error = (
            read_arduino_line()
        )

        if error is not None:

            return False

        if not data:

            continue

        log(
            f"Arduino -> Raspberry Pi: "
            f"{data}"
        )

        # ----------------------------------------------------
        # Expected ACK
        # ----------------------------------------------------

        if data == expected_response:

            log(
                f"Received expected ACK: "
                f"{expected_response}"
            )

            publish_component_status(
                COMPONENT_SERVO,
                STATUS_NORMAL,
                None
            )

            return True
            
        # ----------------------------------------------------
        # Wrong Servo ACK
        # ----------------------------------------------------

        if (
            data == SERVO_0_RESPONSE
            or
            data == SERVO_45_RESPONSE
        ):

            log(
                f"Wrong Servo ACK. "
                f"Expected={expected_response}, "
                f"Received={data}"
            )

            publish_component_status(
                COMPONENT_SERVO,
                STATUS_ERROR,
                SERVO_ACK_ERROR
            )

            return False


        # ----------------------------------------------------
        # Normal Arduino status
        # ----------------------------------------------------

        if is_normal_arduino_message(data):

            handle_normal_arduino_status(data)

            continue


        log(
            f"Unexpected Arduino message: "
            f"{data}"
        )


    log(
        f"Servo ACK timeout: "
        f"{expected_response}"
    )

    publish_component_status(
        COMPONENT_SERVO,
        STATUS_ERROR,
        SERVO_ACK_TIMEOUT
    )

    return False


# ============================================================
# Wait for Buzzer Confirmation
# ============================================================

def wait_for_buzzer_confirmation():

    log(
        "Waiting for Buzzer confirmation..."
    )

    start_time = time.time()

    while (
        time.time() - start_time
        < BUZZER_RESPONSE_TIMEOUT
    ):

        data, error = (
            read_arduino_line()
        )

        if error is not None:

            publish_component_status(
                COMPONENT_BUZZER,
                STATUS_ERROR,
                BUZZER_ERROR
            )

            return False

        if not data:

            continue

        log(
            f"Arduino -> Raspberry Pi: "
            f"{data}"
        )

        if data == BUZZER_START_RESPONSE:

            log(
                "Buzzer started."
            )

            continue

        if data == BUZZER_DONE_RESPONSE:

            log(
                "Buzzer operation completed."
            )

            publish_component_status(
                COMPONENT_BUZZER,
                STATUS_NORMAL,
                None
            )

            return True

        if is_normal_arduino_message(data):

            handle_normal_arduino_status(data)

            continue

        log(
            f"Unexpected Arduino message: "
            f"{data}"
        )

    log(
        "Buzzer response timeout."
    )

    publish_component_status(
        COMPONENT_BUZZER,
        STATUS_ERROR,
        BUZZER_ERROR
    )

    return False


# ============================================================
# Process Chocolate Count
# ============================================================

def process_chocolate_count():

    global chocolate_count

    chocolate_count += 1

    log(
        f"Chocolate count: "
        f"{chocolate_count}/"
        f"{CHOCOLATE_UNIT_PER_SET}"
    )

    if (
        chocolate_count
        >= CHOCOLATE_UNIT_PER_SET
    ):

        log(
            "Chocolate set completed."
        )

        buzzer_command_success = (
            send_buzzer_on()
        )

        if not buzzer_command_success:

            publish_component_status(
                COMPONENT_BUZZER,
                STATUS_ERROR,
                BUZZER_ERROR
            )

            return False

        buzzer_success = (
            wait_for_buzzer_confirmation()
        )

        if not buzzer_success:

            return False

        chocolate_count = 0

        log(
            "Chocolate count reset to 0."
        )

    return True
    
# ============================================================
# Process CHOCO
# ============================================================

def process_choco(
    confidence,
    image_path
):

    log(
        "Chocolate detected."
    )

    log(
        "Activating servo to 0 degrees..."
    )

    command_success = (
        send_choco_command()
    )

    if not command_success:

        return create_result(
            status="FAILED",
            result_type="CHOCO",
            confidence=confidence,
            image_path=image_path,
            error_type="HW",
            error_code=ARDUINO_ERROR
        )

    servo_success = (
        wait_for_servo_confirmation(
            SERVO_0_RESPONSE
        )
    )

    if not servo_success:

        return create_result(
            status="FAILED",
            result_type="CHOCO",
            confidence=confidence,
            image_path=image_path,
            error_type="HW",
            error_code=SERVO_ACK_TIMEOUT
        )

    log(
        "CHOCO servo operation confirmed."
    )

    production_success = (
        process_chocolate_count()
    )

    if not production_success:

        log(
            "Buzzer operation failed."
        )

        return create_result(
            status="FAILED",
            result_type="CHOCO",
            confidence=confidence,
            image_path=image_path,
            error_type="HW",
            error_code=BUZZER_ERROR
        )

    return create_result(
        status="SUCCESS",
        result_type="CHOCO",
        confidence=confidence,
        image_path=image_path
    )


# ============================================================
# Process CANDY
# ============================================================

def process_candy(
    confidence,
    image_path
):

    log(
        "Candy detected."
    )

    log(
        "Activating servo to 45 degrees..."
    )

    command_success = (
        send_candy_command()
    )

    if not command_success:

        return create_result(
            status="FAILED",
            result_type="CANDY",
            confidence=confidence,
            image_path=image_path,
            error_type="HW",
            error_code=ARDUINO_ERROR
        )

    servo_success = (
        wait_for_servo_confirmation(
            SERVO_45_RESPONSE
        )
    )

    if not servo_success:

        return create_result(
            status="FAILED",
            result_type="CANDY",
            confidence=confidence,
            image_path=image_path,
            error_type="HW",
            error_code=SERVO_ACK_TIMEOUT
        )

    log(
        "CANDY servo operation confirmed."
    )

    return create_result(
        status="SUCCESS",
        result_type="CANDY",
        confidence=confidence,
        image_path=image_path
    )
    
# ============================================================
# Initialize MQTT
# ============================================================

log(
    "Initializing MQTT before hardware/model..."
)


mqtt_initialized = (
    initialize_mqtt()
)


# ============================================================
# MQTT Initial State
# ============================================================

if mqtt_initialized:

    publish_component_status(
        COMPONENT_CAMERA,
        STATUS_NORMAL,
        None
    )

    publish_component_status(
        COMPONENT_CONVEYOR,
        STATUS_NORMAL,
        None
    )

    publish_component_status(
        COMPONENT_ARDUINO,
        STATUS_NORMAL,
        None
    )

    publish_component_status(
        COMPONENT_IR_SENSOR,
        STATUS_NORMAL,
        None
    )

    publish_component_status(
        COMPONENT_SERVO,
        STATUS_NORMAL,
        None
    )

    publish_component_status(
        COMPONENT_BUZZER,
        STATUS_NORMAL,
        None
    )

else:

    log(
        "MQTT is unavailable."
    )

    log(
        "Sorting system will continue "
        "without MQTT."
    )


# ============================================================
# Initialize YOLO
# ============================================================

log(
    "Loading YOLO model..."
)


try:

    model = YOLO(
        MODEL_PATH
    )

except Exception as e:

    log(
        f"YOLO model loading failed: {e}"
    )

    publish_component_status(
        COMPONENT_CAMERA,
        STATUS_ERROR,
        MODEL_LOAD_ERROR
    )

    publish_product_detection(
        classification_status="FAILED",
        product_type_code=None,
        confidence=0.00,
        image_path=None
    )

    raise


log(
    "YOLO model loaded."
)


log(
    f"Model classes: {model.names}"
)


# ============================================================
# Validate YOLO Class Names
# ============================================================

try:

    available_class_names = []

    if isinstance(model.names, dict):

        available_class_names = [
            normalize_class_name(name)
            for name in model.names.values()
        ]

    elif isinstance(model.names, list):

        available_class_names = [
            normalize_class_name(name)
            for name in model.names
        ]

    log(
        f"Normalized model classes: "
        f"{available_class_names}"
    )

    if (
        YOLO_CANDY_CLASS_NAME
        not in available_class_names
        or
        YOLO_CHOCOLATE_CLASS_NAME
        not in available_class_names
    ):

        log(
            "WARNING: Expected product class names "
            "were not found in YOLO model."
        )

except Exception as e:

    log(
        f"YOLO class validation warning: {e}"
    )
    
# ============================================================
# Initialize Camera
# ============================================================

log(
    "Initializing camera..."
)


try:

    picam2 = Picamera2()

    camera_config = (
        picam2.create_preview_configuration(
            main={
                "size": (
                    CAMERA_WIDTH,
                    CAMERA_HEIGHT
                )
            }
        )
    )

    picam2.configure(
        camera_config
    )

    picam2.start()

    time.sleep(2)

except Exception as e:

    log(
        f"Camera initialization failed: {e}"
    )

    publish_component_status(
        COMPONENT_CAMERA,
        STATUS_ERROR,
        CAMERA_ERROR
    )

    raise


log(
    f"Camera ready: "
    f"{CAMERA_WIDTH}x{CAMERA_HEIGHT}"
)


# ============================================================
# Connect Arduino
# ============================================================

log(
    "Connecting to Arduino..."
)


try:

    arduino = serial.Serial(
        ARDUINO_PORT,
        BAUD_RATE,
        timeout=0.1
    )

    time.sleep(2)

    arduino.reset_input_buffer()

except serial.SerialException as e:

    log(
        f"Arduino connection failed: {e}"
    )

    publish_component_status(
        COMPONENT_ARDUINO,
        STATUS_OFFLINE,
        SERIAL_DISCONNECTED
    )

    raise

except OSError as e:

    log(
        f"Arduino OS connection error: {e}"
    )

    publish_component_status(
        COMPONENT_ARDUINO,
        STATUS_OFFLINE,
        SERIAL_DISCONNECTED
    )

    raise

except Exception as e:

    log(
        f"Arduino connection failed: {e}"
    )

    publish_component_status(
        COMPONENT_ARDUINO,
        STATUS_ERROR,
        SERIAL_ERROR
    )

    raise


log(
    "Arduino connected."
)


publish_component_status(
    COMPONENT_ARDUINO,
    STATUS_NORMAL,
    None
)


# ============================================================
# Set Initial Motor Speed
# ============================================================

log(
    "Setting initial motor speed..."
)


speed_initialized = (
    set_motor_speed(
        MOTOR_SPEED_LEVEL
    )
)


if speed_initialized:

    log(
        f"Initial motor speed level "
        f"{MOTOR_SPEED_LEVEL} configured."
    )

else:

    log(
        "WARNING: Failed to configure initial motor speed."
    )


# ============================================================
# Waiting
# ============================================================

log(
    "Waiting for object detection..."
)


# ============================================================
# Photo Number
# ============================================================

photo_number = (
    get_next_photo_number()
)


# ============================================================
# Main Loop
# ============================================================

try:

    while True:

        # ====================================================
        # Read Arduino Serial
        # ====================================================

        data, error = (
            read_arduino_line()
        )

        if error is not None:

            if error == SERIAL_DISCONNECTED:

                publish_component_status(
                    COMPONENT_ARDUINO,
                    STATUS_OFFLINE,
                    SERIAL_DISCONNECTED
                )

            time.sleep(1)

            continue

        if not data:

            continue

        log(
            f"Arduino -> Raspberry Pi: "
            f"{data}"
        )


        # ====================================================
        # SYSTEM_READY
        # ====================================================

        if data == SYSTEM_READY_RESPONSE:

            handle_normal_arduino_status(
                data
            )

            continue
            
        # ====================================================
        # OBJECT_DETECTED
        # ====================================================

        if data == OBJECT_DETECTED_RESPONSE:

            handle_normal_arduino_status(
                data
            )

            continue


        # ====================================================
        # PHOTO
        # ====================================================

        if data == PHOTO_RESPONSE:

            log(
                "PHOTO signal received."
            )


            # =================================================
            # Filename
            # =================================================

            filename = (
                f"photo_{photo_number:03d}.jpg"
            )

            filepath = os.path.join(
                PHOTO_DIR,
                filename
            )

            log(
                f"Local image path: {filepath}"
            )


            # =================================================
            # Capture Image
            # =================================================

            try:

                log(
                    "Camera capture started."
                )

                frame = (
                    picam2.capture_array()
                )

                if frame is None:

                    raise Exception(
                        "Captured frame is None."
                    )

            except Exception as e:

                log(
                    "Camera capture failed."
                )

                log(
                    f"Camera error: {e}"
                )

                publish_product_detection(
                    classification_status="FAILED",
                    product_type_code=None,
                    confidence=0.00,
                    image_path=None
                )

                publish_component_status(
                    COMPONENT_CAMERA,
                    STATUS_ERROR,
                    CAMERA_ERROR
                )

                result = create_result(
                    status="FAILED",
                    result_type="NULL",
                    confidence=0.00,
                    image_path=None,
                    error_type="HW",
                    error_code=CAMERA_ERROR
                )

                print_result(result)

                send_process_done()

                photo_number += 1

                continue


            # =================================================
            # Check Resolution
            # =================================================

            height, width = (
                frame.shape[:2]
            )

            log(
                f"Captured image size: "
                f"{width}x{height}"
            )
            
            # =================================================
            # Save Image
            # =================================================

            try:

                success = cv2.imwrite(
                    filepath,
                    frame
                )

            except Exception as e:

                log(
                    "Image save failed."
                )

                log(
                    f"Image save error: {e}"
                )

                success = False

            if not success:

                publish_product_detection(
                    classification_status="FAILED",
                    product_type_code=None,
                    confidence=0.00,
                    image_path=None
                )

                publish_component_status(
                    COMPONENT_CAMERA,
                    STATUS_ERROR,
                    IMAGE_SAVE_ERROR
                )

                result = create_result(
                    status="FAILED",
                    result_type="NULL",
                    confidence=0.00,
                    image_path=None,
                    error_type="SW",
                    error_code=IMAGE_SAVE_ERROR
                )

                print_result(result)

                send_process_done()

                photo_number += 1

                continue


            log(
                "Photo captured successfully."
            )

            log(
                f"Image saved: {filepath}"
            )


            # =================================================
            # Upload Image
            # =================================================

            image_path, upload_error = (
                upload_image_to_server(
                    filepath
                )
            )

            image_upload_success = (
                image_path is not None
            )

            if not image_upload_success:

                log(
                    "WARNING: Image upload failed."
                )

                log(
                    "YOLO classification will continue."
                )

                log(
                    f"Upload error code: "
                    f"{upload_error}"
                )

                publish_component_status(
                    COMPONENT_CAMERA,
                    STATUS_WARNING,
                    IMAGE_UPLOAD_FAILED
                )

            else:

                log(
                    "Server imagePath received successfully."
                )

                log(
                    f"imagePath = {image_path}"
                )


            # =================================================
            # YOLO Inference
            # =================================================

            log(
                "YOLO detection started."
            )

            try:

                results = model(
                    filepath,
                    verbose=True
                )

            except Exception as e:

                log(
                    "YOLO inference failed."
                )

                log(
                    f"YOLO error: {e}"
                )

                publish_component_status(
                    COMPONENT_CAMERA,
                    STATUS_ERROR,
                    YOLO_ERROR
                )

                publish_product_detection(
                    classification_status="FAILED",
                    product_type_code=None,
                    confidence=0.00,
                    image_path=image_path
                )

                result = create_result(
                    status="FAILED",
                    result_type="NULL",
                    confidence=0.00,
                    image_path=image_path,
                    error_type="SW",
                    error_code=YOLO_ERROR
                )

                print_result(result)

                send_process_done()

                photo_number += 1

                continue
                
            # =================================================
            # Find Best Detection
            # =================================================

            best_class_id = None
            best_class_name = None
            best_confidence = 0.0

            for detection_result in results:

                if detection_result.boxes is None:

                    continue

                for box in detection_result.boxes:

                    class_id = int(
                        box.cls[0].item()
                    )

                    confidence = float(
                        box.conf[0].item()
                    )

                    if (
                        confidence
                        > best_confidence
                    ):

                        best_confidence = (
                            confidence
                        )

                        best_class_id = (
                            class_id
                        )

                        best_class_name = (
                            get_yolo_class_name(
                                class_id
                            )
                        )


            # =================================================
            # No Detection
            # =================================================

            if best_class_name is None:

                log(
                    "No object detected by YOLO."
                )

                publish_product_detection(
                    classification_status="FAILED",
                    product_type_code=None,
                    confidence=0.00,
                    image_path=image_path
                )

                publish_component_status(
                    COMPONENT_CAMERA,
                    STATUS_WARNING,
                    NO_DETECTION
                )

                result = create_result(
                    status="FAILED",
                    result_type="NULL",
                    confidence=0.00,
                    image_path=image_path,
                    error_type=None,
                    error_code=NO_DETECTION
                )

                print_result(result)

                send_process_done()

                photo_number += 1

                continue


            # =================================================
            # Log YOLO Result
            # =================================================

            log(
                f"YOLO class ID: "
                f"{best_class_id}"
            )

            log(
                f"YOLO class name: "
                f"{best_class_name}"
            )

            log(
                f"YOLO confidence: "
                f"{best_confidence:.2f}"
            )


            # =================================================
            # Confidence Check
            # =================================================

            if (
                best_confidence
                <= CONFIDENCE_THRESHOLD
            ):

                log(
                    "Confidence is 0.70 or lower."
                )

                log(
                    "Classification result: NULL"
                )

                publish_product_detection(
                    classification_status="FAILED",
                    product_type_code=None,
                    confidence=best_confidence,
                    image_path=image_path
                )

                result = create_result(
                    status="FAILED",
                    result_type="NULL",
                    confidence=best_confidence,
                    image_path=image_path,
                    error_type=None,
                    error_code=None
                )

                print_result(result)

                send_process_done()

                photo_number += 1

                continue
                
            # =================================================
            # Class Classification
            # =================================================

            final_type, mqtt_product_type = (
                convert_yolo_class_to_product_type(
                    best_class_name
                )
            )


            # =================================================
            # Unknown Class
            # =================================================

            if final_type is None:

                log(
                    f"Unknown YOLO class: "
                    f"{best_class_name}"
                )

                publish_component_status(
                    COMPONENT_CAMERA,
                    STATUS_ERROR,
                    UNKNOWN_CLASS
                )

                publish_product_detection(
                    classification_status="FAILED",
                    product_type_code=None,
                    confidence=best_confidence,
                    image_path=image_path
                )

                result = create_result(
                    status="FAILED",
                    result_type="NULL",
                    confidence=best_confidence,
                    image_path=image_path,
                    error_type="SW",
                    error_code=UNKNOWN_CLASS
                )

                print_result(result)

                send_process_done()

                photo_number += 1

                continue

            # =================================================
            # Final Classification Candidate
            # =================================================

            log(
                f"FINAL CLASSIFICATION CANDIDATE: "
                f"{final_type}"
            )

            log(
                f"MQTT PRODUCT TYPE: "
                f"{mqtt_product_type}"
            )


            # =================================================
            # Hardware Processing
            # =================================================

            if final_type == "CHOCO":

                result = process_choco(
                    confidence=best_confidence,
                    image_path=image_path
                )

            elif final_type == "CANDY":

                result = process_candy(
                    confidence=best_confidence,
                    image_path=image_path
                )

            else:

                result = create_result(
                    status="FAILED",
                    result_type="NULL",
                    confidence=best_confidence,
                    image_path=image_path,
                    error_type="SW",
                    error_code=UNKNOWN_CLASS
                )


            # =================================================
            # Final Result
            # =================================================

            print_result(result)


            # =================================================
            # MQTT Final Classification Result
            # =================================================

            if result["status"] == "SUCCESS":

                classification_status = "SUCCESS"

            else:

                classification_status = "FAILED"


            vision_publish_success = (
                publish_product_detection(
                    classification_status=classification_status,
                    product_type_code=(
                        mqtt_product_type
                        if classification_status == "SUCCESS"
                        else None
                    ),
                    confidence=best_confidence,
                    image_path=image_path
                )
            )


            if not vision_publish_success:

                log(
                    "Product detection MQTT publish failed."
                )

                publish_component_status(
                    COMPONENT_DISPLAY,
                    STATUS_WARNING,
                    DATA_SEND_ERROR
                )


            # =================================================
            # Processing Complete
            # =================================================

            send_process_done()
            
            # =================================================
            # Next Image Number
            # =================================================

            photo_number += 1

            continue


        # ====================================================
        # Normal Arduino Status Messages
        # ====================================================

        if is_normal_arduino_message(data):

            handle_normal_arduino_status(
                data
            )

            continue


        # ====================================================
        # Unknown Arduino Message
        # ====================================================

        log(
            f"Unknown Arduino message: "
            f"{data}"
        )

        publish_component_status(
            COMPONENT_ARDUINO,
            STATUS_ERROR,
            UNKNOWN_COMMAND
        )


# ============================================================
# Program Termination
# ============================================================

except KeyboardInterrupt:

    log(
        "Program stopped by user."
    )


except Exception as e:

    log(
        f"Program error: {e}"
    )

    publish_component_status(
        COMPONENT_ARDUINO,
        STATUS_ERROR,
        ARDUINO_ERROR
    )


finally:

    log(
        "Closing camera, Arduino and MQTT connection..."
    )


    # --------------------------------------------------------
    # Camera
    # --------------------------------------------------------

    try:

        if picam2 is not None:

            picam2.stop()

    except Exception:

        pass
        
    # --------------------------------------------------------
    # Arduino
    # --------------------------------------------------------

    try:

        if arduino is not None:

            arduino.close()

    except Exception:

        pass


    # --------------------------------------------------------
    # MQTT
    # --------------------------------------------------------

    try:

        if mqtt_client is not None:

            if mqtt_connected:

                mqtt_client.disconnect()

            mqtt_client.loop_stop()

    except Exception:

        pass


    log(
        "Program terminated."
    )
