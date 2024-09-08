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

    m_sensors   : sensor.Sensor = None
    m_total_steps :int = 0
    def __init__(
            self,
            motor_params: dict = {},
            motor_settings: dict = {},
            sensors: sensor.Sensor | None = None):
        self.m_motor_params["motor_settings"] |= motor_settings
        self.m_motor_params |= motor_params
        self.m_driver = fastdriver.FastdriverController(**(self.m_motor_params))
        self.m_sensors = sensors

    def drive(
            self,
            direction: Direction = Direction.FWD,
            speed: int = 100,
            steps: int | None = None,
            delta: datetime.timedelta | None = None,
            motor_id: int | None = None,
            fs_only: bool = True) -> bool:

        if motor_id is not None:
            motor_id = range(motor_id, motor_id+1)
        else:
            motor_id = range(self.m_motor_params.get("num_motors", 1))
        try:        
            if isinstance(steps, int):
                for i in motor_id:
                    print("* Driving steps:", steps)
                    self.m_driver.move(i, steps, direction.value, fs_only=fs_only)
                    self.m_total_steps = (self.m_total_steps - steps) if (direction == Direction.BWD) else (self.m_total_steps + steps)
                    print("--- ", self.m_total_steps)
            else:
                for i in motor_id:
                    self.m_driver.start_rotate(i, direction.value, speed)
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

    def reset(
            self,
            direction: Direction = Direction.BWD,
            speed: int = 100,
            steps: int | None = None,
            delta: datetime.timedelta | None = None,
            motor_id: int | None = None,
            fs_only: bool = False
    ) -> bool:

        return self.drive(
            direction=direction,
            speed=speed,
            steps=steps,
            delta=delta,
            motor_id=motor_id,
            fs_only=fs_only
        )

