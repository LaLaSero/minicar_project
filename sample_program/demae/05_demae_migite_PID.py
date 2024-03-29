import os
import sys
sys.path.append('/home/pi/togikai/togikai_function/')
import togikai_drive
import togikai_ultrasonic
import signal
import RPi.GPIO as GPIO
import Adafruit_PCA9685
import time
import numpy as np

####################↓パラメータ↓####################
#前壁との最小距離
Cshort = 130 #FRdis = 130
Cshort_stop =20
#右左折判定基準
short = 20 #RHdis,LHdis = 60
Target_dis = 30 #migite_target_distance
#モーター出力
FORWARD_S = 60  #<=100
FORWARD_C = 40 #<=100
REVERSE = -60 #<=100
#STEER
LEFT = 80 #<=100
RIGHT = -80 #-100<=
#PD control
Kp_RH = -3
Kp_LH = -3
Kd_RH = 1
Kd_LH = 1
Ki_RH = 0.1
Ki_LH = 0.1
min_RHdis = min(RHdis,RRHdis)
min_RHdis0 = min_RHdis
####################↑パラメータ↑####################

####################↓初期化処理↓####################

# GPIOピン番号の指示方法
GPIO.setmode(GPIO.BOARD)

# GPIO初期化
GPIO.cleanup()

#超音波センサ初期設定
# Triger -- Fr:15, FrLH:13, RrLH:35, FrRH:32, RrRH:36
t_list=[15,13,35,32,36]
GPIO.setup(t_list,GPIO.OUT,initial=GPIO.LOW)
# Echo -- Fr:26, FrLH:24, RrLH:37, FrRH:31, RrRH:38
e_list=[26,24,37,31,38]
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

#操舵、駆動モーターの初期化
togikai_drive.Accel(PWM_PARAM,pwm,time,0)
togikai_drive.Steer(PWM_PARAM,pwm,time,0)

#データ記録用配列作成
d = np.zeros(6)

#PID 初期化
integral_delta_dis = 0
####################↑初期化処理↑####################

#一時停止（Enterを押すとプログラム実行開始）
print('Press any key to continue')
input()

#開始時間
start_time = time.time()
t = start_time
#ここから走行用プログラム
try:
	while True:
		# #Frセンサ距離
		# FRdis = togikai_ultrasonic.Mesure(GPIO,time,15,26)
		# #FrLHセンサ距離
		# LHdis = togikai_ultrasonic.Mesure(GPIO,time,13,24)
		# #FrRHセンサ距離
		# RHdis = togikai_ultrasonic.Mesure(GPIO,time,32,31)
		# #RrLHセンサ距離
		# RLHdis = togikai_ultrasonic.Mesure(GPIO,time,35,37)
		# #RrRHセンサ距離
		# RRHdis = togikai_ultrasonic.Mesure(GPIO,time,36,38)
		#Frセンサ距離
		FRdis = togikai_ultrasonic.Mesure(GPIO,time,t_list[2],e_list[2])
		#FrLHセンサ距離
		LHdis = togikai_ultrasonic.Mesure(GPIO,time,t_list[1],e_list[1])
		#FrRHセンサ距離
		RHdis = togikai_ultrasonic.Mesure(GPIO,time,t_list[0],e_list[0])
		Left_dist = togikai_ultrasonic.Mesure(GPIO,time,t_list[3],e_list[3])

		#時間更新
		t_before = t
		t = time.time()
		delta_t = t-t_before
		#右手法最小距離更新
		min_RHdis_before = min_RHdis
		min_RHdis = min(RHdis,RRHdis)
		#目標値までの差更新
		delta_dis = min_RHdis - Target_dis
		#目標値までの差積分更新
		integral_delta_dis += delta_dis
		#速度更新
		v = (min_RHdis - min_RHdis_before)/delta_t

		#ステア値更新（!!!PID選択!!!）
		#STEER_migite = RIGHT
		STEER_migite = Kp_RH*delta_dis #migite_Steer_P_SEIGYO
		#STEER_migite = Kp_RH*delta_dis - Kd_RH*v #migite_Steer_PD_SEIGYO
		#STEER_migite = Kp_RH*delta_dis - Kd_RH*v + Ki_RH*integral_delta_dis #migite_Steer_PID_SEIGYO

		if min_RHdis > Target_dis:    
			print("右旋回_migite"+'：　%.1f' %STEER_migite)
		else:
			###PID使うときはここもコメントアウト###
			#STEER_migite = LEFT
			###PID使うときはここもコメントアウト###
			print("左旋回_migite"+'：　%.1f' %STEER_migite)

		#出力値更新
		togikai_drive.Accel(PWM_PARAM,pwm,time,FORWARD_S)
		togikai_drive.Steer(PWM_PARAM,pwm,time,STEER_migite)

		#そのほか制御
		if FRdis < Cshort or LHdis < short or RHdis < short:
			if (FRdis < Cshort_stop ): #or LHdis < Cshort_stop or RHdis < Cshort_stop
				togikai_drive.Accel(PWM_PARAM,pwm,time,REVERSE)
				#togikai_drive.Accel(PWM_PARAM,pwm,time,0) #Stop if something is in front of you
				togikai_drive.Steer(PWM_PARAM,pwm,time,0)
				time.sleep(0.1)
				togikai_drive.Accel(PWM_PARAM,pwm,time,0)
				togikai_drive.Steer(PWM_PARAM,pwm,time,0)
				#GPIO.cleanup()
				#d = np.vstack([d,[time.time()-start_time, FRdis, RHdis, LHdis, RRHdis, RLHdis]])
				#np.savetxt('/home/pi/code/record_data.csv', d, fmt='%.3e')
				print('Stop!')
				print('Press any key to continue')
				input()
				#break
			"""
			elif LHdis < RHdis:
			togikai_drive.Accel(PWM_PARAM,pwm,time,FORWARD_C)
			togikai_drive.Steer(PWM_PARAM,pwm,time,RIGHT) #original = "+"
			comment = "右旋回"
			print(comment)
			else :
			togikai_drive.Accel(PWM_PARAM,pwm,time,FORWARD_C)
			togikai_drive.Steer(PWM_PARAM,pwm,time,LEFT) #original = "-"
			comment = "左旋回"
			print(comment)
			"""
						
		#距離データを配列に記録
		d = np.vstack([d,[time.time()-start_time, FRdis, RHdis, LHdis, RRHdis, RLHdis]])
		#距離を表示
		print('RrLH:{4:.1f} , FrLH:{2:.1f}, Fr:{0:.1f} , FrRH:{1:.1f} , RrRH:{3:.1f}'.format(FRdis,RHdis,LHdis,RRHdis,RLHdis))
		min_RHdis0 = min_RHdis
		#time.sleep(0.05)

except KeyboardInterrupt:
	print('stop!')
	np.savetxt('/home/pi/code/record_data.csv', d, fmt='%.3e')
	togikai_drive.Accel(PWM_PARAM,pwm,time,0)
	togikai_drive.Steer(PWM_PARAM,pwm,time,0)
	GPIO.cleanup()
