import cwiid
import time
import Adafruit_PCA9685

#connecting to the wiimote. This allows several attempts
# as first few often fail.
pwm = Adafruit_PCA9685.PCA9685()
pwm.set_pwm_freq(60)
pwm.set_pwm(4, 0, 0)
print( 'Press 1+2 on your Wiimote now...')
wm = None
i=2
while not wm:
	try:
		wm=cwiid.Wiimote()
	except RuntimeError:
		if (i>5):
			print("cannot create connection")
			pwm.set_pwm(4, 0, 0)
			quit()
		print( "Error opening wiimote connection")
		print( "attempt " + str(i))
		i +=1

#set wiimote to report button presses and accelerometer state
wm.rpt_mode = cwiid.RPT_BTN | cwiid.RPT_ACC

#turn on led to show connected
wm.led = 1

#activate the servos
#pwm.setPWM(4,0)
#servos.setSpeeds(0,0)
#print state every second

def setSeeds(s1, s2):
    print("s %d %d" % (s1, s2))
    #pwm.set_pulse(h

while True:
	buttons = wm.state['buttons']
	if (buttons & cwiid.BTN_B):
		#boost mode
		speedModifier=200
		speedModifier2=50
	else:
		speedModifier=150
		speedModifier2=100
	if (buttons & cwiid.BTN_2):
		#print((wm.state['acc'][1]-125))
		setSpeeds((speedModifier - wm.state['acc'][1]),wm.state['acc'][1] -speedModifier2)
	elif (buttons & cwiid.BTN_1):
		#print ~(wm.state['acc'][1]-125)
		setSpeeds(~(speedModifier - wm.state['acc'][1]),~(wm.state['acc'][1] -speedModifier2))
	else:
		#print("stop")
		setSpeeds(0,0)
	time.sleep(0.2)
