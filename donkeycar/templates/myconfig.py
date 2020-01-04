# """ 
# My CAR CONFIG 

# This file is read by your car application's manage.py script to change the car
# performance

# If desired, all config overrides can be specified here. 
# The update operation will not touch this file.
# """
DRIVE_LOOP_HZ = 5   
CAMERA_TYPE = "WEBCAM" 
DRIVE_TRAIN_TYPE = "SUNFOUNDER_PWM"

#STEERING
#used for the DRIVE_TRAIN_TYPE=SUNFOUNDER_PWM
STEERING_CHANNEL = 0            #channel on the 9685 pwm board 0-15
STEERING_LEFT_PWM = 260         #pwm value for full left steering
STEERING_RIGHT_PWM = 500        #pwm value for full right steering

#THROTTLE
#used for the DRIVE_TRAIN_TYPE=SUNFOUNDER_PWM
THROTTLE_CHANNEL = 4            #channel on the 9685 pwm board 0-15
THROTTLE_MAX_PWM = 1200         #pwm value for max movement (throttle ->= 1, -1)
THROTTLE_MIN_PWM = 500          #pwm value for min movement (throttle -> 0)
#THROTTLE_ZERO_PWM = 0          #pwm value for no movement (throttle = 0)


#JOYSTICK
CONTROLLER_TYPE='ps4'
USE_FPV = False                     # send camera data to FPV webserver

#REMOTE_PILOT
REMOTE_PILOT_HOST = "192.168.2.35" # remote pilot server hostname or ip
REMOTE_PILOT_PORT = 9090           # remote pilot server port
