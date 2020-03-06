
import io

import pandas as pd

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive']

SERVICE_ACCOUNT_FILE = 'trackexplorer-270111-6a2016e424ee.json'

credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)


service = build('drive', 'v3', credentials=credentials)


driveId = None
grid_list = None


def update_grid_list():
    
    global grid_list, driveId
    
    # get the drive Id
    driveId = None
    all_drives = service.drives().list().execute()
    for drive in all_drives['drives']:
        if drive['name'] == 'MESA models':
            driveId = drive['id']
    
    # get trackExplorer folder Id
    folders = service.files().list(q = "mimeType = 'application/vnd.google-apps.folder' and name = 'trackExplorer'", 
                                   driveId=driveId, includeItemsFromAllDrives=True, supportsAllDrives=True, corpora='drive').execute()
    folderId = folders['files'][0]['id']
    
    # get the grid list fileId
    files = service.files().list(q = "'{}' in parents and name = 'Model_grid_info.csv'".format(folderId),
                                driveId=driveId, includeItemsFromAllDrives=True, supportsAllDrives=True, corpora='drive').execute() 
    fileId = files['files'][0]['id']
    
    
    request = service.files().get_media(fileId=fileId)
    #fh = io.BytesIO()
    fh = io.FileIO('grid_list.csv', 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        
    grid_list = pd.read_csv('grid_list.csv')
    
        
update_grid_list()
