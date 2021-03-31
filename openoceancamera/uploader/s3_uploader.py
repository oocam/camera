import boto3
import os
import logging

logging.basicConfig(filename="system_logs.txt", format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

class S3Uploader:
    def __init__(self):
        self.s3 = boto3.client("s3")

    def upload_file(self, filename: str):
        CAMERA_UID = os.environ.get("CAMERA_UID", "undefined")
        s3_object_name = CAMERA_UID + "/" + filename.split("/")[-1]
        with open(filename, 'rb') as f:
            try:
                self.s3.upload_fileobj(f, "oocam-deepsea-store", s3_object_name)
            except Exception as err:
                logger.warn(f"Could not upload to S3 bucket, skipping file.\n{err}")


if __name__ == "__main__":
    import zipfile
    from datetime import datetime
    upload_handler = S3Uploader()
    ROOT = "/Users/utkarsh/Pictures/test"
    zipname = os.path.join(ROOT, datetime.now().strftime('%Y-%m-%d_%H-%M-%S')) + ".zip"
    zipfh = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(ROOT):
        for f in filter(lambda x: str(x).endswith(".jpg") or str(x).endswith(".h264"), files):
            print(os.path.join(root, f))
            zipfh.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), os.path.join(ROOT, '..')))
    upload_handler.upload_file(zipname)
