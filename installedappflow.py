from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
CLIENT_SECRET_FILE = '/home/hu/PAP/secrets/client_secret.json'

def test_run_local_server():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=8080, open_browser=False)
    print("✅ Authenticatie geslaagd. Token ontvangen.")

if __name__ == '__main__':
    test_run_local_server()
