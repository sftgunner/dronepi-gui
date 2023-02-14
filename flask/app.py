#Import necessary libraries
from flask import Flask, render_template, abort, send_file, Response, request
from pathlib import Path
import os
import datetime as dt
import cv2
from PIL import Image,ImageDraw,ImageFont
from io import BytesIO
import numpy as np
import json
import time
#Initialize the Flask app
app = Flask(__name__)

FolderPath = os.path.dirname(os.path.realpath(__file__))+"/recordings/"

print(FolderPath)

class drone_camera:
    def __init__(self, source):
        self.source = source
        self.recording = False
        self.palette = "icefire"
        self.online = True
        self.override = False
        self.width = int(source.get(3)) #cv2.CAP_PROP_FRAME_WIDTH
        self.height = int(source.get(4)) #cv2.CAP_PROP_FRAME_HEIGHT
        self.framerate = int(source.get(5)) #cv2.CAP_PROP_FPS

webcam = drone_camera(cv2.VideoCapture(0))

'''
for ip camera use - rtsp://username:password@ip_address:554/user=username_password='password'_channel=channel_number_stream=0.sdp' 
for local webcam use cv2.VideoCapture(0)
'''

def serve_pil_image(pil_img):
    img_io = BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')

def gen_frames():  
    while True:
        success, raw_frame = webcam.source.read()  # read the camera frame
        # if not success:
        if not success or webcam.override:
            webcam.online = False
            # Issue reading the webcam
            
            pil_image = Image.new('RGB', (160, 140), color = 'black')
            
            d = ImageDraw.Draw(pil_image)
            d.text((10, 125), 'Warwick Drone', fill=(255, 255, 255))
            d.text((10, 10), 'Camera offline', fill=(255, 255, 255))
            d.text((10, 20), 'Please check connection.', fill=(255, 255, 255))
            
            # pil_image = Image.open('Image.jpg').convert('RGB') 
            
            open_cv_image = np.array(pil_image) 
            # Convert RGB to BGR 
            open_cv_image = open_cv_image[:, :, ::-1].copy() 
            ret, buffer = cv2.imencode('.jpg', open_cv_image)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
            
        else:
            ret, buffer = cv2.imencode('.jpg', raw_frame)
                
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
            if webcam.recording:
                try:
                    webcam.writer.write(raw_frame)
                except:
                    print("Webcam unable to write")
            
            
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/liveview')
def liveview():
    return render_template('liveview.html')

@app.route('/api', methods=['GET'])
def search():
    args = request.args
    
    command = args.get("command")
    
    if command == "webcamonlinetoggle":
        webcam.override = not webcam.override
        response = "Webcam toggled to "+str(webcam.override)
        result = str(webcam.override)
        status = 200
    elif command ==  "recordingtoggle":
        webcam.recording = not webcam.recording
        if webcam.recording:
            webcam.writer = cv2.VideoWriter(f'flask/recordings/{dt.datetime.now().isoformat()}.mp4',cv2.VideoWriter_fourcc(*'mp4v'), webcam.framerate, (webcam.width,webcam.height))
        else:
            webcam.writer.release()
            response = "Toggled recording status to "+str(webcam.recording)
            result = str(webcam.recording)
            status = 200
    else:
        response = "Invalid request"
        result = ""
        status = 400
        
    return json.dumps({"status":status,"response":response,"result":result})


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


# ====== BELOW THIS POINT DEALS WITH THE FOLDER LISTING ====== 

def getReadableByteSize(num, suffix='B') -> str:
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)

def getTimeStampString(tSec: float) -> str:
    tObj = dt.datetime.fromtimestamp(tSec)
    tStr = dt.datetime.strftime(tObj, '%Y-%m-%d %H:%M:%S')
    return tStr

def getIconClassForFilename(fName):
    fileExt = Path(fName).suffix
    fileExt = fileExt[1:] if fileExt.startswith(".") else fileExt
    fileTypes = ["aac", "ai", "bmp", "cs", "css", "csv", "doc", "docx", "exe", "gif", "heic", "html", "java", "jpg", "js", "json", "jsx", "key", "m4p", "md", "mdx", "mov", "mp3",
                 "mp4", "otf", "pdf", "php", "png", "pptx", "psd", "py", "raw", "rb", "sass", "scss", "sh", "sql", "svg", "tiff", "tsx", "ttf", "txt", "wav", "woff", "xlsx", "xml", "yml"]
    fileIconClass = f"bi bi-filetype-{fileExt}" if fileExt in fileTypes else "bi bi-file-earmark"
    return fileIconClass

# route handler
@app.route('/recordings/', defaults={'reqPath': ''})
@app.route('/recordings/<path:reqPath>')
def getFiles(reqPath):
    # Join the base and the requested path
    # could have done os.path.join, but safe_join ensures that files are not fetched from parent folders of the base folder
    absPath = os.path.join(FolderPath, reqPath)

    # Return 404 if path doesn't exist
    if not os.path.exists(absPath):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(absPath):
        return send_file(absPath)

    # Show directory contents
    def fObjFromScan(x):
        fileStat = x.stat()
        # return file information for rendering
        return {'name': x.name,
                'fIcon': "bi bi-folder-fill" if os.path.isdir(x.path) else getIconClassForFilename(x.name),
                'relPath': os.path.relpath(x.path, FolderPath).replace("\\", "/"),
                'mTime': getTimeStampString(fileStat.st_mtime),
                'size': getReadableByteSize(fileStat.st_size)}
    fileObjs = [fObjFromScan(x) for x in os.scandir(absPath)]
    # get parent directory url
    parentFolderPath = os.path.relpath(
        Path(absPath).parents[0], FolderPath).replace("\\", "/")
    return render_template('files.html', data={'files': fileObjs,
                                                 'parentFolder': parentFolderPath})

if __name__ == "__main__":
    app.run(debug=False,host="0.0.0.0", port=8410) #Needs to be false on debug to open the camera properly