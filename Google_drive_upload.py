import time
import os
import glob
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Lokale map met CSV-bestanden
LOCAL_FOLDER = '/home/hu/PAP/'

# Lokale map met secrets.
# LET OP: zet deze map in .gitignore zodat deze niet op github.com komt
LOCAL_SECRET = '/home/hu/PAP/secrets/'

# Google Drive map-ID van /PAP_main/
DRIVE_FOLDER_ID = '1H39qoW0GFccQ_FFR2GZbzyf7bzA0CDI0'

# OAuth instellingen
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CLIENT_SECRET_FILE = os.path.join(LOCAL_SECRET, 'client_secret.json')
TOKEN_PICKLE = os.path.join(LOCAL_SECRET, 'token.pickle')

# Authenticatie
def authenticate_drive():
    creds = None

    # Probeer bestaande token te laden
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)

    # Als er geen geldige credentials zijn, start de flow via console
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=8080, open_browser=False)
        print("✅ Authenticatie geslaagd. Token ontvangen.")

        # Sla token op
        with open(TOKEN_PICKLE, 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)
    return service

# Upload of update CSV-bestanden
def upload_all_csvs(local_folder, drive_folder_id):
    service = authenticate_drive()
    csv_files = glob.glob(os.path.join(local_folder, '*.csv'))

    if not csv_files:
        print("📂 Geen CSV-bestanden gevonden.")
        return

    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        print(f"📄 Verwerken: {file_name}")

        # Zoek of bestand al bestaat in de Drive-map
        query = f"name='{file_name}' and '{drive_folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])

        media = MediaFileUpload(file_path, mimetype='text/csv')

        if items:
            # Bestand bestaat, update het
            file_id = items[0]['id']
            try:
                updated_file = service.files().update(fileId=file_id, media_body=media).execute()
                print(f"✅ Bestand bijgewerkt: {updated_file.get('id')}")
            except Exception as e:
                print(f"⚠️ Fout bij bijwerken van {file_name}: {e}")
        else:
            # Bestand bestaat niet, maak nieuw bestand aan
            file_metadata = {
                'name': file_name,
                'parents': [drive_folder_id]
            }
            try:
                new_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                print(f"🆕 Nieuw bestand geüpload: {new_file.get('id')}")
            except Exception as e:
                print(f"⚠️ Fout bij aanmaken van {file_name}: {e}")
        time.sleep(1)

# ▶️ Start upload
if __name__ == '__main__':
    upload_all_csvs(LOCAL_FOLDER, DRIVE_FOLDER_ID)
