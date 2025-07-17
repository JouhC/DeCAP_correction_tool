from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import base64
import json
import os
from pathlib import Path
import logging

# Create a logger specific to this module
logger = logging.getLogger(__name__)

load_dotenv()

GDRIVE_KEY = json.loads(base64.b64decode(os.environ["GOOGLE_DRIVE_KEY_BASE64"]).decode('utf-8'))
FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
FILENAME = os.environ.get("GOOGLE_DRIVE_FILE_NAME")
FILE_PATH = os.path.join(Path(__file__).resolve().parents[2],"data",FILENAME)
CONFIG_PATH = os.path.join(Path(__file__).resolve().parents[2], "config.json")

def extract_filenames(drive_service):
    # Query files in the folder
    query = f"'{FOLDER_ID}' in parents and trashed = false"

    response = drive_service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)',
    ).execute()

    return response.get('files', [])

def upload_to_gdrive():
    # Create credentials
    credentials = service_account.Credentials.from_service_account_info(GDRIVE_KEY)

    # Build Drive API service
    drive_service = build('drive', 'v3', credentials=credentials)

    files = extract_filenames(drive_service)
    
    file_id = None
    for file in files:
        if file['name'] == FILENAME:
            logger.info(f"File {FILENAME} already exists in the folder.")
            file_id = file['id']
            break
    
    # Set metadata with the folder ID
    file_metadata = {
        'name': FILENAME,
        'parents': [FOLDER_ID],
    }

    media = MediaFileUpload(FILE_PATH, mimetype='application/octet-stream', resumable=True)
    
    if file_id:
    # Upload file
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
    else:
        # Update existing file
        uploaded_file = drive_service.files().update(
            fileId=file_id,
            media_body=media,
            fields='id'
        ).execute()

    logger.info(f"Uploaded to Folder! File ID: {uploaded_file.get('id')}")
    return


def main():
    # Create credentials
    credentials = service_account.Credentials.from_service_account_info(GDRIVE_KEY)

    # Build Drive API service
    drive_service = build('drive', 'v3', credentials=credentials)
    files = extract_filenames(drive_service)

    print(files)

if __name__ == "__main__":
    main()