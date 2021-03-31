import os
import json
import zipfile
from datetime import datetime, timedelta
from constants import EXTERNAL_DRIVE
from uploader import S3Uploader
import logging

logging.basicConfig(filename="system_logs.txt", format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

try:
    if not os.path.exists(os.path.join(EXTERNAL_DRIVE, "uploads.txt")):
        with open(os.path.join(EXTERNAL_DRIVE, "uploads.txt"), 'w') as uploads:
            pass
except:
    logger.error("There is no USB connected")

def start_upload(slot):
    logger.info("Starting upload slot")
    upload_handler = S3Uploader()
    try:
        zipname = os.path.join(EXTERNAL_DRIVE, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')) + ".zip"
        zipfh = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(EXTERNAL_DRIVE):
            for f in filter(lambda x: str(x).endswith(".jpg") or str(x).endswith(".h264"), files):
                zipfh.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), os.path.join(EXTERNAL_DRIVE, '..')))
        logger.info("Created ZIP file")
        upload_handler.upload_file(zipname)
    except Exception as err:
        logger.error(f"USB Not connected. Error message: {err}")
