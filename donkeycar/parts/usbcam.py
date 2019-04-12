import os
import cv2
import time
import numpy as np
from PIL import Image
import glob


class PiCamera():
    def __init__(self, resolution=(120, 160), framerate=7):
        self.video = cv2.VideoCapture(0)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0]) #SCREEN_WIDTH
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1]) #SCREEN_HIGHT
        print('video resolution h, w {0}'.format(resolution))
        # Find OpenCV version
        print('OpenCV version %s' % cv2.__version__)
        (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
        
        # With webcam get(CV_CAP_PROP_FPS) does not work.
        # Let's see for ourselves.
        
        if int(major_ver) < 3:
            fps = self.video.get(cv2.cv.CV_CAP_PROP_FPS)
            print("Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(fps))
        else:
            fps = self.video.get(cv2.CAP_PROP_FPS)
            print("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))

        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.on = True

        print('UsbCamera loaded.. .warming camera')
        #time.sleep(2)

    def run(self):
        _, bgr_image = self.video.read()
        return bgr_image

    def run_threaded(self):
        return self.frame

    def update(self):
        # keep looping infinitely until the thread is stopped
        while self.on:
            if self.video.isOpened():
                _, bgr_image = self.video.read()
                # if the thread indicator variable is set, stop the thread
                if bgr_image is not None:
                    self.frame = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stopping UsbCamera')
        time.sleep(.5)
        self.video.release()
