
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

# GPIOピン番号の指示方法
GPIO.setmode(GPIO.BOARD)

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
Cshort = 130 #FRdis = 130
Cshort_stop =20
#右左折判定基準
short = 20 #RHdis,LHdis = 60
Target_dis = 30 #migite_target_distance
#モーター出力
FORWARD_S = 45  #<=100
FORWARD_C = 30 #<=100
REVERSE = -60 #<=100
#STEER
LEFT = 100 #<=100
RIGHT = -100 #<=100
#PD control
Kp_RH = -3
Kp_LH = -3
Kd_RH = 1
Kd_LH = 1

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

#bibun shokika
t0 = start_time
RHdis = togikai_ultrasonic.Mesure(GPIO,time,32,31)
RRHdis = togikai_ultrasonic.Mesure(GPIO,time,36,38)
min_RHdis = min(RHdis,RRHdis)
min_RHdis0 = min_RHdis

#ここから走行用プログラム
try:
    while True:
        #Frセンサ距離
        FRdis = togikai_ultrasonic.Mesure(GPIO,time,15,26)
        #FrLHセンサ距離
        LHdis = togikai_ultrasonic.Mesure(GPIO,time,13,24)
        #FrRHセンサ距離
        RHdis = togikai_ultrasonic.Mesure(GPIO,time,32,31)
        #RrLHセンサ距離
        RLHdis = togikai_ultrasonic.Mesure(GPIO,time,35,37)
        #RrRHセンサ距離
        RRHdis = togikai_ultrasonic.Mesure(GPIO,time,36,38)
        min_RHdis = min(RHdis,RRHdis)
       
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
        elif min_RHdis > Target_dis:#RRHdis > Target_dis
             STEER_migite = -80
             #STEER_migite = Kp_RH*(min_RHdis - Target_dis) #migite_Steer_P_SEIGYO
             #STEER_migite = Kp_RH*(min_RHdis - Target_dis)-Kd_RH*(min_RHdis-min_RHdis0)/(time.time()-t0) #migite_Steer_PD_SEIGYO
             togikai_drive.Accel(PWM_PARAM,pwm,time,FORWARD_S)
             togikai_drive.Steer(PWM_PARAM,pwm,time,STEER_migite)#STEER_migite
             comment = "右旋回_migite"
             print(comment)
             print('%.1f' %STEER_migite)
        else:
             STEER_migite = 80
             #STEER_migite = Kp_LH *(min_RHdis - Target_dis) #migite_Steer_P_SEIGYO
             #STEER_migite = Kp_RH*(min_RHdis - Target_dis)-Kd_LH*(min_RHdis-min_RHdis0)/(time.time()-t0) #migite_Steer_PD_SEIGYO
             togikai_drive.Accel(PWM_PARAM,pwm,time,FORWARD_S)
             togikai_drive.Steer(PWM_PARAM,pwm,time,STEER_migite)#STEER_migite
             comment = "左旋回_migite"
             print(comment)
             print('%.1f' %STEER_migite)

        #距離データを配列に記録
        d = np.vstack([d,[time.time()-start_time, FRdis, RHdis, LHdis, RRHdis, RLHdis]])
        #距離を表示
        print('RrLH:{4:.1f} , FrLH:{2:.1f}, Fr:{0:.1f} , FrRH:{1:.1f} , RrRH:{3:.1f}'.format(FRdis,RHdis,LHdis,RRHdis,RLHdis))
        t0 = time.time()
        min_RHdis0 = min_RHdis
        #time.sleep(0.05)

except KeyboardInterrupt:
    print('stop!')
    np.savetxt('/home/pi/code/record_data.csv', d, fmt='%.3e')
    togikai_drive.Accel(PWM_PARAM,pwm,time,0)
    togikai_drive.Steer(PWM_PARAM,pwm,time,0)
    GPIO.cleanup()
