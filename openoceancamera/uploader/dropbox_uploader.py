import os
import json
import pickle
import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect

import logging
logging.basicConfig(filename="system_logs.txt", format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

CREDENTIAL_STORE = os.path.join(os.environ["HOME"], ".oocam", "credentials")
APP_KEY=os.environ.get("DROPBOX_KEY", "")
APP_SECRET=os.environ.get("DROPBOX_SECRET", "")

def load_credentials_file():
    if os.path.exists(os.path.dirname(CREDENTIAL_STORE)) and os.path.exists(CREDENTIAL_STORE):
        with open(CREDENTIAL_STORE, 'rb') as f:
            try:
                data = pickle.load(f)
                return data
            except:
                return None
    elif os.path.exists(os.path.dirname(CREDENTIAL_STORE)):
        with open(CREDENTIAL_STORE, 'wb') as f:
            pass
        return None
    else:
        os.makedirs(os.path.dirname(CREDENTIAL_STORE))
        return None

class DropboxUploader:
    def __init__(self):
        self.auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET, token_access_type="legacy")
        self.oauth_result = load_credentials_file()
        if self.oauth_result is not None:
            self.isLoggedIn = True
        else:
            self.isLoggedIn = False

    def start_auth_flow(self):
        """
        Returns: Authorisation URL
        """
        url = self.auth_flow.start()
        with open(CREDENTIAL_STORE, 'wb') as credential_store:
            pickle.dump(self.auth_flow, credential_store)
        return url

    def complete_auth_flow(self, auth_code):
        try:
            self.auth_flow = load_credentials_file()
            self.oauth_result = self.auth_flow.finish(auth_code)
            with open(CREDENTIAL_STORE, 'wb') as credential_store:
                pickle.dump(self.oauth_result, credential_store)
            self.isLoggedIn = True
        except Exception as e:
            logger.error(e)

    def get_user_details(self):
        with dropbox.Dropbox(oauth2_access_token=self.oauth_result.access_token) as dbx:
            return dbx.users_get_current_account()

    def upload_small_file(self, file_path):
        with open(file_path, 'rb') as f:
            filename = os.path.join("/", os.path.basename(f.name))
            data = f.read()
        dbx = dropbox.Dropbox(oauth2_access_token=self.oauth_result.access_token)
        upload_result = dbx.files_upload(data, filename, mode=dropbox.files.WriteMode.overwrite, mute=True)
        return upload_result

    def upload_file(self, file_path):
        with open(file_path, 'rb') as f:
            filename = os.path.join("/", os.path.basename(f.name))
            dbx = dropbox.Dropbox(oauth2_access_token=self.oauth_result.access_token)
            try:
                metadata = dbx.files_get_metadata(filename)
                if metadata:
                    logger.info(f"File alredy exists on server")
                return metadata
            except dropbox.exceptions.ApiError:
                chunk_size = 4 * 1024 * 1024
                file_size = os.path.getsize(file_path)
                if file_size < chunk_size:
                    return self.upload_small_file(file_path) 
                upload_session = dbx.files_upload_session_start(f.read(chunk_size))
                cursor = dropbox.files.UploadSessionCursor(session_id=upload_session.session_id, offset=f.tell())
                commit = dropbox.files.CommitInfo(path=filename)
                while f.tell() < file_size:
                    if file_size - f.tell() <= chunk_size:
                        return dbx.files_upload_session_finish(f.read(chunk_size), cursor, commit)
                    else:
                        dbx.files_upload_session_append_v2(f.read(chunk_size), cursor)
                        cursor.offset = f.tell()

if __name__ == "__main__":
    dbx = DropboxUploader()
    if not dbx.isLoggedIn:
        print(DropboxUploader.start_auth_flow())
        code = input("Auth code: ")
        DropboxUploader.complete_auth_flow(code)
        logger.info("Logged in to Dropbox")
    print("Starting upload")
    dbx = DropboxUploader()
    dbx.upload_file("/Users/utkarsh/Downloads/sample.pdf")