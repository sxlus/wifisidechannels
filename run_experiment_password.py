from experiment.experiment import NumericalPasswordSCExperiment
from experiment.action import Action
from hardware.train.train import Train
from hardware.motor.motor import Motor
from hardware.motor.motor import Direction

from meassure.meassure import Meassure

import datetime
import time

meassure = Meassure(
    kwargs = {
        "interface": "wlp0s20f3",
        "channel": 44,
        "num": 1,
        "mac_sa": "d83add30620c"
    })

motor = Motor(
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

exp = NumericalPasswordSCExperiment(
    delta=datetime.timedelta(seconds=0),
    max_steps       = 8000,
    password_file   = "test_passwords.txt",
    max_positions   = 10,
)

train = Train()
train_delta = datetime.timedelta(seconds=1)

NO_DOMAIN = 1

while exp.m_next_pw_idx < len(exp.m_passwords):
    exp.create_actions_from_password(
        motor=motor,
        meassure=meassure
    )
    for i in range(NO_DOMAIN):
        exp.run()
        train.drive(delta=train_delta)