import typing

class Action:
    m_name: str
    m_obj: typing.Callable
    m_kwargs: dict
    def __init__(
            self,
            obj : typing.Callable,
            kwargs: dict = {},
            name = "Action"
    ):
        self.m_name = name
        self.m_obj = obj
        self.m_kwargs = kwargs

    def start(self):
        #print(self.m_kwargs, self.m_obj)
        if not self.m_obj(**self.m_kwargs):
            raise BaseException("[Action][start] Failure")
