import sys

import requests

import socket

import serial

import json



from PyQt5 import uic

from PyQt5.QtCore import Qt, QTimer



from PyQt5.QtWidgets import (

    QApplication,

    QMainWindow,

    QMessageBox,

    QLineEdit,

    QDialog,

    QGridLayout,

    QPushButton,

    QVBoxLayout,

    QHBoxLayout

)



# 기존 메인 HMI

from main import MainWindow





# ============================================================

# 서버 설정

# ============================================================



API_BASE_URL = "http://210.119.12.62:5051"





# ============================================================

# ESP32 Worker Display 설정

# ============================================================



ESP32_PORT = "/dev/ttyUSB0"

ESP32_BAUDRATE = 115200





class ESP32Display:

    """

    Raspberry Pi <-> ESP32-2432S028 Serial 통신

    """



    def __init__(self):

        self.ser = None



        try:

            self.ser = serial.Serial(

                ESP32_PORT,

                ESP32_BAUDRATE,

                timeout=1

            )



            print("================================")

            print("ESP32 Worker Display 연결 성공")

            print(f"Port : {ESP32_PORT}")

            print(f"Baud : {ESP32_BAUDRATE}")

            print("================================")



        except Exception as e:

            print("================================")

            print("ESP32 Worker Display 연결 실패")

            print(e)

            print("================================")



            self.ser = None

            

    def send(self, message):

        """

        ESP32로 한 줄 전송

        """



        if self.ser is None:

            print(f"ESP32 전송 실패 - 연결 안됨 : {message}")

            return False



        try:

            data = message.strip() + "\n"



            self.ser.write(

                data.encode("utf-8")

            )



            self.ser.flush()



            print(f"ESP32 TX : {message}")



            return True



        except Exception as e:

            print(f"ESP32 Serial 전송 오류 : {e}")



            return False



    def show_login(self):

        self.send("SCREEN:LOGIN")



    def login_success(self, user_name):

        self.send(

            f"LOGIN:{user_name}"

        )



    def show_worker(self):

        self.send("WORKER")



    def send_status(self, status):

        self.send(

            f"STATUS:{status}"

        )



    def send_production(

        self,

        chocolate_current,

        chocolate_target,

        chocolate_set,

        chocolate_progress,

        candy_current,

        candy_target,

        candy_set,

        candy_progress

    ):

        """

        생산 현황 전송



        예:

        PRODUCTION:

        10,100,1,10,

        5,50,5,10

        """



        message = (

            "PRODUCTION:"

            f"{chocolate_current},"

            f"{chocolate_target},"

            f"{chocolate_set},"

            f"{chocolate_progress},"

            f"{candy_current},"

            f"{candy_target},"

            f"{candy_set},"

            f"{candy_progress}"

        )



        self.send(message)



    def close(self):

        if self.ser is not None:



            try:

                self.ser.close()



            except Exception:

                pass



            self.ser = None

            

# ============================================================

# 숫자 키패드

# ============================================================



class NumericKeypad(QDialog):



    def __init__(

        self,

        current_value="",

        password_mode=False,

        parent=None

    ):



        super().__init__(parent)



        self.setWindowTitle("숫자 입력")

        self.setFixedSize(360, 500)

        self.setModal(True)



        self.setStyleSheet("""

            QDialog {

                background-color: #F7F9FA;

            }



            QLineEdit {

                background-color: white;

                border: 2px solid #B8C5C8;

                border-radius: 8px;

                padding: 8px;

                font-size: 28px;

                font-weight: bold;

            }



            QPushButton {

                background-color: white;

                border: 1px solid #C5D0D2;

                border-radius: 8px;

                font-size: 24px;

                font-weight: bold;

            }



            QPushButton:pressed {

                background-color: #DDEBED;

            }



            QPushButton#btnConfirm {

                background-color: #3E8E93;

                color: white;

                border: none;

            }



            QPushButton#btnCancel {

                background-color: #E8ECEE;

                color: #333333;

            }

        """)



        self.input = QLineEdit()



        self.input.setReadOnly(True)

        self.input.setFixedHeight(65)



        self.input.setText(

            current_value

        )



        self.input.setAlignment(

            Qt.AlignCenter

        )



        if password_mode:



            self.input.setEchoMode(

                QLineEdit.Password

            )



        grid = QGridLayout()



        grid.setSpacing(8)



        number_buttons = [



            ("1", 0, 0),

            ("2", 0, 1),

            ("3", 0, 2),



            ("4", 1, 0),

            ("5", 1, 1),

            ("6", 1, 2),



            ("7", 2, 0),

            ("8", 2, 1),

            ("9", 2, 2),



            ("지우기", 3, 0),

            ("0", 3, 1),

            ("←", 3, 2)

        ]



        for text, row, col in number_buttons:



            button = QPushButton(text)



            button.setMinimumSize(

                95,

                65

            )



            button.setFocusPolicy(

                Qt.NoFocus

            )



            if text.isdigit():



                button.clicked.connect(

                    lambda checked,

                    n=text:

                    self.add_number(n)

                )



            elif text == "←":



                button.clicked.connect(

                    self.delete_number

                )



            elif text == "지우기":



                button.clicked.connect(

                    self.clear_number

                )



            grid.addWidget(

                button,

                row,

                col

            )



        self.btnCancel = QPushButton("취소")



        self.btnCancel.setObjectName(

            "btnCancel"

        )



        self.btnCancel.setMinimumHeight(

            60

        )

        

        self.btnCancel.setFocusPolicy(

            Qt.NoFocus

        )



        self.btnCancel.clicked.connect(

            self.reject

        )



        self.btnConfirm = QPushButton("확인")



        self.btnConfirm.setObjectName(

            "btnConfirm"

        )



        self.btnConfirm.setMinimumHeight(

            60

        )



        self.btnConfirm.setFocusPolicy(

            Qt.NoFocus

        )



        self.btnConfirm.clicked.connect(

            self.accept

        )



        bottom_layout = QHBoxLayout()



        bottom_layout.setSpacing(8)



        bottom_layout.addWidget(

            self.btnCancel

        )



        bottom_layout.addWidget(

            self.btnConfirm

        )



        layout = QVBoxLayout()



        layout.setContentsMargins(

            15,

            15,

            15,

            15

        )



        layout.setSpacing(10)



        layout.addWidget(

            self.input

        )



        layout.addLayout(

            grid

        )



        layout.addLayout(

            bottom_layout

        )



        self.setLayout(

            layout

        )



    def add_number(self, number):



        if len(self.input.text()) < 10:



            self.input.setText(

                self.input.text() + number

            )



    def delete_number(self):



        self.input.setText(

            self.input.text()[:-1]

        )



    def clear_number(self):



        self.input.clear()



    def get_value(self):



        return self.input.text()

        

# ============================================================

# Login Window

# ============================================================



class LoginWindow(QMainWindow):



    def __init__(self):



        super().__init__()



        # ----------------------------------------------------

        # ESP32 LCD 연결

        # ----------------------------------------------------



        self.esp32 = ESP32Display()



        # ----------------------------------------------------

        # Login UI

        # ----------------------------------------------------



        uic.loadUi(

            "ui/login.ui",

            self

        )



        # 직접 키보드 입력 방지



        self.txtLoginId.setReadOnly(

            True

        )



        self.txtPassword.setReadOnly(

            True

        )



        self.txtLoginId.setFocusPolicy(

            Qt.NoFocus

        )



        self.txtPassword.setFocusPolicy(

            Qt.NoFocus

        )



        # 입력창 터치 → 숫자 키패드



        self.txtLoginId.mousePressEvent = (

            self.open_login_id_keypad

        )



        self.txtPassword.mousePressEvent = (

            self.open_password_keypad

        )



        self.txtPassword.setEchoMode(

            QLineEdit.Password

        )



        # 로그인 버튼



        self.btnLogin.clicked.connect(

            self.login

        )



        # 로그인 정보



        self.token = None

        self.user_id = None

        self.user_name = None

        self.user_role = None

        

        # 생산 세션



        self.session_id = None

        self.current_session = None



        # ----------------------------------------------------

        # 네트워크 상태

        # ----------------------------------------------------



        self.lblWifiStatus.setText(

            "Wi-Fi 확인 중"

        )



        self.lblServerStatus.setText(

            "서버 확인 중"

        )



        self.lblWifiIcon.setStyleSheet(

            "background-color: #9CA3AF;"

            "border-radius: 6px;"

        )



        self.lblServerIcon.setStyleSheet(

            "background-color: #9CA3AF;"

            "border-radius: 6px;"

        )



        # ----------------------------------------------------

        # ESP32 로그인 화면 표시

        # ----------------------------------------------------



        self.esp32.show_login()



        # ----------------------------------------------------

        # 연결 확인

        # ----------------------------------------------------



        self.check_connection_status()



        self.network_timer = QTimer(

            self

        )



        self.network_timer.timeout.connect(

            self.check_connection_status

        )



        self.network_timer.start(

            5000

        )



    # ========================================================

    # Numeric Keypad

    # ========================================================



    def open_login_id_keypad(

        self,

        event

    ):



        keypad = NumericKeypad(

            current_value=self.txtLoginId.text(),

            password_mode=False,

            parent=self

        )



        if keypad.exec_() == QDialog.Accepted:



            self.txtLoginId.setText(

                keypad.get_value()

            )

            

    def open_password_keypad(

        self,

        event

    ):



        keypad = NumericKeypad(

            current_value=self.txtPassword.text(),

            password_mode=True,

            parent=self

        )



        if keypad.exec_() == QDialog.Accepted:



            self.txtPassword.setText(

                keypad.get_value()

            )



    # ========================================================

    # Network

    # ========================================================



    def check_connection_status(self):



        network_ok = False



        try:



            socket.create_connection(

                (

                    "210.119.12.62",

                    5051

                ),

                timeout=2

            ).close()



            network_ok = True



        except OSError:



            network_ok = False



        # REST 서버



        server_ok = False



        if network_ok:



            try:



                requests.get(

                    f"{API_BASE_URL}/",

                    timeout=2

                )



                server_ok = True



            except requests.exceptions.RequestException:



                server_ok = False



        # Wi-Fi



        if network_ok:



            self.lblWifiStatus.setText(

                "Wi-Fi 연결됨"

            )



            self.lblWifiIcon.setStyleSheet(

                "background-color: #22C55E;"

                "border-radius: 6px;"

            )



        else:



            self.lblWifiStatus.setText(

                "Wi-Fi 연결 안됨"

            )



            self.lblWifiIcon.setStyleSheet(

                "background-color: #EF4444;"

                "border-radius: 6px;"

            )



        # Server



        if server_ok:



            self.lblServerStatus.setText(

                "서버 연결됨"

            )



            self.lblServerIcon.setStyleSheet(

                "background-color: #22C55E;"

                "border-radius: 6px;"

            )



            self.btnLogin.setEnabled(

                True

            )



            # ESP32에도 서버 연결 상태 전달



            self.esp32.send_status(

                "SERVER_OK"

            )

            

        else:



            self.lblServerStatus.setText(

                "서버 연결 안됨"

            )



            self.lblServerIcon.setStyleSheet(

                "background-color: #EF4444;"

                "border-radius: 6px;"

            )



            self.btnLogin.setEnabled(

                False

            )



            self.esp32.send_status(

                "SERVER_ERROR"

            )



    # ========================================================

    # Login

    # ========================================================



    def login(self):



        login_id = (

            self.txtLoginId.text().strip()

        )



        password = (

            self.txtPassword.text()

        )



        if not login_id or not password:



            QMessageBox.warning(

                self,

                "로그인",

                "아이디와 비밀번호를 입력해 주세요."

            )



            return



        self.btnLogin.setEnabled(

            False

        )



        # ESP32 로그인 진행 표시



        self.esp32.send(

            "STATUS:LOGIN"

        )



        url = (

            f"{API_BASE_URL}"

            "/api/auth/login"

        )



        data = {



            "loginId": login_id,



            "password": password

        }



        try:



            response = requests.post(

                url,

                json=data,

                timeout=5

            )



            if response.status_code == 200:



                result = response.json()



                self.token = result[

                    "token"

                ]



                self.user_id = result[

                    "userId"

                ]

                

                self.user_name = result[

                    "name"

                ]



                self.user_role = result[

                    "role"

                ]



                print("로그인 성공")

                print(

                    "사용자:",

                    self.user_name

                )



                print(

                    "역할:",

                    self.user_role

                )



                # ESP32 로그인 성공 표시



                self.esp32.login_success(

                    self.user_name

                )



                # 생산 세션 조회



                self.get_current_session()



            else:



                self.btnLogin.setEnabled(

                    True

                )



                self.esp32.send(

                    "STATUS:LOGIN_FAILED"

                )



                print(

                    f"로그인 실패 : "

                    f"{response.status_code} / "

                    f"{response.text}"

                )



                QMessageBox.warning(

                    self,

                    "로그인 실패",

                    "아이디 또는 비밀번호를 확인해 주세요."

                )



        except requests.exceptions.ConnectionError:



            self.btnLogin.setEnabled(

                True

            )



            self.esp32.send(

                "STATUS:SERVER_ERROR"

            )



            QMessageBox.critical(

                self,

                "서버 연결 실패",

                "서버에 연결할 수 없습니다."

            )



        except requests.exceptions.Timeout:



            self.btnLogin.setEnabled(

                True

            )



            self.esp32.send(

                "STATUS:TIMEOUT"

            )



            QMessageBox.critical(

                self,

                "서버 응답 없음",

                "서버 응답 시간이 초과되었습니다."

            )



        except Exception as e:



            self.btnLogin.setEnabled(

                True

            )



            print(

                f"로그인 처리 오류 : {e}"

            )



            QMessageBox.critical(

                self,

                "오류",

                "로그인 처리 중 오류가 발생했습니다."

            )

            

    # ========================================================

    # Current Production Session

    # ========================================================



    def get_current_session(self):



        url = (

            f"{API_BASE_URL}"

            "/api/production-sessions/current"

        )



        headers = {



            "Authorization":

            f"Bearer {self.token}"

        }



        try:



            response = requests.get(

                url,

                headers=headers,

                timeout=5

            )



            print(

                "현재 생산 세션 조회:",

                response.status_code

            )



            print(

                response.text

            )



            if response.status_code == 200:



                session = response.json()



                self.current_session = (

                    session

                )



                self.session_id = (

                    session["sessionId"]

                )



                print(

                    "현재 생산 세션 사용"

                )



                print(

                    "세션 ID:",

                    self.session_id

                )



                self.open_main_window()



            elif response.status_code == 404:



                print(

                    "현재 생산 세션 없음"

                )



                self.start_production_session()



            else:



                self.btnLogin.setEnabled(

                    True

                )



                self.esp32.send(

                    "STATUS:SESSION_ERROR"

                )



                QMessageBox.warning(

                    self,

                    "생산 작업 조회 실패",

                    "현재 생산 작업을 확인할 수 없습니다."

                )



        except requests.exceptions.ConnectionError:



            self.btnLogin.setEnabled(

                True

            )



            self.esp32.send(

                "STATUS:SERVER_ERROR"

            )



            QMessageBox.critical(

                self,

                "서버 연결 실패",

                "생산 작업 정보를 불러올 수 없습니다."

            )



        except requests.exceptions.Timeout:



            self.btnLogin.setEnabled(

                True

            )

            

            self.esp32.send(

                "STATUS:TIMEOUT"

            )



            QMessageBox.critical(

                self,

                "서버 응답 없음",

                "생산 작업 조회 시간이 초과되었습니다."

            )



        except Exception as e:



            self.btnLogin.setEnabled(

                True

            )



            print(

                f"생산 세션 조회 오류 : {e}"

            )



            QMessageBox.critical(

                self,

                "오류",

                "생산 작업 조회 중 오류가 발생했습니다."

            )



    # ========================================================

    # Start Production Session

    # ========================================================



    def start_production_session(self):



        url = (

            f"{API_BASE_URL}"

            "/api/production-sessions/start"

        )



        headers = {



            "Authorization":

            f"Bearer {self.token}"

        }



        try:



            response = requests.post(

                url,

                headers=headers,

                timeout=5

            )



            print(

                "생산 세션 시작:",

                response.status_code

            )



            print(

                response.text

            )



            if 200 <= response.status_code < 300:



                session = response.json()



                self.current_session = (

                    session

                )



                self.session_id = (

                    session["sessionId"]

                )



                print(

                    "새 생산 세션 생성"

                )



                print(

                    "세션 ID:",

                    self.session_id

                )



                self.open_main_window()



            else:



                self.btnLogin.setEnabled(

                    True

                )



                self.esp32.send(

                    "STATUS:SESSION_ERROR"

                )



                QMessageBox.warning(

                    self,

                    "생산 작업 시작 실패",

                    "생산 작업을 시작할 수 없습니다."

                )

                

        except requests.exceptions.ConnectionError:



            self.btnLogin.setEnabled(

                True

            )



            QMessageBox.critical(

                self,

                "서버 연결 실패",

                "생산 작업을 시작할 수 없습니다."

            )



        except requests.exceptions.Timeout:



            self.btnLogin.setEnabled(

                True

            )



            QMessageBox.critical(

                self,

                "서버 응답 없음",

                "생산 작업 시작 요청 시간이 초과되었습니다."

            )



        except Exception as e:



            self.btnLogin.setEnabled(

                True

            )



            print(

                f"생산 세션 시작 오류 : {e}"

            )



            QMessageBox.critical(

                self,

                "오류",

                "생산 작업 시작 중 오류가 발생했습니다."

            )



    # ========================================================

    # Open Main Window

    # ========================================================



    def open_main_window(self):



        # ESP32를 작업자 화면으로 변경



        self.esp32.show_worker()



        # 기존 Raspberry Pi 화면



        self.main_window = MainWindow(



            user_name=self.user_name,



            session=self.current_session,



            token=self.token,



            logout_callback=self.return_to_login,



            esp32_display=self.esp32



        )



        self.main_window.showFullScreen()



        self.hide()

        

    # ========================================================

    # Return Login

    # ========================================================



    def return_to_login(self):



        self.token = None

        self.user_id = None

        self.user_name = None

        self.user_role = None

        self.session_id = None

        self.current_session = None



        self.btnLogin.setEnabled(

            True

        )



        self.txtLoginId.clear()

        self.txtPassword.clear()



        # ESP32 로그인 화면 복귀



        self.esp32.show_login()



        self.show()



    # ========================================================

    # Close

    # ========================================================



    def closeEvent(self, event):



        print(

            "Login 프로그램 종료"

        )



        self.esp32.close()



        event.accept()





# ============================================================

# Main

# ============================================================



if __name__ == "__main__":



    app = QApplication(

        sys.argv

    )



    window = LoginWindow()



    window.showFullScreen()



    sys.exit(

        app.exec_()

    )

