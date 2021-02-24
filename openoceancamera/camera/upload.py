import os
from datetime import datetime, timedelta
from constants import EXTERNAL_DRIVE
from uploader import DropboxUploader

def start_upload(slot):
    upload_handler = DropboxUploader()
    for root, dirs, files in os.walk(EXTERNAL_DRIVE):
        for f in sorted(files, reverse=True):
            if slot["stop"] > datetime.now():
                upload_handler.upload_file(os.path.join(root, f))
            else:
                break
