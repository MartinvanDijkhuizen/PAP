import csv
import os
import time
import logging
from datetime import datetime

# alle bestanden die gecheckt moeten worden, voeg hier je extra bestand toe en maak de tijd onderin korter
CSV_FILES = [
        '/home/hu/PAP/sensorbuitenmuur.csv',
        '/home/hu/PAP/sensorbinnenmuur.csv',
        '/home/hu/PAP/sensorhoek.csv',
        '/home/hu/PAP/sensorraam.csv',
        '/home/hu/PAP/sensorruimte.csv',
        '/home/hu/PAP/sensorvloer.csv'
]

# file waar alle fouten in gestopt worden
OUTLIER_FILE = '/home/hu/PAP/sensorerrors.csv'

# slaat de datapunten hierin op
logging.basicConfig(filename='/home/hu/PAP/checkalg.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Leest de laatste n regels van een CSV-bestand
def read_last_n_rows(file_path, n):
    try:
        with open(file_path, 'r') as f:
            return list(csv.reader(f))[-n:]
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return []

# Bepaalt of de laatste meting een uitschieter is op basis van een drempelwaarde
def is_outlier(values, threshold=0.2):
    *previous, latest = values
    avg_temp = sum(v[0] for v in previous) / len(previous)
    avg_hum = sum(v[1] for v in previous) / len(previous)

    temp_diff = abs(latest[0] - avg_temp) / avg_temp
    hum_diff = abs(latest[1] - avg_hum) / avg_hum

    return temp_diff > threshold or hum_diff > threshold

# Zet rijen uit de CSV om in metingen van temperatuur en luchtvochtigheid
def parse_measurements(rows):
    measurements = []
    for row in rows:
        try:
            temp = float(row[1]) # temperatuur uit kolom 2
            hum = float(row[2])	# luchtvochtigheid uit kolom 3
            measurements.append((temp, hum, row))
        except (IndexError, ValueError):
            continue # sla ongeldige of incomplete rijen over
    return measurements

# Controleert of er uitschieters zijn in het bestand
def check_file_for_outliers(file_path):
    rows = read_last_n_rows(file_path, 5)
    measurements = parse_measurements(rows)

    if len(measurements) < 5:
        return None  # niet genoeg datapunten

    if is_outlier(measurements):
        return measurements[-1][2]  # eerder datapunten uitlezen
    return None

# Hoofdfunctie die continu de bestanden controleert
def main():
    while True:
        for file_path in CSV_FILES:
            outlier_row = check_file_for_outliers(file_path)
            if outlier_row:
		# Voeg bestandsnaam toe aan het begin van de rij met de uitschieter
                outlier_entry = [os.path.basename(file_path)] + outlier_row
                with open(OUTLIER_FILE, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(outlier_entry)
                logging.info(f"uitschieter ontdekt in {file_path}.")
        time.sleep(50)  # wacht 50 seconden, zodat je 6 metingen per 5 minuten kan checken

if __name__ == '__main__':
    main()

