# Released by rdb under the Unlicense (unlicense.org)
# Based on information from:
# https://www.kernel.org/doc/Documentation/input/joystick-api.txt

#https://pimylifeup.com/raspberry-pi-wiimote-controllers/
#https://www.instructables.com/id/Wiimote-Controller-Configuration-for-Raspberry-Pi-/
#https://wiibrew.org/wiki/Wiimote
#https://github.com/ricorx7/donkey/blob/master/donkeycar/parts/controllers/joystick.py
#https://gist.github.com/rdb/8864666
#https://discourse.panda3d.org/t/game-controllers-on-linux-without-pygame/14128

import os, struct, array, time
from fcntl import ioctl


class WiiMote():
    # These constants were borrowed from linux/input.h
    axis_names = {
        0x00 : 'x',
        0x01 : 'y',
        0x02 : 'z',
        0x03 : 'rx',
        0x04 : 'ry',
        0x05 : 'rz',
        0x06 : 'trottle',
        0x07 : 'rudder',
        0x08 : 'wheel',
        0x09 : 'gas',
        0x0a : 'brake',
        0x10 : 'hat0x',
        0x11 : 'hat0y',
        0x12 : 'hat1x',
        0x13 : 'hat1y',
        0x14 : 'hat2x',
        0x15 : 'hat2y',
        0x16 : 'hat3x',
        0x17 : 'hat3y',
        0x18 : 'pressure',
        0x19 : 'distance',
        0x1a : 'tilt_x',
        0x1b : 'tilt_y',
        0x1c : 'tool_width',
        0x20 : 'volume',
        0x28 : 'misc',
    }

    button_names = {
        0x120 : 'trigger',
        0x121 : 'thumb',
        0x122 : 'thumb2',
        0x123 : 'top',
        0x124 : 'top2',
        0x125 : 'pinkie',
        0x126 : 'base',
        0x127 : 'base2',
        0x128 : 'base3',
        0x129 : 'base4',
        0x12a : 'base5',
        0x12b : 'base6',
        0x12f : 'dead',
        0x130 : 'a',
        0x131 : 'b',
        0x132 : 'c',
        0x133 : 'x',
        0x134 : 'y',
        0x135 : 'z',
        0x136 : 'tl',
        0x137 : 'tr',
        0x138 : 'tl2',
        0x139 : 'tr2',
        0x13a : 'select',
        0x13b : 'start',
        0x13c : 'mode',
        0x13d : 'thumbl',
        0x13e : 'thumbr',

        0x220 : 'dpad_up',
        0x221 : 'dpad_down',
        0x222 : 'dpad_left',
        0x223 : 'dpad_right',

        # XBox 360 controller uses these codes.
        0x2c0 : 'dpad_left',
        0x2c1 : 'dpad_right',
        0x2c2 : 'dpad_up',
        0x2c3 : 'dpad_down',
    }

    def __init__(self):

        # Iterate over the joystick devices.
        print('Available devices:')

        for fn in os.listdir('/dev/input'):
            if fn.startswith('js'):
                print('  /dev/input/%s' % (fn))

        # We'll store the states here.
        self.axis_states = {}
        self.button_states = {}
        self.axis_map = []
        self.button_map = []

        # Open the joystick device.
        fn = '/dev/input/js0'
        print('Opening %s...' % fn)
        self.jsdev = open(fn, 'rb')

        # Get the device name.
        #buf = bytearray(63)
        buf = array.array('B', [0] * 64)
        ioctl(self.jsdev, 0x80006a13 + (0x10000 * len(buf)), buf) # JSIOCGNAME(len)
        js_name = buf.tobytes().decode('utf-8')
        print('Device name: %s' % js_name)

        # Get number of axes and buttons.
        buf = array.array('B', [0])
        ioctl(self.jsdev, 0x80016a11, buf) # JSIOCGAXES
        num_axes = buf[0]

        buf = array.array('B', [0])
        ioctl(self.jsdev, 0x80016a12, buf) # JSIOCGBUTTONS
        num_buttons = buf[0]

        # Get the axis map.
        buf = array.array('B', [0] * 0x40)
        ioctl(self.jsdev, 0x80406a32, buf) # JSIOCGAXMAP

        for axis in buf[:num_axes]:
            axis_name = WiiMote.axis_names.get(axis, 'unknown(0x%02x)' % axis)
            self.axis_map.append(axis_name)
            self.axis_states[axis_name] = 0.0

        # Get the button map.
        buf = array.array('H', [0] * 200)
        ioctl(self.jsdev, 0x80406a34, buf) # JSIOCGBTNMAP

        for btn in buf[:num_buttons]:
            btn_name = WiiMote.button_names.get(btn, 'unknown(0x%03x)' % btn)
            self.button_map.append(btn_name)
            self.button_states[btn_name] = 0

        print( '%d axes found: %s' % (num_axes, ', '.join(self.axis_map)))
        print( '%d buttons found: %s' % (num_buttons, ', '.join(self.button_map)))

        self.running = True
        self.angle = 0.0
        self.throttle = 0.0
        self.drive_mode = 'user'
        self.recording = False

    def run(self):
        self.read_event()
        return self.angle, self.throttle, self.drive_mode, self.recording

    def run_threaded(self):
        return self.angle, self.throttle, self.drive_mode, self.recording

    def shutdown(self):
        self.running = False
        print("stopping wiimote")
        #self.jsdev.close()
        os.close(self.jsdev.fileno())

    def read_event(self):
        evbuf = self.jsdev.read(8)
        if evbuf:
            jstime, jsvalue, jstype, jsnumber = struct.unpack('IhBB', evbuf)

            if jstype & 0x80:
                print ("(initial)")

            if jstype & 0x01:
                button = self.button_map[jsnumber]
                if button == "x" or button =="y":
                    #emergency stop
                    self.throttle = 0.0
                    self.angle = 0.0
                if button:
                    self.button_states[button] = jsvalue
                    if jsvalue:
                        print ("%s pressed" % (button))
                    else:
                        print( "%s released" % (button))

            if jstype & 0x02:
                axis = self.axis_map[jsnumber]
                if axis:
                    fvalue = jsvalue / 32767.0
                    self.axis_states[axis] = fvalue
                    print( "%s: %.3f" % (axis, fvalue))
                if axis == "x":
                    self.angle = fvalue
                elif axis == "y":
                    self.throttle = fvalue

            print("s %f, %f, %s, %d" % (self.angle, self.throttle, self.drive_mode, self.recording))

    def update(self):
        # keep looping infinitely until the thread is stopped
        # Main event loop
        while self.running:
            self.read_event()
