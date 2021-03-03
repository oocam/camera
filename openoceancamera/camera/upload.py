import os
import json
from datetime import datetime, timedelta
from constants import EXTERNAL_DRIVE
from uploader import DropboxUploader
import logging

logging.basicConfig(filename="system_logs.txt", format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)


if not os.path.exists(os.path.join(EXTERNAL_DRIVE, "uploads.txt")):
    with open(os.path.join(EXTERNAL_DRIVE, "uploads.txt"), 'w') as uploads:
        pass

def start_upload(slot):
    logger.info("Starting upload slot")
    upload_handler = DropboxUploader()
    uploaded_files = []
    with open(os.path.join(EXTERNAL_DRIVE, "uploads.txt"), 'r') as uploads:
        for filename in uploads:
            uploaded_files.append(filename)
    for root, dirs, files in os.walk(EXTERNAL_DRIVE):
        for f in filter(lambda x: uploaded_files.index(x), sorted(files, reverse=True)):
            if slot["stop"] > datetime.now():
                logger.info(f"Uploading {f}")
                upload_handler.upload_file(os.path.join(root, f))
                logger.info(f"Uploaded {f}")
            else:
                break
