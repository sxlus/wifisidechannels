import typing
import datetime
import time

class Action:
    m_name: str
    m_obj: typing.Callable
    m_kwargs: dict
    m_delta: datetime.timedelta

    def __init__(
            self,
            obj : typing.Callable,
            kwargs: dict = {},
            name = "Action",
            delta = datetime.timedelta(seconds=0)
    ):
        self.m_name = name
        self.m_obj = obj
        self.m_kwargs = kwargs
        self.m_delta = delta

    def start(self):
        #print(self.m_kwargs, self.m_obj)
        if not self.m_obj(**self.m_kwargs):
            raise BaseException("[Action][start] Failure")
        print(f"[ {self.m_name} ][ SLEEP ]: {str(self.m_delta.total_seconds())}")
        time.sleep(self.m_delta.total_seconds())
    
    def __str__(self):
        return f"[ ACTION: {self.m_name} ]\n\tOBJ: {self.m_obj}\n\tDELTA: {str(self.m_delta.total_seconds())}" + (f"\n\tKWARGS: {str(self.m_kwargs)}" if self.m_kwargs != {} else "")
