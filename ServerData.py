# previous code with sejal ui
from sre_constants import error

import can
import time
from PyQt5.QtCore import QTimer
import binascii
import serial
import sys
import requests
import datetime
import pandas as pd
from datetime import datetime, timedelta, timezone
from finalTesting import Ui_FinalTestingUtility
import resources_rc
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QFileDialog, QSizePolicy
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QDateTime
from openpyxl import Workbook, load_workbook
from PyQt5.QtGui import QCursor
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QIcon
from CAN_data import CAN_Data
from PyQt5.QtCore import QPoint
from openpyxl.styles import Alignment, Font, PatternFill
import logging
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import QThread, pyqtSignal


# from mainwindow import Ui_MainWindow
class TimerThread(QThread):
    # Signal to update the UI with the elapsed time
    update_time_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.elapsed_time = 0

    def run(self):
        while True:
            QThread.sleep(1)  # Sleep for 1 second
            self.elapsed_time += 1

            # Calculate hours, minutes, seconds
            hours, remainder = divmod(self.elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

            # Emit the signal to update the UI
            self.update_time_signal.emit(formatted_time)


class MyClass(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_FinalTestingUtility()
        self.ui.setupUi(self)
        self.CANdata_obj = CAN_Data(self.ui)

        screen = QApplication.primaryScreen()
        screen_size = screen.size()

        # Load the image
        logo = QPixmap("AEPL_Logo.png")  # replace with your image file
        # Create a QLabel widget to display the image
        label = self.ui.label_19
        label.setPixmap(logo)

        # Set the window size based on screen resolution (100% of screen size)
        self.setGeometry(0, 0, screen_size.width(), screen_size.height())
        self.setMinimumSize(800, 600)
        self.stackedWidget = self.ui.stackedWidget

        self.stackedWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.barcode = None
        self.ui.pushButton_2.setEnabled(True)
        self.stage4_url = "http://192.168.2.253:6101/api/stage4"
        self.stage5_url = "http://192.168.2.253:6101/api/stage5"
        self.device_status_url = f"http://192.168.2.253:6101/api/test_points/{self.barcode}"
        self.check_server_url = "http://192.168.2.253:6101/api/PROD_check"

        self.Barcode = None
        self.model_name = None
        # Initialize a QTimer
        self.timer_thread = TimerThread()

        self.timer_thread.start()  # Start the thread
        self.elapsed_time = 0
        self.operator = None
        self.qc_head = None
        # Initialize CAN bus in the __init__ method to avoid reinitializing it every time
        cursor = QCursor()
        cursor.setPos(620, 70)
        self.totalParams = 36
        self.processed_params = 0
        self.sent_data = False
        self.UIN = None
        self.data = {
            "QR_code": self.barcode,
            "model_name": None,
            "visual_inspection_status": True,
            "visual_inspection_timestamp": None,
            "board_flashing_status": True,
            "board_flashing_timestamp": None,
            "screw_fitting_status": True,
            "screw_fitting_timestamp": None,
            "mechanical_fitting_status": True,
            "mechanical_fitting_timestamp": None,
            "final_testing_status": True,
            "final_testing_timestamp": None,
            "IMEI": None,
            "ICCID": None,
            "SystemRtc": None,
            "AppFWVersion": None,
            "BLFWVersion": None,
            "GPSFWVersion": None,
            "GSMFWVersion": None,
            "HWVersion": None,
            "GPSFix": None,
            "HDOP": None,
            "PDOP": None,
            "No_satelite": None,
            "GSMStatus": None,
            "signalStrength": None,
            "Network_code": None,
            "Network_Type": None,
            "SIM": None,
            "MEMS": None,
            "Voltage": None,
            "Memory": None,
            "Ignition": None,
            "Tamper": None,
            "DI_1_H": None,
            "DI_1_L": None,
            "DI_2_H": None,
            "DI_2_L": None,
            "DI_3_H": None,
            "DI_3_L": None,
            "DO_1_H": None,
            "DO_1_L": None,
            "DO_2_H": None,
            "DO_2_L": None,
            "CAN": None,
            "RS485": None,
            "AnalogInput1": None,
            "AnalogInput2": None,
            "sticker_printing_status": None,
            "sticker_printing_timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f'),
            "last_updated": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f'),
            "UIN": None
        }
        self.headers = {"Content-Type": "application/json"}
        #self.ui.pushButton_2.clicked.connect(self.save_to_excel)
        self.ui.pushButton.clicked.connect(self.on_button_click)
        self.ui.pushButton_2.clicked.connect(self.send_data)
        self.ui.pushButton_8.clicked.connect(self.CANdata_obj.start_functions)

    def on_button_click(self):
        # Call both actions (goToPage2 and login) in sequence
        self.login()
        self.showDateTime()
        self.check_server_status()
        self.check_barcode()


    def check_barcode(self):
        # Clear the barcode input field before scanning (optional)
        self.ui.barcode_Input_2.clear()

        # Set focus to the barcode input field
        self.ui.barcode_Input_2.setFocus()

        # Define the function to check the barcode input
        def check_barcode_value():
            # Get the barcode value and strip leading whitespaces
            barcode = self.ui.barcode_Input_2.toPlainText().lstrip()

            # If the barcode is not empty, process it
            if barcode:
                self.barcode = barcode

                # Clean the barcode text if necessary
                self.barcode = self.barcode.strip()

                # Place the cleaned barcode back into the input field
                self.ui.barcode_Input_2.setPlainText(self.barcode)
                self.device_status_url = f"http://192.168.2.253:6101/api/test_points/{self.barcode}"

                self.get_device_model()

                # Reset the cursor position to the beginning of the input field
                cursor = self.ui.barcode_Input_2.textCursor()
                cursor.setPosition(0)
                self.ui.barcode_Input_2.setTextCursor(cursor)

                # Stop the timer once the barcode is processed
                timer.stop()  # This stops the timer inside the function

                # Proceed to the next stage or action
                self.check_previous_stages()

        # Set up a QTimer to check the input field every 100 milliseconds
        # Ensure the timer is started only once and stops when finished
        timer = QTimer(self)
        timer.timeout.connect(check_barcode_value)

        # Start the timer to check every 100 milliseconds
        timer.start(100)  # Check every 100 milliseconds


    def showDateTime(self):
        # Get the current date and time
        current_datetime = QDateTime.currentDateTime().toString()

        # Display the date and time in the QPlainTextEdit widget
        self.ui.operator_Input_2.setPlainText(current_datetime)


    def show_message(self, title, message):
        # Show a message box to the user
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()

    def login(self):
        # Retrieve the text from the text fields
        self.operator = self.ui.plainTextEdit.toPlainText()  # Retrieve the operator input
        self.qc_head = self.ui.plainTextEdit_2.toPlainText()  # Retrieve the QC head input

        # Debugging print statements to check the retrieved values
        # print("operator:", repr(self.operator))  # Using repr() to detect empty strings
        # print("qc_head:", repr(self.qc_head))

        # Check if both fields are filled
        if self.operator == "" or self.qc_head == "":
            # print("Either operator or qc_head is empty!")  # Debugging message
            # self.show_message("Login Failed", "Please Enter operator and qc head")
            # Ensure navigation doesn't happen when either field is empty
            pass
        else:
            # If both fields are filled, proceed with the login success logic
            # print("operator:", self.operator)
            # print("qc_head:", self.qc_head)

            # self.show_message("Login Successful", "Welcome, Operator!")

            # Set the values in the corresponding UI input fields
            self.ui.operator_Input.setPlainText(self.operator)
            self.ui.QC_input.setPlainText(self.qc_head)

            # Navigate to Page 2 only if both fields are filled
            self.stackedWidget.setCurrentIndex(1)  # Go to Page 2

    def start_timer(self):
        # Connect the timer signal to the update_elapsed_time method
        self.timer_thread.update_time_signal.connect(self.update_elapsed_time)

        # Start the timer thread if not already running
        if not self.timer_thread.isRunning():
            self.timer_thread.start()

    def update_elapsed_time(self, formatted_time):
        # This method will be connected to the timer's signal and update the UI
        # Update the UI with the formatted time (this can be customized as needed)
        self.ui.operator_Input_3.setPlainText(formatted_time)

    def get_device_model(self):
        # Make the GET request to fetch device information based on barcode
        #print("get_device_model", self.device_status_url)

        # Include the barcode in the payload (or query if required by the API)
        try:

            # Make the API request (if you need to send the barcode in the query params, adjust accordingly)
            response = requests.get(self.device_status_url, params=self.data,
                                    headers=self.headers)  # Using params instead of json for GET request

            if response.status_code == 200:
                # Parse the response JSON
                response_data = response.json()

                # Extract the model name from the response
                #self.model_name = response_data.get("device", {}).get("model_name", "Model name not found")
                self.model_name = 'ACON4L'
                # Update the UI with the model name
                self.ui.QC_input_2.setPlainText(self.model_name)

                # Call select_parameters if model name is valid
                if self.model_name and self.model_name != "Model name not found":
                    self.start_timer()
                    self.select_parameters()

                # Display the model name in the UI or print it
            else:
                self.ui.QC_input_2.setPlainText("Model name not found")
                self.ui.QC_input_2.setStyleSheet("background-color: red;")
                self.ui.pushButton_8.setEnabled(False)
                self.ui.label_34.setEnabled(False)
                self.ui.label_13.setEnabled(False)
                self.ui.label_14.setEnabled(False)
                self.ui.label_15.setEnabled(False)
                self.ui.label_16.setEnabled(False)
                self.ui.label_43.setEnabled(False)
                self.ui.plainTextEdit_5.setEnabled(False)
                self.ui.plainTextEdit_6.setEnabled(False)
                self.ui.plainTextEdit_8.setEnabled(False)
                self.ui.plainTextEdit_9.setEnabled(False)
                self.ui.label_17.setEnabled(False)
                self.ui.label_18.setEnabled(False)
                self.ui.label_28.setEnabled(False)
                self.ui.label_29.setEnabled(False)
                self.ui.label_23.setEnabled(False)
                self.ui.label_38.setEnabled(False)
                self.ui.label_30.setEnabled(False)
                self.ui.label_31.setEnabled(False)
                self.ui.label_48.setEnabled(False)
                self.ui.label_51.setEnabled(False)
                self.ui.plainTextEdit_5.setEnabled(False)
                self.ui.plainTextEdit_6.setEnabled(False)
                self.ui.plainTextEdit_8.setEnabled(False)
                self.ui.plainTextEdit_9.setEnabled(False)
                self.ui.plainTextEdit_10.setEnabled(False)
                self.ui.Tamp_L.setEnabled(False)
                self.ui.label_54.setEnabled(False)
                self.ui.label_45.setEnabled(False)
                self.ui.label_46.setEnabled(False)
                self.ui.label_47.setEnabled(False)
                #self.ui.MEMS_INIT.setEnabled(False)
                self.ui.MEMS_Xa.setEnabled(False)
                self.ui.MEMS_Ya.setEnabled(False)
                self.ui.MEMS_Za.setEnabled(False)
                self.ui.label_53.setEnabled(False)
                self.ui.label_27.setEnabled(False)
                self.ui.label_35.setEnabled(False)
                self.ui.label_36.setEnabled(False)
                self.ui.label_32.setEnabled(False)
                self.ui.label_37.setEnabled(False)
                self.ui.mains_input_2.setEnabled(False)
                self.ui.IntBat_input_2.setEnabled(False)
                self.ui.Analog1_2.setEnabled(False)
                self.ui.Analog2_4.setEnabled(False)
                self.ui.Analog2_5.setEnabled(False)
                self.ui.Analog2_3.setEnabled(False)
                self.ui.Analog2_6.setEnabled(False)
                #self.ui.pushButton_6.setEnabled(False)
                self.ui.label_39.setEnabled(False)
                self.ui.label_50.setEnabled(False)
                self.ui.label_49.setEnabled(False)
                self.ui.label_40.setEnabled(False)
                self.ui.label_41.setEnabled(False)
                self.ui.label_42.setEnabled(False)
                self.ui.label_39.setEnabled(False)
                self.ui.DI1_H_3.setEnabled(False)
                self.ui.IGN_H.setEnabled(False)
                self.ui.DI1_H_6.setEnabled(False)
                self.ui.DI1_H_7.setEnabled(False)
                self.ui.DI1_H_4.setEnabled(False)
                self.ui.DI1_H_5.setEnabled(False)
                self.ui.DI1_H_8.setEnabled(False)
                self.ui.DI_H.setEnabled(False)
                self.ui.DO1_L.setEnabled(False)
                self.ui.DO1_H.setEnabled(False)
                self.ui.DO2_L.setEnabled(False)
                self.ui.DO2_H.setEnabled(False)
                self.ui.label_55.setEnabled(False)
                print(f"Error fetching device data. Status code: {response.status_code}")
                print(f"Response: {response.text}")

        except requests.exceptions.RequestException as e:
            # Handle any errors in the request
            print(f"Error: {e}")


    def goToPage2(self):
        # print("Navigating to Page 2")
        self.stackedWidget.setCurrentIndex((self.stackedWidget.currentIndex() + 1) % 2)


    def check_server_status(self):
        response = requests.get("http://192.168.2.253:6101/api/PROD_check")
        if response.status_code == 200:
            # print("response",response.status_code)
            self.ui.barcode_Input.setPlainText("Connected")
        else:
            self.ui.barcode_Input.setPlainText("Please check connection")


    def check_previous_stages(self):
        url = f"http://192.168.2.253:6101/api/test_points/{self.barcode}"
        # print("url",url)
        try:
            # Send a GET request to the URL
            response = requests.get(url)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                data = response.json()  # Parse the JSON response

                # Access the mechanical_fitting_status
                mechanical_fitting_status = data.get('device', {}).get('status', {}).get('mechanical_fitting_status',
                                                                                         False)
                # print("mechanical_fitting_status", mechanical_fitting_status)
                # Check the status
                if mechanical_fitting_status:
                    self.ui.server_Input.setPlainText("Previous stage passed!")
                    self.ui.server_Input.setStyleSheet("background-color: green;")
                    #self.send_data()
                    #    print("Previous stage passed!")
                    return True
            else:

                self.ui.server_Input.setPlainText("Previous stage not passed.")  # Set the text
                self.ui.server_Input.setStyleSheet("background-color: red;")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")


    def select_parameters(self):
        # print("select_parameters", self.model_name)
        if self.model_name == "ACON4L":

            self.ui.DI1_H_6.show()
            self.ui.DI1_H_7.show()
            self.ui.DI1_H_4.show()
            self.ui.DI_H.show()
            self.ui.DI1_H_5.show()
            self.ui.DI1_H_8.show()
            # self.ui.DO1_L.hide()
            # self.ui.DO1_H.hide()
            # self.ui.DO2_L.hide()
            # self.ui.DO2_H.hide()

            self.ui.label_50.show()
            self.ui.label_49.show()
            self.ui.label_40.show()
            #self.ui.label_41.show()
            # self.ui.label_41.hide()
            # self.ui.label_42.hide()
        elif self.model_name == "ACON4S":
            self.ui.DI1_H_6.hide()
            self.ui.DI1_H_7.hide()
            self.ui.DI1_H_4.hide()
            self.ui.DI_H.hide()
            self.ui.DI1_H_5.hide()
            self.ui.DI1_H_8.hide()
            # self.ui.DO1_L.hide()
            # self.ui.DO1_H.hide()
            # self.ui.DO2_L.hide()
            # self.ui.DO2_H.hide()


    def send_data(self):  # Update variable here to send to server
        print("Sending data...")

        if self.check_previous_stages and not self.sent_data:  # Check if data has not been sent yet
            try:
                self.data["QR_code"] = self.barcode
                self.data['model_name'] = self.model_name
                self.data["visual_inspection_timestamp"] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                self.data["board_flashing_timestamp"] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                self.data["screw_fitting_timestamp"] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                self.data["mechanical_fitting_timestamp"] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                self.data['IMEI'] = self.CANdata_obj.IMEI_ascii
                self.data['ICCID'] = self.CANdata_obj.ICCID_ascii
                self.data['SystemRtc'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                self.data['AppFWVersion'] = self.CANdata_obj.appln_ver
                self.data['BLFWVersion'] = None
                self.data['GPSFWVersion'] = self.CANdata_obj.Gps_ver
                self.data['GSMFWVersion'] = self.CANdata_obj.GSM_ver
                self.data['HWVersion'] = None
                self.data['GPSFix'] = self.CANdata_obj.Gps_status
                self.data['HDOP'] = None
                self.data['PDOP'] = None
                self.data['No_satelite'] = self.CANdata_obj.concatenated_satellites_decimal
                self.data['GSMStatus'] = self.CANdata_obj.GSM_result
                self.data['signalStrength'] = self.CANdata_obj.CSQ,
                self.data['Network_code'] = None
                self.data['Network_Type'] = self.CANdata_obj.operatorName
                self.data['SIM'] = None
                self.data['MEMS'] = self.CANdata_obj.MEMS_result
                self.data['Voltage'] = self.CANdata_obj.Mains_result
                self.data['Memory'] = None
                self.data['Ignition'] = self.CANdata_obj.IGN
                self.data['Tamper'] = self.CANdata_obj.tamper
                self.data['DI_1_H'] = self.CANdata_obj.DI1_seen_1
                self.data['DI_1_L'] = self.CANdata_obj.DI1_seen_0
                self.data['DI_2_H'] = self.CANdata_obj.DI2_seen_1
                self.data['DI_2_L'] = self.CANdata_obj.DI2_seen_0
                self.data['DI_3_H'] = self.CANdata_obj.DI3_seen_1
                self.data['DI_3_L'] = self.CANdata_obj.DI3_seen_0
                self.data['DO_1_H'] = None
                self.data['DO_1_L'] = None
                self.data['DO_2_H'] = None
                self.data['DI_2_L'] = None
                self.data['CAN'] = None
                self.data['RS485'] = None
                self.data['AnalogInput1'] = None
                self.data['AnalogInput2'] = None
                self.data['sticker_printing_status'] = None
                self.data['sticker_printing_timestamp'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')
                self.data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')
                self.data['sticker_printing_timestamp'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')

                response = requests.put(self.stage5_url, json=self.data, headers=self.headers)

                if response.status_code == 200:
                    self.Generate_UID()
                    self.processed_params += 1

                    print("Data sent successfully")
                    print(response.json())  # prints the response content in JSON format


                    self.sent_data = True  # Flag that data has been sent successfully
                else:
                    print(f"Failed to send data: {response.status_code}")
                    print(response.text)  # prints the response body (error message)
            except requests.exceptions.RequestException as e:  # Catch any requests-related errors
                print("Error:", e)  # prints the error details
        else:
            if self.sent_data:
                print("Data has already been sent.")

    def Generate_UID(self):
        url = "http://192.168.2.253:6101/api/generate_uid"

        # Define the data to be sent in the request body
        data = {
            "IMEI": self.data['IMEI'],
            "ICCID": self.data['ICCID'],
            "model_name": self.data['model_name'],
            "QR_code": self.data['QR_code']
        }

        # Send the POST request
        response = requests.post(url, json=data)

        # Check the response status and content
        if response.status_code == 200:
            print("Request was successful.")

            # Assuming the response is in JSON format
            response_json = response.json()  # Get the JSON response as a dictionary

            print("Response:", response_json)

            # Now safely fetch the 'UIN' from the response
            UIN = response_json.get('UIN')
            self.data['UIN'] = UIN
            # Check if the UID was successfully assigned
            print("UID:", self.data['UID'])

            if self.data['UIN']:
                self.collect_sticker_prntng_params()
                print("UID (after processing):", self.data['UIN'])
            else:
                print("UIN not found in the response.")
        else:
            print("Request failed with status code:", response.status_code)
            print("Response:", response.text)

    def collect_sticker_prntng_params(self):
        stkr_prntg_var = [self.barcode,self.data.get('IMEI'),self.data.get('ICCID'),self.data.get('UIN')]
        print(stkr_prntg_var)

# Entry point of the program
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("AEPL_Logo.png"))
    # Create an instance of the MyClass class
    processor = MyClass()
    processor.show()

    sys.exit(app.exec_())
