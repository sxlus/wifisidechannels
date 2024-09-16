import datetime
from enum import Enum
import time
import typing
import numpy as np

import hardware.motor.sensor as sensor
import hardware.motor.fastdriver_simple as fastdriver
import hardware.motor.fastdriver as fastdriver

class Direction(Enum):
    FWD = "fwd"
    BWD = "bwd"

class Motor:
    m_driver: fastdriver.FastdriverController = None
    m_motor_params = {
        'com_port': 'COM4',
        'baud_rate': 115200,
        'num_motors': 1,
        'motor_settings': {
            'ACC_KVAL' : 100,
            'DEC_KVAL' : 100,
            'RUN_KVAL' : 100,
            'HOLD_KVAL': 10,
            'MAX_SPEED': 100,
            'FULL_SPEED': 100,
            'ACC': 15,
            'DEC': 15,
            'step_mode': 'FS'
        },
        'stop_at_end': False,
}

    m_sensors:      sensor.Sensor = None
    m_total_steps:  int = 0
    m_speed_set:    int = 1000
    m_speed_home:   int = 500

    def __init__(
            self,
            motor_params: dict = {},
            motor_settings: dict = {},
            sensors: sensor.Sensor | None = None,
            speed_home: int | None = None):
        self.m_motor_params["motor_settings"] |= motor_settings
        self.m_motor_params |= motor_params
        self.m_driver = fastdriver.FastdriverController(**(self.m_motor_params))
        self.m_sensors = sensors
        self.m_speed_set = x if (x:= motor_settings.get("MAX_SPEED", None)) is not None else self.m_speed_set
        self.m_speed_home = speed_home if speed_home is not None else self.m_speed_home

    def drive(
            self,
            direction: Direction = Direction.FWD,
            speed: int | None = None,
            steps: int | None = None,
            delta: datetime.timedelta | None = None,
            motor_id: int | None = None,
            fs_only: bool = True) -> bool:

        if motor_id is not None:
            motor_id = range(motor_id, motor_id+1)
        else:
            motor_id = range(self.m_motor_params.get("num_motors", 1))
        if speed is None:
            speed = self.m_motor_params["motor_settings"].get("MAX_SPEED")
        if speed is None:
            print(f"[ MOTOR ][ DRIVE ][ ERROR ]: speed not set.")
            return False
        try:        
            if isinstance(steps, int):
                for id in motor_id:
                    #print("* Driving steps:", steps)
                    self.m_driver.move(id, steps, direction.value, fs_only=fs_only)
                    self.m_total_steps = (self.m_total_steps - steps) if (direction == Direction.BWD) else (self.m_total_steps + steps)
                    #print("--- ", self.m_total_steps)
                    if delta is not None:
                        time.sleep(delta.total_seconds())
                    else:
                        while self.check_moving(motor_id=id):
                            time.sleep(0.05)
            else:
                for id in motor_id:
                    self.m_driver.start_rotate(id, direction.value, speed)
                    if delta is not None:
                        time.sleep(delta.total_seconds())
                        self.stop()
        except Exception as r:
            print(f"[Motor][drive] encountered error: {r}")
            return False
        return True

    def stop(
            self,
            motor_id: int | None = None) -> bool:

        try:
            if motor_id is None:
                self.m_driver.stop_rotate()
            else:
                self.m_driver.stop_rotate(board=motor_id)
        except Exception as r:
            print(f"[Motor][stop] encountered error {r}")
            return False
        return True

    def get_position(self, steps = None) -> int:
        return self.m_total_steps if steps is not None else 0 if self.m_sensors is None else self.m_sensors.poll()

    def check_finished(self, steps = None) -> bool:
        #print(self.get_position())
        if self.get_position(steps=steps) >= ((len(self.m_sensors)-1) if steps is None else steps):
            return True
        return False

    def check_home(self, steps = None) -> bool:
        if self.get_position(steps = steps) == 0:
            return True
        return False

    def check_moving(self, motor_id: int | None = None):
        #print(self.m_driver.get_status(motor_id if motor_id is not None else 0)[0])
        return True if self.m_driver.get_status(motor_id if motor_id is not None else 0)[0] not in [32266, 32274, 32278, 32282, 32258, 32286] else False

    def reset(
            self,
            direction: Direction = Direction.BWD,
            speed: int | None = None,
            steps: int | None = None,
            delta: datetime.timedelta | None = None,
            motor_id: int | None = None,
            fs_only: bool = False,
            go_until: bool = False,
    ) -> bool:

        if speed is None:
            speed = self.m_speed_home
        if not go_until:
            return self.drive(
                direction=direction,
                speed=speed,
                steps=steps,
                delta=delta,
                motor_id=motor_id,
                fs_only=fs_only
            )
        else:
            self.m_driver.go_until(
                board=motor_id if motor_id is not None else 0,
                speed=speed,
                action="reset_abspos",
                direction=direction.value
            )
            self.m_total_steps = 0
            return True

