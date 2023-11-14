import numpy as np
import cv2
import ffmpeg
from datetime import datetime, timedelta
import time
import pickle
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive.file']


class VideoRecorder:
    target = r'rtsp://rtspstream.com/ball'
    file = 'record.avi'


    def upload_video(self, folder_name='Cam'):
        # default folder_name = Cam
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        service = build('drive', 'v3', credentials=creds)
        items = service.files().list(pageSize=5, fields='nextPageToken, files(id, name, mimeType, size, parents, modifiedTime)').execute().get('files', [])
        if any(item['name'] == folder_name and 'application/vnd.google-apps.folder' in item['mimeType'] for item in items):
            folder_id = list(item['id'] for item in items if item['name'] == folder_name and 'application/vnd.google-apps.folder' in item['mimeType'])[0]
        else:
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder_id = service.files().create(body=folder_metadata, fields='id').execute().get('id')
        file_metadata = {
            'name': self.file,
            'parents': [folder_id]
        }
        media = MediaFileUpload(self.file, resumable=True)
        if any(item['name'] == self.file for item in items):
            file_id = list(item['id'] for item in items if item['name'] == self.file)[0]
            file = service.files().get(fileId=file_id).execute()
            file = service.files().update(fileId=file_id, media_body=media).execute()
        else:
            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id')


    def save_video(self, cap,fps=33.0):
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                i_width,i_height = frame.shape[1],frame.shape[0]
                break
        process = (
        ffmpeg
            .input('pipe:',format='rawvideo', pix_fmt='rgb24',s='{}x{}'.format(i_width,i_height))
            .output(self.file,pix_fmt='yuv420p',vcodec='libx264',r=fps,crf=37)
            # 1 hour = ~ 45 MB, 1 day = ~ 1 GB
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )
        return process


    def record_video(self, target, file, upload_interval):
        # default upload_interval = 10 minutes
        self.target = target
        cap = cv2.VideoCapture(self.target, cv2.CAP_FFMPEG)
        cap.set(3,1920)
        cap.set(4,1080)
        # self.file = f'record_{last.strftime("%Y%m%d_%H%M%S")}.avi'
        self.file = file
        process = self.save_video(cap)
        upload_last_time = datetime.now()
        while(cap.isOpened()):
            ret, frame = cap.read()
            if ret==True:
                frame = cv2.flip(frame,0)
                process.stdin.write(
                    cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        .astype(np.uint8)
                        .tobytes()
                        )
                # cv2.imshow('frame',frame)
                if upload_interval != 0 and datetime.now() > upload_last_time + timedelta(minutes=upload_interval):
                    self.upload_video()
                    upload_last_time = datetime.now()
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    process.stdin.close()
                    process.wait()
                    cap.release()
                    cv2.destroyAllWindows()
                    break
            else:
                process.stdin.close()
                process.wait()
                cap.release()
                cv2.destroyAllWindows()
                break


    def run(self, target, file='record.avi', upload_interval=10):
        while(True):
            self.record_video(target, file, upload_interval)


if __name__ == "__main__":
    target = r'rtsp://rtspstream.com/ball'
    vr = VideoRecorder()
    vr.run(target)
