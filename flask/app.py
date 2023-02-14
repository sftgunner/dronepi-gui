#Import necessary libraries
from flask import Flask, render_template, abort, send_file, Response, request
import os
import datetime as dt
import cv2
from PIL import Image,ImageDraw,ImageFont
from io import BytesIO
import numpy as np
import json
import time

# Required for radiometry

from leptontools import *
from folderindex import *


#Initialize the Flask app
app = Flask(__name__)

# drone_camera isn't currently used, but has been kept just in case for future reference
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

# webcam = drone_camera(cv2.VideoCapture(0))

class uvc_camera:
    def __init__(self):
        self.recording = False
        self.palette = "icefire"
        self.maxminshow = False
        self.framerate = 10
        self.height = 120
        self.width = 160
        
webcam = uvc_camera()

'''
for ip camera use - rtsp://username:password@ip_address:554/user=username_password='password'_channel=channel_number_stream=0.sdp' 
for local webcam use cv2.VideoCapture(0)
'''

def serve_pil_image(pil_img):
    img_io = BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')

def gen_raw_frames():
    ctx = POINTER(uvc_context)()
    dev = POINTER(uvc_device)()
    devh = POINTER(uvc_device_handle)()
    ctrl = uvc_stream_ctrl()

    res = libuvc.uvc_init(byref(ctx), 0)
    if res < 0:
        print("uvc_init error")
        exit(1)

    try:
        res = libuvc.uvc_find_device(ctx, byref(dev), PT_USB_VID, PT_USB_PID, 0)
        if res < 0:
            print("uvc_find_device error")
            exit(1)

        try:
            res = libuvc.uvc_open(dev, byref(devh))
            if res < 0:
                print("uvc_open error "+str(res))
                if res == -6:
                    while True:
                        pil_image = Image.new('RGB', (160, 140), color = 'black')
                        
                        d = ImageDraw.Draw(pil_image)
                        d.text((10, 125), 'Warwick Drone', fill=(255, 255, 255))
                        d.text((10, 10), 'Camera busy (uvc_open=-6)', fill=(255, 255, 255))
                        d.text((10, 20), 'Please reboot to fix.', fill=(255, 255, 255))
                        
                        # pil_image = Image.open('Image.jpg').convert('RGB') 
                        
                        open_cv_image = np.array(pil_image) 
                        # Convert RGB to BGR 
                        open_cv_image = open_cv_image[:, :, ::-1].copy() 
                        ret, buffer = cv2.imencode('.jpg', open_cv_image)
                        frame = buffer.tobytes()
                        yield (b'--frame\r\n'
                            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
                else:
                    print("Not sure what error "+str(res)+" means, so exiting")
                    exit(1)

            print("device opened!")

            print_device_info(devh)
            print_device_formats(devh)

            frame_formats = uvc_get_frame_formats_by_guid(devh, VS_FMT_GUID_Y16)
            if len(frame_formats) == 0:
                print("device does not support Y16")
                exit(1)

            libuvc.uvc_get_stream_ctrl_format_size(devh, byref(ctrl), UVC_FRAME_FORMAT_Y16,
                frame_formats[0].wWidth, frame_formats[0].wHeight, int(1e7 / frame_formats[0].dwDefaultFrameInterval)
            )

            res = libuvc.uvc_start_streaming(devh, byref(ctrl), PTR_PY_FRAME_CALLBACK, None, 0)
            if res < 0:
                print("uvc_start_streaming failed: {0}".format(res))
                exit(1)

            # fourcc = cv2.VideoWriter_fourcc(*'MP4V')
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            out = cv2.VideoWriter('flask/recordings/output.avi', fourcc, 10.0, (640,480))
            # out = cv2.VideoWriter('flask/recordings/output.avi', -1, 20.0, (640,480))

            try:
                while True:
                    data = q.get(True, 500)
                    if data is None:
                        break
                    #print(data)
                    data = cv2.resize(data[:,:], (640, 480))
                    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(data)
                    img = raw_to_8bit(data)
                    if webcam.maxminshow:
                        display_temperature(img, minVal, minLoc, (255, 0, 0))
                        display_temperature(img, maxVal, maxLoc, (0, 0, 255))
                    #cv2.imshow('Lepton Radiometry', img)
                    #cv2.waitKey(1)
                    if webcam.recording:
                        # webcam.writer.write(img)
                        out.write(img)
                    # out.write(img)
                    # cv2.waitKey(1)
                    ret, buffer = cv2.imencode('.jpg', img)
                
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

                cv2.destroyAllWindows()
            finally:
                libuvc.uvc_stop_streaming(devh)

            print("done")
        finally:
            libuvc.uvc_unref_device(dev)
    finally:
        libuvc.uvc_exit(ctx)

            
            
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
    if command == "maxmintoggle":
        webcam.maxminshow = not webcam.maxminshow
        response = "Maxmin toggled to "+str(webcam.maxminshow)
        result = str(webcam.maxminshow)
        status = 200
    elif command ==  "recordingtoggle":
        webcam.recording = not webcam.recording
        # if webcam.recording:
        #     print(webcam.framerate)
        #     print(webcam.width)
        #     print(webcam.height)
        #     webcam.writer = cv2.VideoWriter(f'flask/recordings/{dt.datetime.now().isoformat()}.mp4',cv2.VideoWriter_fourcc(*'mp4v'), webcam.framerate, (webcam.width,webcam.height))
        # else:
        #     webcam.writer.release()
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
    return Response(gen_raw_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


# ====== FOLDER LISTING ====== 

FolderPath = os.path.dirname(os.path.realpath(__file__))+"/recordings/"

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
    
# ====== FLASK ====== 

if __name__ == "__main__":
    app.run(debug=False,host="0.0.0.0", port=8410) #Needs to be false on debug to open the camera properly