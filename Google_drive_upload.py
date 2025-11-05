import os
import glob
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run_flow

# Lokale map met CSV-bestanden
LOCAL_FOLDER = '/home/neids/scripts/'

# Google Drive map-ID van /PAP_main/
DRIVE_FOLDER_ID = '1H39qoW0GFccQ_FFR2GZbzyf7bzA0CDI0'

# Authenticatie
def authenticate_drive():
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    store = Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = run_flow(flow, store)
    service = build('drive', 'v3', credentials=creds)
    return service

# Upload of update CSV-bestanden
def upload_all_csvs(local_folder, drive_folder_id):
    service = authenticate_drive()
    csv_files = glob.glob(os.path.join(local_folder, '*.csv'))

    if not csv_files:
        print("Geen CSV-bestanden gevonden.")
        return

    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        print(f"Verwerken: {file_name}")

        # Zoek of bestand al bestaat in de Drive-map
        query = f"name='{file_name}' and '{drive_folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])

        media = MediaFileUpload(file_path, mimetype='text/csv')

        if items:
            # Bestand bestaat, update het
            file_id = items[0]['id']
            updated_file = service.files().update(fileId=file_id, media_body=media).execute()
            print(f"✅ Bestand bijgewerkt: {updated_file.get('id')}")
        else:
            # Bestand bestaat niet, maak nieuw bestand aan
            file_metadata = {
                'name': file_name,
                'parents': [drive_folder_id]
            }
            new_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f"🆕 Nieuw bestand geüpload: {new_file.get('id')}")

# ▶️ Start upload
upload_all_csvs(LOCAL_FOLDER, DRIVE_FOLDER_ID)
