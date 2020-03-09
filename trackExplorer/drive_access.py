
import io
import tempfile

import pandas as pd

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

try:
    from trackExplorer.fileio import read_history
except:
    from fileio import read_history

SCOPES = ['https://www.googleapis.com/auth/drive']

SERVICE_ACCOUNT_FILE = 'google-credentials.json'

credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)


service = build('drive', 'v3', credentials=credentials)


driveId = None
grid_list = None


def get_drive_IDs(model):

    # get base folder Id
    q = "mimeType = 'application/vnd.google-apps.folder' and name = '{}'".format(model['folder_name'])
    folders = service.files().list(q=q, driveId=driveId, includeItemsFromAllDrives=True, supportsAllDrives=True,
                                   corpora='drive').execute()
    if len(folders['files']) > 0:
        base_folder_id = folders['files'][0]['id']
    else:
        base_folder_id = pd.NA

    # get model folder Id
    q = "mimeType = 'application/vnd.google-apps.folder' and name = '{}'".format(model['model_folder_name']) +\
        "and '{}' in parents".format(base_folder_id)
    folders = service.files().list(q=q, driveId=driveId, includeItemsFromAllDrives=True, supportsAllDrives=True,
                                   corpora='drive').execute()
    if len(folders['files']) > 0:
        model_folder_id = folders['files'][0]['id']
    else:
        model_folder_id = pd.NA

    # get summary file Id
    files = service.files().list(q="'{}' in parents and name = '{}'".format(base_folder_id, model['summary_file']),
                                 driveId=driveId, includeItemsFromAllDrives=True, supportsAllDrives=True,
                                 corpora='drive').execute()
    if len(files['files']) > 0:
        summary_file_id = files['files'][0]['id']
    else:
        summary_file_id = pd.NA

    return base_folder_id, model_folder_id, summary_file_id


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
    folder_id = folders['files'][0]['id']
    
    # get the grid list fileId
    files = service.files().list(q = "'{}' in parents and name = 'Model_grid_info'".format(folder_id),
                                driveId=driveId, includeItemsFromAllDrives=True, supportsAllDrives=True, corpora='drive').execute() 
    file_id = files['files'][0]['id']

    request = service.files().export_media(fileId=file_id, mimeType='text/csv')
    fh = io.FileIO('grid_list.csv', 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        
    grid_list = pd.read_csv('grid_list.csv')

    grid_list['base_folder_id'] = pd.NA
    grid_list['model_folder_id'] = pd.NA
    grid_list['summary_file_id'] = pd.NA

    # for each model in the grid_list, get the necessary file and folder IDs
    for i, model in grid_list.iterrows():
        base_id, model_id, summary_id = get_drive_IDs(model)
        grid_list.loc[i, 'base_folder_id'] = base_id
        grid_list.loc[i, 'model_folder_id'] = model_id
        grid_list.loc[i, 'summary_file_id'] = summary_id


def get_summary_file(gridname):
    global grid_list, driveId

    file_id = grid_list['summary_file_id'][grid_list['name'] == gridname][0]

    request = service.files().get_media(fileId=file_id)
    with tempfile.NamedTemporaryFile() as temp:
        downloader = MediaIoBaseDownload(temp, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        data = pd.read_csv(temp.name)

    return data


def get_track(gridname, filename):
    global grid_list, driveId

    folder_id = grid_list['model_folder_id'][grid_list['name'] == gridname][0]

    # get the fileId of the h5 file
    files = service.files().list(q="'{}' in parents and name = '{}'".format(folder_id, filename),
                                 driveId=driveId, includeItemsFromAllDrives=True, supportsAllDrives=True,
                                 corpora='drive').execute()
    file_id = files['files'][0]['id']

    request = service.files().get_media(fileId=file_id)
    with tempfile.NamedTemporaryFile() as temp:
        downloader = MediaIoBaseDownload(temp, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        data = read_history(temp.name)
        data = pd.DataFrame(data)

    return data


update_grid_list()
# gridname = 'BPS shortP grid'
# filename = 'M2.642_M1.993_P7.11_Z0.02405.hdf5'.
# data = get_summary_file(gridname)
# data = get_track(gridname, filename)
# print(data)
