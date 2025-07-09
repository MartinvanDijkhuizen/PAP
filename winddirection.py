from datetime import datetime
import csv
import serial
import time

request = bytes([0x02, 0x03, 0x00, 0x00, 0x00, 0x01, 0x84, 0x39])
csv_file = "wind_data.csv"

# Ensure CSV file has headers
try:
    with open(csv_file, "x", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Tijdstip", "Graden"])
except FileExistsError:
    pass

with serial.Serial("/dev/ttyUSB0", baudrate=9600, parity=serial.PARITY_NONE, timeout=1) as ser:
    while True:
        try:
            ser.write(request)
            time.sleep(0.1)
            response = ser.read(8)
            
            if len(response) >= 4:
                direction_01 = response[3]
                direction_02 = response[4]
                graden = (direction_01 * 256 + direction_02) / 10
                                
                timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")
                print(f"[{timestamp}] Windrichting: {graden}°")

                with open(csv_file, "a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([timestamp, graden])
            else:
                print("Incomplete response")

        except Exception as e:
            timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")
            with open("wind_errors.log", "a") as log:
                log.write(f"[{timestamp}] Fout: {str(e)}\n")
            print("Fout bij het lezen van de sensor:", e)

        time.sleep(60) # every minute

