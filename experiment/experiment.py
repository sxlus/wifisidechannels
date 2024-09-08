import typing 
import datetime
import time

import experiment.action as action

class Experiment:
    m_actions: typing.Iterable[action.Action]
    m_actions_reset: typing.Iterable[action.Action]
    m_delta: datetime.timedelta
    m_stop_callback: typing.Callable
    m_stop_callback_reset: typing.Callable


    def __init__(
            self,
            actions: typing.Iterable[action.Action],
            actions_reset: typing.Iterable[action.Action],
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
            actions: typing.Iterable[action.Action] | None = None,
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