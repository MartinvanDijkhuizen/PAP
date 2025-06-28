import time
import csv
from datetime import datetime
import os

# CSV file path
csv_file = "/home/weerstation/weerstation_quest/counter_data.csv"

# Start counter
counter = 0

# Check if CSV file exists and read last value
if os.path.exists(csv_file):
    with open(csv_file, "r") as file:
        lines = file.readlines()
        if lines:
            last_line = lines[-1].strip().split(",")
            counter = int(last_line[1])  # Get last counter value

while True:
    # Get current time
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Increase counter by 1
    counter += 1

    # Write to CSV
    with open(csv_file, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([now, counter])

    print(f"[{now}] Counter: {counter} -> saved to {csv_file}")

    # Wait for 5 minutes (300 seconds)
    time.sleep(300)
