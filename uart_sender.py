import time
import serial

csv_file = "/home/weerstation/weerstation_quest/wind_data.csv"
uart_port = "/dev/serial0"  
baud_rate = 9600

# Set up UART
ser = serial.Serial(uart_port, baud_rate, timeout=1)
time.sleep(2)  # Give time for UART to initialize

def get_last_line(file_path):
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            if lines:
                return lines[-1].strip()
    except Exception as e:
        return f"Error reading CSV: {e}"
    return "No data"

while True:
    last_line = get_last_line(csv_file)
    print(f"Sending: {last_line}")
    ser.write((last_line + '\n').encode('utf-8'))
    ser.flush()
    time.sleep(300)  # Wait 5 minutes
