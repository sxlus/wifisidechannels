from fastdriver_simple import FastdriverSimple
import sys

#start or change speed use Arguments: start <num_motors> <speed> [all or motornumbers to start] eg: start 2 50 0 1 to start motor 0 and 1

if(len(sys.argv)<4):
    raise Exception('Invalid number of arguments')

name = sys.argv[1]
numMotor = int(sys.argv[2])

motor_params = {
    'com_port': 'COM4',
    'baud_rate': 115200,
    'num_motors': numMotor,
    'motor_settings': {
      'ACC_KVAL' : 100,
      'DEC_KVAL' : 100,
      'RUN_KVAL' : 100,
      'HOLD_KVAL': 50,
      'MAX_SPEED': 100,
      'FULL_SPEED': 100,
      'ACC': 15,
      'DEC': 15,
      'step_mode': 'FS'
    },
    'stop_at_end': False 
}

fastdriver = FastdriverSimple(**motor_params)

if(name == "start"):
    speed = int(sys.argv[3])
    if(len(sys.argv)<5):
        raise Exception('Invalid number of arguments')
    if(sys.argv[4] == "all"):
        for i in range(0, numMotor):
            fastdriver.start_rotate(i, "fwd", speed)
    else:
        for i in range(4,len(sys.argv)):
            fastdriver.start_rotate(int(sys.argv[i]),"fwd",speed)

if(name == "stop"):
    if(sys.argv[3] == "all"):
        fastdriver.stop_rotate()
    else:
        for i in range(3,len(sys.argv)):
            fastdriver.stop_rotate(int(sys.argv[i]))






