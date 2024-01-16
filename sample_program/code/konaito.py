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
import math

def detect_stroke(ab, bc ,bd):
	ac = sqrt(ab * ab + bc * bc - 1.414 * ab * bc)
	return (ab * ab + bd * bd - (ac + cd) * (ac + cd))

# GPIOピン番号の指示方法
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

#Gard 210523
#Steer Right
if PWM_PARAM[0][0] - PWM_PARAM[0][1] >= 100: #No change!
    PWM_PARAM[0][0] = PWM_PARAM[0][1] + 100  #No change!
    
#Steer Left
if PWM_PARAM[0][1] - PWM_PARAM[0][2] >= 100: #No change!
    PWM_PARAM[0][2] = PWM_PARAM[0][1] - 100  #No change!


#パラメータ
#前壁との最小距離
#Cshort = 30
Cshort = 10
#右左折判定基準
short = 70
#モーター出力
FORWARD_S = 18 #<=100
FORWARD_C = 13 #<=100
REVERSE = -30 #<=100
#Stear
LEFT = 100 #<=100
RIGHT = -100
 #<=100
#データ記録用配列作成
d = np.zeros(6)
#操舵、駆動モーターの初期化
togikai_drive.Accel(PWM_PARAM,pwm,time,0)
togikai_drive.Steer(PWM_PARAM,pwm,time,0)

#一時停止（Enterを押すとプログラム実行開始）
print('Press any key to continue')
input()

#開始時間
start_time = time.time()
#ここから走行用プログラム
try:
	while True:
		#Frセンサ距離
		FRdis = togikai_ultrasonic.Mesure(GPIO,time,t_list[2],e_list[2])
		#FrLHセンサ距離
		LHdis = togikai_ultrasonic.Mesure(GPIO,time,t_list[1],e_list[1])
		#FrRHセンサ距離
		RHdis = togikai_ultrasonic.Mesure(GPIO,time,t_list[0],e_list[0])
		Left_dist = togikai_ultrasonic.Mesure(GPIO,time,t_list[3],e_list[3])
		#RrLHセンサ距離
		RLHdis = 200
		# togikai_ultrasonic.Mesure(GPIO,time,t_list[3],e_list[3])
		#RrRHセンサ距離
		RRHdis = 200
		# togikai_ultrasonic.Mesure(GPIO,time,t_list[4],e_list[4])
		if FRdis >= Cshort:
			if LHdis <= short and RHdis >= short:
				togikai_drive.Accel(PWM_PARAM,pwm,time,FORWARD_C)
				togikai_drive.Steer(PWM_PARAM,pwm,time,RIGHT) #original = "+"
				comment = "右旋回"
				print(comment)
			elif LHdis > short and RHdis < short:
				togikai_drive.Accel(PWM_PARAM,pwm,time,FORWARD_C)
				togikai_drive.Steer(PWM_PARAM,pwm,time,LEFT) #original = "-"
				comment = "左旋回"
				print(comment)
			elif LHdis < short and RHdis < short:
				if (LHdis - RHdis)>10:
					togikai_drive.Accel(PWM_PARAM,pwm,time,FORWARD_C)
					togikai_drive.Steer(PWM_PARAM,pwm,time,LEFT) #original = "-"
					comment = "左旋回"
					print(comment)
				elif(RHdis - LHdis) > 10:
					togikai_drive.Accel(PWM_PARAM,pwm,time,FORWARD_C)
					togikai_drive.Steer(PWM_PARAM,pwm,time,RIGHT) #original = "+"
					comment = "右旋回"
					print(comment)
				else:
					togikai_drive.Accel(PWM_PARAM,pwm,time,FORWARD_S)
					togikai_drive.Steer(PWM_PARAM,pwm,time,0)
					comment = "直進中"
					print(comment)
			else:
				# if FRdis>30:
					
				# 	togikai_drive.Accel(PWM_PARAM,pwm,time,FORWARD_S+15)
				# 	togikai_drive.Steer(PWM_PARAM,pwm,time,0)
				# else:
				togikai_drive.Accel(PWM_PARAM,pwm,time,FORWARD_S)
				togikai_drive.Steer(PWM_PARAM,pwm,time,0)
				comment = "直進中"
				print(comment)
		elif time.time()-start_time < 1:
			pass
		else:
			# togikai_drive.Accel(PWM_PARAM,pwm,time,REVERSE)
			#togikai_drive.Accel(PWM_PARAM,pwm,time,0) #Stop if something is in front of you
			togikai_drive.Steer(PWM_PARAM,pwm,time,0)
			time.sleep(0.1)
			togikai_drive.Accel(PWM_PARAM,pwm,time,0)
			togikai_drive.Steer(PWM_PARAM,pwm,time,0)
			GPIO.cleanup()
			d = np.vstack([d,[time.time()-start_time, FRdis, RHdis, LHdis , RRHdis, RLHdis]])
			np.savetxt('/home/lalase/Music/ultra_sonic/sample/sample_program/code/record_data.csv', d, fmt='%.3e')
			print('Stop!')
			break
		#距離データを配列に記録
		d = np.vstack([d,[time.time()-start_time, FRdis, RHdis, LHdis , RRHdis, RLHdis]])
		#距離を表示
		print('Fr:{0:.1f} , FrRH:{1:.1f} , FrLH:{2:.1f}'.format(FRdis,RHdis,LHdis ,RRHdis,RLHdis))
		time.sleep(0.05)

except KeyboardInterrupt:
	print('stop!')
	np.savetxt('/home/lalase/Music/ultra_sonic/sample/sample_program/code/record_data.csv', d, fmt='%.3e')
	togikai_drive.Accel(PWM_PARAM,pwm,time,0)
	togikai_drive.Steer(PWM_PARAM,pwm,time,0)
	GPIO.cleanup()
