# video_recorder
 Converts RTSP stream from remote camera to MPEG-4 video files in your Google Drive (real-time)

 ## Usage
 Simply set the stream address of your camera (RTSP) and run the program.

 ## Examples
 ```python
 from video_recorder import VideoRecorder

 target = r'rtsp://rtspstream.com/ball'
 vr = VideoRecorder()
 vr.run(target)
 ```
 Also you can set target file name (file) and upload interval (upload_interval).
 On first launch, you will be automatically prompted to log in to Google Disk and give the appropriate permissions to write files.

 ## Remarks
 Make sure you don't confuse the "ffmpeg-python" library (correct) with the "ffmpeg" library (incorrect). You should also have the binaries correctly installed for video conversion on the fly (e.g. you should download the binaries separately: https://ffmpeg.org/download.html).
