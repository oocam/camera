import boto3
import os
import logging

logging.basicConfig(filename="system_logs.txt", format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


class ProgressPercentage(object):
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify, assume this is hooked up to a single filename
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush()

class S3Uploader:
    def __init__(self):
        self.s3 = boto3.client("s3")

    def upload_file(self, filename: str):
        CAMERA_UID = os.environ.get("CAMERA_UID", "undefined")
        s3_object_name = CAMERA_UID + "/" + filename.split("/")[-1]
        with open(filename, 'rb') as f:
            try:
                self.s3.upload_fileobj(f, "oocam-deepsea-store", s3_object_name, Callback=ProgressPercentage(f))
            except Exception as err:
                logger.warn(f"Could not upload to S3 bucket, skipping file.\n{err}")


if __name__ == "__main__":
    import zipfile
    from datetime import datetime
    upload_handler = S3Uploader()
    ROOT = "/Users/utkarsh/Pictures/test"
    zipname = os.path.join(ROOT, "2021-03-31_18-17-34.zip")
    upload_handler.upload_file(zipname)
