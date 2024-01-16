import math
import os
import sys
sys.path.append('/home/lalase/Music/ultra_sonic/sample/sample_program/togikai/togikai_function/')
import togikai_drive
import togikai_ultrasonic
import signal
import RPi.GPIO as GPIO
import Adafruit_PCA9685
import time
import numpy as np

li=[]

def detect_stroke(ab, bc ,bd):
	ab = ab + 8
	bd = bd + 8
	bc = bc + 8
	print(ab ,bd , bc)
	ac = math.sqrt(ab * ab + bc * bc - 1.414 * ab * bc)
	cd = math.sqrt(bc * bc + bd * bd - 1.414* bc * bd)
	if len(li)<4:
		li.append(math.sqrt(abs(ab * ab + bd * bd - (ac + cd) * (ac + cd))))
		return 100
	li[0]=li[1]
	li[1]=li[2]
	li[2]=li[3]
	li[3]=(math.sqrt(abs(ab * ab + bd * bd - (ac + cd) * (ac + cd))))
	return sum(li)/4

GPIO.setmode(GPIO.BCM)

#超音波センサ初期設定
# Triger -- Fr:15, FrLH:13, RrLH:35, FrRH:32, RrRH:36
t_list=[14, 23, 8, 5]
GPIO.setup(t_list,GPIO.OUT,initial=GPIO.LOW)
# Echo -- Fr:26, FrLH:24, RrLH:37, FrRH:31, RrRH:38
e_list=[15, 24, 7, 6]
GPIO.setup(e_list,GPIO.IN)

#PWM制御の初期設定
##モータドライバ:PCA9685のPWMのアドレスを設定
pwm = Adafruit_PCA9685.PCA9685(address=0x40)
##動作周波数を設定
pwm.set_pwm_freq(60)

#アライメント調整済みPWMパラメータ読み込み
PWM_PARAM = togikai_drive.ReadPWMPARAM(pwm)

try:
	while True:
		FRdis = togikai_ultrasonic.Mesure(GPIO,time,t_list[2],e_list[2])
		#FrLHセンサ距離
		LHdis = togikai_ultrasonic.Mesure(GPIO,time,t_list[1],e_list[1])
		#FrRHセンサ距離
		RHdis = togikai_ultrasonic.Mesure(GPIO,time,t_list[0],e_list[0])
		Left_dis = togikai_ultrasonic.Mesure(GPIO,time,t_list[3],e_list[3])
		
		print(FRdis,LHdis,RHdis,Left_dis)
		print(detect_stroke(FRdis,LHdis,Left_dis))
		time.sleep(0.5)


except KeyboardInterrupt:
	print('stop!')
	togikai_drive.Accel(PWM_PARAM,pwm,time,0)
	togikai_drive.Steer(PWM_PARAM,pwm,time,0)
	GPIO.cleanup()