from experiment.experiment import Experiment
from experiment.action import Action
from hardware.train.train import Train
from hardware.motor.motor import Motor
from hardware.motor.sensor import Sensor
from hardware.motor.motor import Direction

from meassure.meassure import Meassure

import datetime
import time

NO_DOMAIN = 11
total_steps = 8400

#sens = Sensor(
#    serial="/dev/ttyACM3"
#)

sens = None

train = Train()

motor = Motor(
    sensors=sens,
    motor_params={
        'com_port': '/dev/ttyACM0',
    },
    motor_settings={
        'ACC_KVAL' : 2,
        'DEC_KVAL' : 0,
        'RUN_KVAL' : 4,
        'HOLD_KVAL': 0,
        'MAX_SPEED': 1000,
        'FULL_SPEED': 1000,
        'ACC': 1000,
        'DEC': 500,
        'step_mode': 'FS'
    }
)

meassure = Meassure(
    kwargs={
        "interface": "wlp0s20f3"
    }
)

train_delta = datetime.timedelta(seconds=1)

ACTIONS = [
    Action(
        name="MEASSURE",
        obj=meassure.do,
        kwargs={
            "kwargs":{
                "num": 2,
                "mac_sa": "d8:3a:dd:e5:66:2c",
                "mac_da": "127c6136fcc2",
                "channel": 44
            }
        }
    ),
    Action(
        name="MOTOR_STEP",
        obj=motor.drive,
        kwargs={
            "direction": Direction.FWD,
            "steps": 400,
            "fs_only": False
        }
    )
]
ACTIONS_RESET = [
    Action(
        name="MOTOR_RESET_POS",
        obj=motor.reset,
        kwargs={
            "direction": Direction.BWD,
            "steps": total_steps,
            "fs_only": False
        }
    )
]

exp = Experiment(
    actions=ACTIONS,
    actions_reset=ACTIONS_RESET,
    delta=datetime.timedelta(seconds=1),
    stop_callback=lambda x=total_steps: motor.check_finished(steps=x),
    stop_callback_reset=lambda x=total_steps: motor.check_home(steps=x)
)

for x in range(NO_DOMAIN):
    exp.run()
    time.sleep(exp.m_delta.total_seconds())
    exp.reset()
    train.drive(delta=datetime.timedelta(seconds=0.5))
    time.sleep(10)