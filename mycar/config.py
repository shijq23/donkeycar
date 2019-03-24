"""
CAR CONFIG

This file is read by your car application's manage.py script to change the car
performance.

EXMAPLE
-----------
import dk
cfg = dk.load_config(config_path='~/mycar/config.py')
print(cfg.CAMERA_RESOLUTION)

"""


import os

#PATHS
CAR_PATH = PACKAGE_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(CAR_PATH, 'data')
MODELS_PATH = os.path.join(CAR_PATH, 'models')

#VEHICLE
DRIVE_LOOP_HZ = 5
MAX_LOOPS = 100000

#CAMERA
CAMERA_RESOLUTION = (120, 160) #(height, width)
CAMERA_FRAMERATE = DRIVE_LOOP_HZ

#STEERING
STEERING_CHANNEL = 0
STEERING_LEFT_PWM = 260
STEERING_RIGHT_PWM = 500

#THROTTLE
THROTTLE_CHANNEL = 4
THROTTLE_MAX_PWM = 1000
THROTTLE_MIN_PWM = 0
THROTTLE_ZERO_PWM = 500

#TRAINING
BATCH_SIZE = 128
TRAIN_TEST_SPLIT = 0.8


TUB_PATH = os.path.join(CAR_PATH, 'tub') # if using a single tub

#ROPE.DONKEYCAR.COM
ROPE_TOKEN="GET A TOKEN AT ROPE.DONKEYCAR.COM"

#REMOTE_PILOT
REMOTE_PILOT_HOST = "192.168.2.35"
REMOTE_PILOT_PORT = "8888"
