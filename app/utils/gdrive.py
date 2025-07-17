import base64
import json
import os
from pathlib import Path
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# Create a logger specific to this module
logger = logging.getLogger(__name__)

GDRIVE_KEY = json.loads(base64.b64decode(os.getenv("GOOGLE_DRIVE_KEY_BASE64")).decode('utf-8'))
FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
FILENAME = os.getenv("GOOGLE_DRIVE_FILE_NAME")
FILE_PATH = os.path.join(Path(__file__).resolve().parents[2],"data",FILENAME)
CONFIG_PATH = os.path.join(Path(__file__).resolve().parents[2], "config.json")
TEMP_PATH = os.path.join(Path(__file__).resolve().parents[2],"data","temp.db")

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
        # Update existing file
        uploaded_file = drive_service.files().update(
            fileId=file_id,
            media_body=media,
            fields='id'
        ).execute()
    else:
         # Upload file
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

    logger.info(f"Uploaded to Folder! File ID: {uploaded_file.get('id')}")
    return

def download_from_gdrive():
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

    if file_id:
        request = drive_service.files().get_media(fileId=file_id)
        with open(TEMP_PATH, 'wb') as fh:
            downloader = MediaFileUpload(request, chunksize=2048, resumable=True)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                logger.info(f"Download {int(status.progress() * 100)}% complete.")
        logger.info(f"Downloaded file to {FILE_PATH}")
    else:
        logger.info(f"File {FILENAME} not found in the folder.")

def sync_files():


def main():
    upload_to_gdrive()

if __name__ == "__main__":
    main()