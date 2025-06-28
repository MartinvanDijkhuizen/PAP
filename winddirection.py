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
                direction_idx = response[3]
                if direction_idx < 16:
                    degrees = direction_idx * 22.5
                else:
                    degrees = "Ongeldige waarde"

                timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")
                print(f"[{timestamp}] Windrichting: {degrees}°")

                with open(csv_file, "a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([timestamp, degrees])
            else:
                print("Incomplete response")

        except Exception as e:
            timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")
            with open("wind_errors.log", "a") as log:
                log.write(f"[{timestamp}] Fout: {str(e)}\n")
            print("Fout bij het lezen van de sensor:", e)

        time.sleep(300)  # every 5 minutes

