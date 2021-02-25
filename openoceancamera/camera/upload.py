import os
from datetime import datetime, timedelta
from constants import EXTERNAL_DRIVE
from uploader import DropboxUploader
import logging

logging.basicConfig(filename="system_logs.txt", format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

def start_upload(slot):
    logger.info("Starting upload slot")
    upload_handler = DropboxUploader()
    for root, dirs, files in os.walk(EXTERNAL_DRIVE):
        for f in sorted(files, reverse=True):
            if slot["stop"] > datetime.now():
                logger.info(f"Uploading {f}")
                upload_handler.upload_file(os.path.join(root, f))
                logger.info(f"Uploaded {f}")
            else:
                break
