import typing 
import datetime
import time
import pathlib
import os

from wifisidechannels.models.models import Packet
from experiment.action import Action
from hardware.motor.motor import Motor, Direction
from meassure.meassure import Meassure

class Experiment:
    m_actions: typing.Iterable[Action]
    m_actions_reset: typing.Iterable[Action]
    m_delta: datetime.timedelta
    m_stop_callback: typing.Callable
    m_stop_callback_reset: typing.Callable


    def __init__(
            self,
            actions: typing.Iterable[Action] = [],
            actions_reset: typing.Iterable[Action] = [],
            delta: datetime.timedelta = datetime.timedelta(seconds=0),
            stop_callback: typing.Callable = lambda: True,
            stop_callback_reset: typing.Callable = lambda: True
    ):
        self.m_actions = actions
        self.m_actions_reset = actions_reset
        self.m_delta = delta
        self.m_stop_callback = stop_callback
        self.m_stop_callback_reset = stop_callback_reset

    def run(
            self,
            actions: typing.Iterable[Action] | None = None,
            stop_callback: typing.Callable | None = None
    ) -> bool:

        actions = self.m_actions if actions is None else actions
        stop_callback = self.m_stop_callback if stop_callback is None else stop_callback

        try:
            #print(stop_callback())
            while not stop_callback():
                for action in actions:
                    action.start()
                    time.sleep(self.m_delta.total_seconds())
        except Exception as r:
            print(f"[Experiment] encountered error {r}")
            return False
        return True

    def reset(
            self,
            stop_callback: typing.Callable | None = None
    ) -> bool:

        stop_callback = self.m_stop_callback_reset if stop_callback is None else stop_callback
        #print(stop_callback)
        return self.run(
            actions=self.m_actions_reset,
            stop_callback=stop_callback
        )
        



class NumericalPasswordSCExperiment(Experiment):

    m_actions: typing.Iterable[Action]
    m_actions_reset: typing.Iterable[Action]
    m_delta: datetime.timedelta
    m_stop_callback: typing.Callable
    m_stop_callback_reset: typing.Callable

    m_max_steps: int
    m_max_positions: int = 10
    m_password_file: pathlib.Path | str
    m_passwords: list = []
    m_next_pw_idx: int = 0
    m_current_pw: str = ""

    def __init__(
            self,
            actions: typing.Iterable[Action] = [],
            actions_reset: typing.Iterable[Action] = [],
            delta: datetime.timedelta = datetime.timedelta(seconds=0),
            stop_callback: typing.Callable = lambda: True,
            stop_callback_reset: typing.Callable = lambda: True,
            max_steps: int = 8000,
            max_positions: int = 10,
            password_file: pathlib.Path | str = "test_passwords.txt"
    ):
        super().__init__(
                actions = actions,
                actions_reset = actions_reset,
                delta = delta,
                stop_callback = stop_callback,
                stop_callback_reset = stop_callback_reset
        )

        self.m_password_file = password_file
        self.m_passwords = self.read_file(file=password_file)
        self.m_max_steps = max_steps
        self.m_max_positions = max_positions

    def read_file(
            self,
            file: pathlib.Path | str | None = None,
    ) -> list[str]:

        if file is None:
            file = self.m_password_file

        try:
            with open(file, "rt") as f:
                passwords = [ x.strip() for x in f.readlines() ]
        except Exception as r:
            print(f"[ EXPERIMENT ][ READ FILE ][ ERROR ]: Reading file: {file} - {r}.")

        return passwords


    def create_actions_from_password(
            self,
            motor: Motor,
            meassure: Meassure,
            password: str | None = None,
            idx: int | None = None,
            number_of_chunks: int | None = None,
            from_idy: int | None = None,
            v: bool = False
    ) -> list[list[Action], list[Action]] | None:

        if number_of_chunks is None:
            number_of_chunks = 1
        if idx is None:
            if len(self.m_passwords) == 0:
                print(f"[ EXPERIMENT ][ CREATE ACTIONS ][ ERROR ]: Passwords are empty! Read them first!")
                return None

            idx = self.m_next_pw_idx
            if idx >= len(self.m_passwords):
                print(f"[ EXPERIMENT ][ CREATE ACTIONS ][ WARN ]: Index `idx` = {idx} >= len(passwords) = {len(self.m_passwords)}, setting to 0.")
                self.m_next_pw_idx = 0
                idx = self.m_next_pw_idx
            password = self.m_passwords[idx]
            self.m_next_pw_idx += 1

        else:
            if password is None:
                print(f"[ EXPERIMENT ][ CREATE ACTIONS ][ ERROR ]: Need password or index.")
                return None
        
        self.m_current_pw   = password
        step_per_number     = self.m_max_steps // self.m_max_positions
        delta_per_number    = (step_per_number / motor.m_speed_set)
        #print("DELTA PER NUMBER: ", delta_per_number)
        #print("STEP  PER NUMBER: ", step_per_number)
        #print("MOTOR SET SPEED : ", motor.m_speed_set)

        password_split      = [int(x, 10) for x in list(password)]
        reset               = Action(
                name=f"MOTOR_RESET_GO_UNTIL",
                obj=motor.reset,#lambda **kwargs: True, #
                kwargs={
                    "direction": Direction.BWD,
                    "speed": motor.m_speed_home,
                    "go_until": True
                }
            )
        ACTIONS             = [
            #reset
        ]
        RESET_ACTIONS       = [
            reset
        ]

        # random start position ?

        for idy in range(len(password_split)):
            if from_idy is None:
                if idy > 0:
                    from_idy = password_split[idy-1]
                else:
                    from_idy = [int(x, 10) for x in list(self.m_passwords[idx-1])][-1] if idx > 0 else 0

            to_idy = password_split[idy]
            if from_idy < to_idy:
                diff_idy = (to_idy - from_idy)
                step = diff_idy*step_per_number 
                direction = Direction.FWD
            else:
                diff_idy =(from_idy - to_idy)
                step = diff_idy*step_per_number
                direction = Direction.BWD

            if idy > 0:
                rest = step % number_of_chunks
                chunk_step = step // number_of_chunks
                for chunk in range(1, number_of_chunks+1):
                    ACTIONS += [
                        Action(
                            name=f"MOTOR_STEP_FROM_{str(from_idy)}_TO_{to_idy}_CHUNK_{chunk}/{number_of_chunks}",
                            obj=motor.drive,#lambda **kwargs: True, 
                            kwargs={
                                "direction": direction,
                                "steps": chunk_step + (rest if chunk == number_of_chunks else 0),
                                "fs_only": False
                            },
                            #delta=datetime.timedelta(seconds=((diff_idy*delta_per_number)/number_of_chunks) + (1 if (diff_idy > 0) else 0))#0)
                        ),
                        Action(
                            name="MEASSURE",
                            obj=meassure.do,
                            kwargs={}
                        ),
                    ]
            else:
                ACTIONS += [
                    Action(
                        name=f"MOTOR_STEP_FROM_{str(from_idy)}_TO_{to_idy}",
                        obj=motor.drive,#lambda **kwargs: True,
                        kwargs={
                            "direction": direction,
                            "steps": step,
                            "fs_only": False
                        },
                        #delta=datetime.timedelta(seconds=(diff_idy*delta_per_number) + (1 if (diff_idy > 0) else 0))#0)#
                    ),
                    Action(
                        name="MEASSURE",
                        obj=meassure.do,
                        kwargs={}
                    ),
                ]
            from_idy = None
        # might use absolut position to determine steps required to go home, or motor.go_until to use halll sensor


        if v:
            for act in ACTIONS:
                print(str(act))

            #for act in RESET_ACTIONS:
            #    print(str(act))

        self.m_actions          = ACTIONS
        self.m_actions_reset    = RESET_ACTIONS

        return [ACTIONS, RESET_ACTIONS]
    
    def run(
            self,
            actions: typing.Iterable[Action] | None = None
    ) -> bool:

        actions = self.m_actions if actions is None else actions

        try:
            for act in actions:
                act.start()
                #print("SLEEPING: ", self.m_delta.total_seconds())
                time.sleep(self.m_delta.total_seconds())
        except Exception as r:
            print(f"[Experiment] encountered error {r}")
            return False
        return True

    def reset(
            self,
            meassure: Meassure | None = None,
    ) -> bool:

        if isinstance(meassure, Meassure):
            self.m_next_pw_idx = self.m_next_pw_idx-1
            meassure.m_unit.m_data = []
            for processor in meassure.m_unit.m_processor:
                processor.m_data = []
                processor.m_todo = []
        return self.run(
            actions=self.m_actions_reset
        )

    def store(
        self,
        meassure: Meassure,
        write_file: pathlib.Path | str | None = "test",
        meta_info: dict = {},
    ) -> dict | None:

        if isinstance(write_file, str):
            write_file = pathlib.Path(write_file)
        if write_file is None:
            write_file = pathlib.Path("")
        try:
            meassure.process_and_store(
                write_file = pathlib.Path(os.path.join(write_file.parents[0], write_file.stem + "_" + str(self.m_current_pw) + "".join(write_file.suffixes))),
                meta_info=meta_info | {
                    "max_steps":        self.m_max_steps,
                    "max_positions":    self.m_max_positions,
                    "password_file":    self.m_password_file,
                    "pw":       self.m_current_pw,
                }
            )
        except Exception as r:
            print(f"[ EXPERIMENT ][ ERROR ] Cant store data. State unsave. {r}")
            return False
        finally:
            meassure.m_unit.m_data = []
        return True