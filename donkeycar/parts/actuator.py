"""
actuators.py
Classes to control the motors and servos. These classes
are wrapped in a mixer class before being used in the drive loop.
"""

import time
import donkeycar as dk


class PCA9685:
    """
    PWM motor controler using PCA9685 boards.
    This is used for most RC Cars
    """
    def __init__(self, channel, frequency=60):
        import Adafruit_PCA9685
        # Initialise the PCA9685 using the default address (0x40).
        self.pwm = Adafruit_PCA9685.PCA9685()
        self.pwm.set_pwm_freq(frequency)
        self.channel = channel

    def set_pulse(self, pulse):
        try:
            self.pwm.set_pwm(self.channel, 0, pulse)
        except OSError as err:
            print("Unexpected issue setting PWM (check wires to motor board): {0}".format(err))

    def run(self, pulse):
        self.set_pulse(pulse)


class PWMSteering:
    """
    Wrapper over a PWM motor cotnroller to convert angles to PWM pulses.
    """
    LEFT_ANGLE = -1
    RIGHT_ANGLE = 1

    def __init__(self, controller=None,
                 left_pulse=290, right_pulse=490):

        self.controller = controller
        self.left_pulse = left_pulse
        self.right_pulse = right_pulse

    def run(self, angle):
        # map absolute angle to angle that vehicle can implement.
        pulse = dk.util.data.map_range(
            angle,
            self.LEFT_ANGLE, self.RIGHT_ANGLE,
            self.left_pulse, self.right_pulse
        )

        self.controller.set_pulse(pulse)

    def shutdown(self):
        self.run(0)  # set steering straight


class PWMThrottle:
    """
    Wrapper over a PWM motor cotnroller to convert -1 to 1 throttle
    values to PWM pulses.
    """
    MIN_THROTTLE = -1
    MAX_THROTTLE = 1

    def __init__(self,
                 controller=None,
                 max_pulse=300,
                 min_pulse=490,
                 zero_pulse=350):

        self.controller = controller
        self.max_pulse = max_pulse
        self.min_pulse = min_pulse
        self.zero_pulse = zero_pulse

        # send zero pulse to calibrate ESC
        self.controller.set_pulse(self.zero_pulse)
        time.sleep(1)

    def run(self, throttle):
        if throttle > 0:
            pulse = dk.util.data.map_range(throttle,
                                           0, self.MAX_THROTTLE,
                                           self.zero_pulse, self.max_pulse)
        else:
            pulse = dk.util.data.map_range(throttle,
                                           self.MIN_THROTTLE, 0,
                                           self.min_pulse, self.zero_pulse)

        self.controller.set_pulse(pulse)

    def shutdown(self):
        self.run(0)  # stop vehicle


class Adafruit_DCMotor_Hat:
    """
    Adafruit DC Motor Controller
    Used for each motor on a differential drive car.
    """
    def __init__(self, motor_num):
        from Adafruit_MotorHAT import Adafruit_MotorHAT
        import atexit

        self.FORWARD = Adafruit_MotorHAT.FORWARD
        self.BACKWARD = Adafruit_MotorHAT.BACKWARD
        self.mh = Adafruit_MotorHAT(addr=0x60)

        self.motor = self.mh.getMotor(motor_num)
        self.motor_num = motor_num

        atexit.register(self.turn_off_motors)
        self.speed = 0
        self.throttle = 0

    def run(self, speed):
        """
        Update the speed of the motor where 1 is full forward and
        -1 is full backwards.
        """
        if speed > 1 or speed < -1:
            raise ValueError("Speed must be between 1(forward) and -1(reverse)")

        self.speed = speed
        self.throttle = int(dk.util.data.map_range(abs(speed), -1, 1, -255, 255))

        if speed > 0:
            self.motor.run(self.FORWARD)
        else:
            self.motor.run(self.BACKWARD)

        self.motor.setSpeed(self.throttle)

    def shutdown(self):
        self.mh.getMotor(self.motor_num).run(Adafruit_MotorHAT.RELEASE)


class SunFounder_ESC:
    def __init__(self,
                 max_pulse=1000,
                 min_pulse=0,
                 zero_pulse=500):
        self.max_pulse = max_pulse
        self.min_pulse = min_pulse
        self.zero_pulse = zero_pulse
        self.throttle = 0

    def getPWM_speed(self, speed):
        """
        Calculate the PWM value from speed, where 1 is full forward and
        -1 is full backwards, 0 is stop.
        """
        if speed == 0:
            direction = SunFounder_Motor_Hat.FORWARD
            self.throttle = 0
        elif speed > 0:
            direction = SunFounder_Motor_Hat.FORWARD
            self.throttle = int(dk.util.data.map_range(speed, 0, 1, SunFounder_Motor_Hat.PWM_MIN_SPEED, SunFounder_Motor_Hat.PWM_MAX_SPEED))
        else:
            direction = SunFounder_Motor_Hat.BACKWARD
            self.throttle = int(dk.util.data.map_range(speed, -1, 0, SunFounder_Motor_Hat.PWM_MAX_SPEED, SunFounder_Motor_Hat.PWM_MIN_SPEED))
        return (direction, self.throttle)

    def getPWM_pulse(self, pulse):
        """
        Calculate the PWM value from pulse
        """
        if pulse == self.zero_pulse:
            direction = SunFounder_Motor_Hat.FORWARD
            self.throttle = 0
        elif pulse > self.zero_pulse:
            direction = SunFounder_Motor_Hat.FORWARD
            self.throttle = int(dk.util.data.map_range(pulse, self.zero_pulse, self.max_pulse, SunFounder_Motor_Hat.PWM_MIN_SPEED, SunFounder_Motor_Hat.PWM_MAX_SPEED))
        else:
            direction = SunFounder_Motor_Hat.BACKWARD
            self.throttle = int(dk.util.data.map_range(pulse, self.min_pulse, self.zero_pulse, SunFounder_Motor_Hat.PWM_MAX_SPEED, SunFounder_Motor_Hat.PWM_MIN_SPEED))
        return (direction, self.throttle)


class SunFounder_Motor_Hat:
    """
    SunFounder DC Motor Controller
    Used for each motor on a differential drive car.
    """
    Motor_A = 17
    Motor_B = 27
    PWM_A = 4
    PWM_B = 5
    FORWARD = False
    BACKWARD = True
    PWM_MAX_SPEED = 1200
    PWM_MIN_SPEED = 500

    def __init__(self,
                 max_pulse=1000,
                 min_pulse=0,
                 zero_pulse=500):
        import RPi.GPIO as GPIO
        import atexit
    
        mode = GPIO.getmode()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SunFounder_Motor_Hat.Motor_A, GPIO.OUT)
        GPIO.setup(SunFounder_Motor_Hat.Motor_B, GPIO.OUT)
        if mode != None:
            GPIO.setmode(mode)

        self.esc = SunFounder_ESC(max_pulse, min_pulse, zero_pulse)
        self.motor_a = PCA9685(SunFounder_Motor_Hat.PWM_A)
        self.motor_b = PCA9685(SunFounder_Motor_Hat.PWM_B)
        GPIO.output(SunFounder_Motor_Hat.Motor_A, SunFounder_Motor_Hat.FORWARD)
        GPIO.output(SunFounder_Motor_Hat.Motor_B, SunFounder_Motor_Hat.FORWARD)
        self.dir = SunFounder_Motor_Hat.FORWARD
        self.motor_a.set_pulse(0)
        self.motor_b.set_pulse(0)

        atexit.register(self.shutdown)
        self.speed = 0
        self.throttle = 0

    def set_pulse(self, pulse):
        dir, pwm = self.esc.getPWM_pulse(pulse)
        self.apply(dir, pwm)

    def apply(self, dir, pwm):
        import RPi.GPIO as GPIO
        if dir != self.dir:
            GPIO.output(SunFounder_Motor_Hat.Motor_A, dir)
            GPIO.output(SunFounder_Motor_Hat.Motor_B, dir)
            self.dir = dir
        if pwm != self.throttle:
            self.motor_a.set_pulse(pwm)
            self.motor_b.set_pulse(pwm)
            self.throttle = pwm

    def run(self, speed):
        """
        Update the speed of the motor where 1 is full forward and
        -1 is full backwards.
        """
        if speed > 1 or speed < -1:
            raise ValueError("Speed must be between 1(forward) and -1(reverse)")

        self.speed = speed
        dir, pwm = self.esc.getPWM_speed(speed)
        self.apply(dir, pwm)

    def shutdown(self):
        self.motor_a.run(0)
        self.motor_b.run(0)
