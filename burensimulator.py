from datetime import datetime
import csv
import time
import board
import busio
import digitalio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import numpy

# Neighbour simulator defaults
# Simulated temperature of walls and floor
Taim_wall_west = 21
Taim_wall_east = 21
Taim_floor_west = 21
Taim_floor_east = 21

# Set all Tmean to 0
Tmean_wall_west = 0
Tmean_wall_east = 0
Tmean_floor_west = 0
Tmean_floor_east = 0

# Initialize SPI connection
spi = busio.SPI(clock = board.SCK, MISO = board.MISO, MOSI = board.MOSI)
# Assign a chip select pin
cs = digitalio.DigitalInOut(board.D7)
# Create MCP3008 object
mcp = MCP.MCP3008(spi, cs)
# Create analog input channels for NTCs on the MCP3008 pin 1, 2, and 3
NTC1 = AnalogIn(mcp, MCP.P1)
NTC2 = AnalogIn(mcp, MCP.P2)
NTC3 = AnalogIn(mcp, MCP.P3)
NTC4 = AnalogIn(mcp, MCP.P4)


# Set up GPIO18 to GPIO21 as an output to control the Pico-Relay-B
# Set all outputs to False (=low)
sim_wall_west = digitalio.DigitalInOut(board.D21)
sim_wall_west.direction = digitalio.Direction.OUTPUT
sim_wall_west.value = False
sim_wall_east = digitalio.DigitalInOut(board.D20)
sim_wall_east.direction = digitalio.Direction.OUTPUT
sim_wall_east.value = False
sim_floor_west = digitalio.DigitalInOut(board.D19)
sim_floor_west.direction = digitalio.Direction.OUTPUT
sim_floor_west.value = False
sim_floor_east = digitalio.DigitalInOut(board.D18)
sim_floor_east.direction = digitalio.Direction.OUTPUT
sim_floor_east.value = False

csv_file = "burensimulator.csv"

# Define temperature function
def calculate_temperature(voltage):
	#         12k Ohm        NTC
	# +5V-----=======---+---=====-----Ground
	#                   |
	#                   |
	#                MCP3008
	
	# Calculate the current through 12K Ohm Resistor
	I = (5.0 - voltage) / 12000
	# Calculate resistant of NTC
	R = voltage / I
	# Calculate Temperature with Beta model
	Tinv = numpy.log(R / 10000) / 4050 + 1 / (298.15)
	T = 1 / Tinv - 273.15
	return T

# Ensure CSV file has headers
try:
    with open(csv_file, "x", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Tijdstip", "T Westgevel", "T Oostgevel", "T vloer west", "T vloer oost"])
except FileExistsError:
    pass

while True:
	"""
	The script contains two loops:
	1. 60 seconds loop 
		In this loop the script measures the Temperature of the west
		wall, Tmes_wall_west. With Taim_wall_west, it determines if	the
		simulator needs to add heat. If so it changes sim_wall_west in
		TRUE during 15 seconds.
		Consecutively, sim_wall_east, sim_floor_west, and
		sim_floor_east are processed. All during 15 seconds, 60
		seconds in total.
		The consecutive process is deliberately. Only one wall or floor
		can be heated at a time, to prevent Electrical overload.
	2. 5 minutes loop
		After 5 60 seconds loops, the mean of the Temperatures are
		written to the .csv-file. Then the procedure starts again. 
	"""
	
	# start to set al Tmean to 0
	Tmean_wall_west = 0
	Tmean_wall_east = 0
	Tmean_floor_west = 0
	Tmean_floor_east = 0
	
	
	# 60 seconds loop
	for _ in range(5):
		Tmes_wall_west = calculate_temperature(NTC1.voltage)
		if Tmes_wall_west < Taim_wall_west:
			sim_wall_west.value = True
		time.sleep(15)
		sim_wall_west.value = False	
		Tmean_wall_west += Tmes_wall_west/5 
			
		Tmes_wall_east = calculate_temperature(NTC2.voltage)
		if Tmes_wall_east < Taim_wall_east:
			sim_wall_east.value = True
		time.sleep(15)
		sim_wall_east.value = False
		Tmean_wall_east += Tmes_wall_east/5
			
		Tmes_floor_west = calculate_temperature(NTC3.voltage)
		if Tmes_floor_west < Taim_floor_west:
			sim_floor_west.value = True
		time.sleep(15)
		sim_floor_west.value = False			
		Tmean_floor_west += Tmes_floor_west/5
			
		Tmes_floor_east = calculate_temperature(NTC4.voltage)
		if Tmes_floor_east < Taim_floor_east:
			sim_floor_east.value = True
		time.sleep(15)
		sim_floor_east.value = False
		Tmean_floor_east += Tmes_floor_east/5
			
		
	
	# 5 minutes loop	
	try:
		timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")
		Tmean_wall_west = round(Tmean_wall_west,1)
		Tmean_wall_east = round(Tmean_wall_east,1)
		Tmean_floor_west = round(Tmean_floor_west,1)
		Tmean_floor_east = round(Tmean_floor_east,1)
		print(f"[{timestamp}] T Westgevel: {Tmean_wall_west} C")
		print(f"[{timestamp}] T Oostgevel: {Tmean_wall_east} C")
		print(f"[{timestamp}] T vloer west: {Tmean_floor_west} C")
		print(f"[{timestamp}] T vloer oost: {Tmean_floor_east} C")
		with open(csv_file, "a", newline='') as f:
			writer = csv.writer(f)
			writer.writerow([timestamp, Tmean_wall_west, Tmean_wall_east, Tmean_floor_west, Tmean_floor_east])
	except Exception as e:
		timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")
		with open("burensimulator.log", "a") as log:
			log.write(f"[{timestamp}] Fout: {str(e)}\n")
			print("Fout bij het lezen van de sensor:", e)	
