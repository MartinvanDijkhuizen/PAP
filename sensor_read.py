from datetime import datetime
import csv
import time
import board
import busio
import digitalio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import adafruit_dht
import numpy
import serial
import psycopg2
from psycopg2 import sql

# Neighbour simulator defaults
# Simulated temperature of walls and floor
Taim_wall_west = 19.0
Taim_wall_east = 19.0
Taim_floor_west = 19.0
Taim_floor_east = 19.0
# Initialize SPI connection
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
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

# Initialize the DHT22 sensors (connected to GPIO 4,5,6,17,22,27)
dht_innerwall = adafruit_dht.DHT22(board.D5)
dht_outerwall = adafruit_dht.DHT22(board.D6)
dht_corner = adafruit_dht.DHT22(board.D22)
dht_window = adafruit_dht.DHT22(board.D17)
dht_inside = adafruit_dht.DHT22(board.D27)
dht_floor = adafruit_dht.DHT22(board.D4)

# Anemometer defaults
anemometer_voltage = numpy.array([0.404, 2.0])
anemometer_wind_speed = numpy.array([0, 32.4])
# a and b of lineair function y = ax + b, to calculate wind_speed
a, b = numpy.polyfit(anemometer_voltage, anemometer_wind_speed, 1)
# Create analog input channel for anemometer on the MCP3008 pin 0
windspeedchannel = AnalogIn(mcp, MCP.P0)

# Winddirection meter defaults
request = bytes([0x02, 0x03, 0x00, 0x00, 0x00, 0x01, 0x84, 0x39])


# Name of the csv file to store the data
csv_file = "sensordata.csv"

# Database configuration
DB_CONFIG = {
    "host": "145.38.194.194",
    "port": 5432,
    "database": "PAP",
    "user": "BE-lab",
    "password": "P!u9@#dp!@y",
}


def read_NTC_sensor(NTC):
    try:
        voltage = NTC.voltage
        temperature = calculate_NTC_temperature(voltage)
        return round(temperature, 1)
    except Exception as e:
        timestamp_log = datetime.now().replace(microsecond=0).isoformat()
        with open("errors.log", "a") as log:
            log.write(f"[{timestamp_log}] Fout: {str(e)}\n")
        print("Fout bij het lezen van de NTC sensor:", e)
        return None


# Define temperature function
def calculate_NTC_temperature(voltage):
    #         12k Ohm        NTC
    # +3.3V-----=======---+---=====-----Ground
    #                   |
    #                   |
    #                MCP3008

    # Calculate the current through 12K Ohm Resistor
    I = (3.3 - voltage) / 12000
    # Calculate resistant of NTC
    R = voltage / I
    # Calculate Temperature with Beta model
    Tinv = numpy.log(R / 10000) / 4050 + 1 / (298.15)
    T = 1 / Tinv - 273.15
    return T


def compare_temperatures(T, Taim):
    if T < Taim:
        return True
    else:
        return False


def read_dht_sensor(sensor):
    try:
        temperature = sensor.temperature
        humidity = sensor.humidity
        if temperature is not None and humidity is not None:
            return round(temperature, 1), round(humidity, 1)
        else:
            return None, None
    except RuntimeError as e:
        print(f"Sensor error: {e.args[0]}")
        timestamp_log = datetime.now().replace(microsecond=0).isoformat()
        with open("errors.log", "a") as log:
            log.write(f"[{timestamp_log}] Fout: {str(e)}\n")
        print("Fout bij het lezen van de DHT sensors:", e)
        return None, None


def read_wind_speed():
    try:
        voltage = windspeedchannel.voltage
        wind_speed = calculate_wind_speed(voltage)
        return round(wind_speed, 1)
    except Exception as e:
        timestamp_log = datetime.now().replace(microsecond=0).isoformat()
        with open("errors.log", "a") as log:
            log.write(f"[{timestamp_log}] Fout: {str(e)}\n")
        print("Fout bij het lezen van de anemometer:", e)
        return None


def calculate_wind_speed(x):
    ws = round(a * x + b, 1)
    return ws


def read_wind_direction():
    with serial.Serial(
        "/dev/ttyUSB0", baudrate=9600, parity=serial.PARITY_NONE, timeout=1
    ) as ser:
        try:
            ser.write(request)
            time.sleep(0.1)
            response = ser.read(8)

            if len(response) >= 4:
                direction_01 = response[3]
                direction_02 = response[4]
                wd = (direction_01 * 256 + direction_02) / 10
                return wd
            else:
                print("Incomplete wind direction response")
                return None
        except Exception as e:
            timestamp_log = datetime.now().replace(microsecond=0).isoformat()
            with open("errors.log", "a") as log:
                log.write(f"[{timestamp_log}] Fout: {str(e)}\n")
            print("Fout bij het lezen van de windrichtingsensor:", e)
            return None


def open_csv():
    # Ensure CSV file has headers
    try:
        with open(csv_file, "x", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Timestamp",
                    "T Westgevel",
                    "T Oostgevel",
                    "T vloer west",
                    "T vloer oost",
                    "T vloer",
                    "H vloer",
                    "T raam",
                    "H raam",
                    "T ruimte",
                    "H ruimte",
                    "T hoek",
                    "H hoek",
                    "T binnenmuur",
                    "H binnenmuur",
                    "T buitenmuur",
                    "H buitenmuur",
                    "Windsnelheid",
                    "Windrichting",
                ]
            )
    except FileExistsError:
        pass


def write_csv(
    timestamp,
    Tww,
    Twe,
    Tfw,
    Tfe,
    Tvloer,
    Hvloer,
    Traam,
    Hraam,
    Truimte,
    Hruimte,
    Thoek,
    Hhoek,
    Tbinnenmuur,
    Hbinnenmuur,
    Tbuitenmuur,
    Hbuitenmuur,
    wind_speed,
    wind_direction,
):
    try:
        with open(csv_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    timestamp,
                    Tww,
                    Twe,
                    Tfw,
                    Tfe,
                    Tvloer,
                    Hvloer,
                    Traam,
                    Hraam,
                    Truimte,
                    Hruimte,
                    Thoek,
                    Hhoek,
                    Tbinnenmuur,
                    Hbinnenmuur,
                    Tbuitenmuur,
                    Hbuitenmuur,
                    wind_speed,
                    wind_direction,
                ]
            )
    except Exception as e:
        timestamp_log = datetime.now().replace(microsecond=0).isoformat()
        with open("errors.log", "a") as log:
            log.write(f"[{timestamp_log}] Fout: {str(e)}\n")
        print("Fout bij het schrijven naar CSV:", e)


def insert_to_postgres(
    timestamp,
    Tww,
    Twe,
    Tfw,
    Tfe,
    Tvloer,
    Hvloer,
    Traam,
    Hraam,
    Truimte,
    Hruimte,
    Thoek,
    Hhoek,
    Tbinnenmuur,
    Hbinnenmuur,
    Tbuitenmuur,
    Hbuitenmuur,
    wind_speed,
    wind_direction,
):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        insert_query = sql.SQL(
            """INSERT INTO sensor_data 
            (timestamp, t_westgevel, t_oostgevel, t_vloer_west, t_vloer_oost,
             t_vloer, h_vloer, t_raam, h_raam, t_ruimte, h_ruimte, t_hoek, h_hoek,
             t_binnenmuur, h_binnenmuur, t_buitenmuur, h_buitenmuur,
             windsnelheid, windrichting)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        )

        cursor.execute(
            insert_query,
            (
                timestamp,
                Tww,
                Twe,
                Tfw,
                Tfe,
                Tvloer,
                Hvloer,
                Traam,
                Hraam,
                Truimte,
                Hruimte,
                Thoek,
                Hhoek,
                Tbinnenmuur,
                Hbinnenmuur,
                Tbuitenmuur,
                Hbuitenmuur,
                wind_speed,
                wind_direction,
            ),
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        timestamp_log = datetime.now().replace(microsecond=0).isoformat()
        with open("errors.log", "a") as log:
            log.write(f"[{timestamp_log}] Database error: {str(e)}\n")
        print("Fout bij het schrijven naar de database:", e)


def main():
    open_csv()
    while True:
        # read sensors
        T_wall_west = read_NTC_sensor(NTC1)
        sim_wall_west.value = compare_temperatures(T_wall_west, Taim_wall_west)
        time.sleep(1)
        T_wall_east = read_NTC_sensor(NTC2)
        sim_wall_east.value = compare_temperatures(T_wall_east, Taim_wall_east)
        time.sleep(1)
        T_floor_west = read_NTC_sensor(NTC3)
        sim_floor_west.value = compare_temperatures(T_floor_west, Taim_floor_west)
        time.sleep(1)
        T_floor_east = read_NTC_sensor(NTC4)
        sim_floor_east.value = compare_temperatures(T_floor_east, Taim_floor_east)
        time.sleep(1)
        Tvloer, Hvloer = read_dht_sensor(dht_floor)
        time.sleep(1)
        Traam, Hraam = read_dht_sensor(dht_window)
        time.sleep(1)
        Truimte, Hruimte = read_dht_sensor(dht_inside)
        time.sleep(1)
        Thoek, Hhoek = read_dht_sensor(dht_corner)
        time.sleep(1)
        Tbinnenmuur, Hbinnenmuur = read_dht_sensor(dht_innerwall)
        time.sleep(1)
        Tbuitenmuur, Hbuitenmuur = read_dht_sensor(dht_outerwall)
        time.sleep(1)
        wind_speed = read_wind_speed()
        time.sleep(1)
        wind_direction = read_wind_direction()

        timestamp = datetime.now().replace(microsecond=0).isoformat()

        # Write to CSV
        write_csv(
            timestamp,
            T_wall_west,
            T_wall_east,
            T_floor_west,
            T_floor_east,
            Tvloer,
            Hvloer,
            Traam,
            Hraam,
            Truimte,
            Hruimte,
            Thoek,
            Hhoek,
            Tbinnenmuur,
            Hbinnenmuur,
            Tbuitenmuur,
            Hbuitenmuur,
            wind_speed,
            wind_direction,
        )
        time.sleep(1)

        # Insert to PostgreSQL
        insert_to_postgres(
            timestamp,
            T_wall_west,
            T_wall_east,
            T_floor_west,
            T_floor_east,
            Tvloer,
            Hvloer,
            Traam,
            Hraam,
            Truimte,
            Hruimte,
            Thoek,
            Hhoek,
            Tbinnenmuur,
            Hbinnenmuur,
            Tbuitenmuur,
            Hbuitenmuur,
            wind_speed,
            wind_direction,
        )

        time.sleep(
            286
        )  # Wait for 286 seconds, together with the 14 seconds of sensor reading, this makes it 5 minutes between writes


if __name__ == "__main__":
    main()
