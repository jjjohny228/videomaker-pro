from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
import os


class GoogleDriveUploader:
    def __init__(self) -> None:
        self.__do_auth()

    def __do_auth(self):
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
        self.drive = GoogleDrive(gauth)

    def upload_video(self, video_folder_path, filename, output_name):
        f = self.drive.CreateFile({"title": output_name})
        f.SetContentFile(os.path.join(video_folder_path, filename))
        f.Upload()
