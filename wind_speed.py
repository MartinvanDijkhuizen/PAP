from datetime import datetime
import csv
import time
import board
import busio
import digitalio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import numpy

# anemometer defaults
anemometer_voltage    = numpy.array([0.404, 2.0])
anemometer_wind_speed = numpy.array([0, 32.4])
# a and b of lineair function y = ax + b, to calculate wind_speed
a, b = numpy.polyfit(anemometer_voltage, anemometer_wind_speed, 1)

# Initialize SPI connection
spi = busio.SPI(clock = board.SCK, MISO = board.MISO, MOSI = board.MOSI)
# Assign a chip select pin
cs = digitalio.DigitalInOut(board.D7)
# Create MCP3008 object
mcp = MCP.MCP3008(spi, cs)
# Create analog input channel for anemometer on the MCP3008 pin 0
channel = AnalogIn(mcp, MCP.P0)

csv_file = "wind_speed.csv"

# Define wind_speed function
def calculate_wind_speed(x):
	ws = round(a * x + b, 1)
	return ws

# Ensure CSV file has headers
try:
    with open(csv_file, "x", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Wind_speed"])
except FileExistsError:
    pass

# Prevent all calculations from taking place at the same time
time.sleep(210)

while True:
	try:
		timestamp = datetime.now().replace(microsecond=0).isoformat()
		wind_speed = calculate_wind_speed(channel.voltage)
		with open(csv_file, "a", newline='') as f:
			writer = csv.writer(f)
			writer.writerow([timestamp, wind_speed])
	except Exception as e:
		timestamp = datetime.now().replace(microsecond=0).isoformat()
		with open("wind_errors.log", "a") as log:
			log.write(f"[{timestamp}] Fout: {str(e)}\n")
			print("Fout bij het lezen van de sensor:", e)

	time.sleep(300) # every 5 minutes
