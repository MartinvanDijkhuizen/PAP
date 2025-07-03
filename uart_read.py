import serial
import csv
from datetime import datetime

# Configure serial port
ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=5)

# Path to the CSV file
csv_file_path = '/home/hu/PAP/weerdata.csv'

print("Listening for UART messages...")

while True:
    try:
        message = ser.readline().decode('utf-8').strip()
        if message:
            print(f"Received: {message}")
            with open(csv_file_path, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([message])
        else:
            print("No message received this time.")

        time.sleep(290)  # Sleep 5 minutes
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)
