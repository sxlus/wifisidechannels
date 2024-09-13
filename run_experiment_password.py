import datetime
import time
import os
import pathlib
import multiprocessing as mp

from experiment.experiment import NumericalPasswordSCExperiment
from experiment.action import Action

from hardware.train.train import Train
from hardware.motor.motor import Motor
from hardware.motor.motor import Direction

from meassure.meassure import Meassure



SPEED = 1000
NO_DOMAIN = 25
NUMBER_OF_CHUNKS = 16
TRAIN_DELTA_SECONDS = 0.5
PHY_DOMAIN = "WILDE_13"
PASSWORD_FILE = "3_all_passwords.txt"
CWD = os.getcwd()
DSD = pathlib.Path(os.path.join(CWD, "EXPERIMENT", PHY_DOMAIN))
PASSWORD_FILE = pathlib.Path(os.path.join(CWD, "PASSWORDS", PASSWORD_FILE))
READ_FILE = "MU_2x4_mac_sa_00c0cab63c70.pcapng"
#READ_FILE = "DUMP/AP_to_Phone_default_mac_sa_127c6136fcc2_capture.pcapng"

if __name__ == '__main__':
    #mp.set_start_method("fork")
    meassure = Meassure(
        kwargs = {
            "interface": "wlp0s20f3",
            "channel": 44,
            "num": 8,
            "mac_sa": "00c0cab63c70",# "00c0cab63c70",# ALFA "127c6136fcc2",# PI "d83add30620c"
            "mac_da": "80cc9c339049",# NETGEAR, , d83add30620c
            #"read_file": READ_FILE
        })

    motor = Motor(
        sensors=None,
        motor_params={
            'com_port': '/dev/ttyACM0',
            #"dry": True
        },
        motor_settings={
            'ACC_KVAL' : 40,
            'DEC_KVAL' : 40,
            'RUN_KVAL' : 40,
            'HOLD_KVAL': 20,
            'MAX_SPEED': SPEED,
            'FULL_SPEED': SPEED,
            'ACC': 1000,
            'DEC': 1000,
            'step_mode': 'FS'
        }
    )

    exp = NumericalPasswordSCExperiment(
        delta=datetime.timedelta(seconds=0),
        max_steps       = 8000,
        password_file   = PASSWORD_FILE,
        max_positions   = 10,
    )

    train = Train()
    train_delta = datetime.timedelta(seconds=TRAIN_DELTA_SECONDS)#0)

    try:
        for i in range(0, NO_DOMAIN):
            from_idy = None
            exp.create_actions_from_password(
                motor=motor,
                meassure=meassure,
                number_of_chunks=None,
                from_idy=from_idy,
                v=False
            )
            exp.reset()
            exp.m_next_pw_idx = 0
            while exp.m_next_pw_idx < len(exp.m_passwords):
                exp.create_actions_from_password(
                    motor=motor,
                    meassure=meassure,
                    number_of_chunks=NUMBER_OF_CHUNKS,
                    from_idy=from_idy,
                    v=True
                )
                print(f"[ EXPERIMENT ][ TODO ][ PW ]: {str(exp.m_current_pw)}")
                print(f"[ EXPERIMENT ][ STATUS ][ ALL ]: {str((exp.m_next_pw_idx-1)+i*len(exp.m_passwords)) + '/' + str(len(exp.m_passwords)*NO_DOMAIN)}", end=" - ")
                print(f"[ EXPERIMENT ][ STATUS ][ PW ]: {str(exp.m_next_pw_idx-1) + '/' + str(len(exp.m_passwords))}", end=" - ")
                print(f"[ EXPERIMENT ][ STATUS ][ Domain ]: {i}/{NO_DOMAIN}")
                if not exp.run():
                    print(f"[ EXPERIEMNT ][ RUN ][ WARN ] Redoing current Task.")
                    exp.reset(meassure=meassure)
                    from_idy = 0
                    continue
                from_idy = None

                # async call :)
                exp.store(
                    write_file=pathlib.Path(os.path.join(DSD, "WILDE_13")),
                    meassure=meassure,
                    meta_info={
                        "train_domain": i,
                        "train_delta" : train_delta.total_seconds(),
                        "motor_settings": motor.m_motor_params.get("motor_settings", {}),
                        "number_of_chunks": NUMBER_OF_CHUNKS
                    }
                )
                print(f"[ EXPERIMENT ][ TODO ][ PW ]: {str(exp.m_current_pw)}")
                print(f"[ EXPERIMENT ][ STATUS ][ ALL ]: {str((exp.m_next_pw_idx-1)+i*len(exp.m_passwords)) + '/' + str(len(exp.m_passwords)*NO_DOMAIN)}", end=" - ")
                print(f"[ EXPERIMENT ][ STATUS ][ PW ]: {str(exp.m_next_pw_idx-1) + '/' + str(len(exp.m_passwords))}", end=" - ")
                print(f"[ EXPERIMENT ][ STATUS ][ Domain ]: {i}/{NO_DOMAIN}")

            train.drive(delta=train_delta)

    except KeyboardInterrupt:
        pass
    meassure.terminate()