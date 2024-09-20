import datetime

class Packet:
    NAME:   str
    TIME:   datetime.datetime
    RAW:    str | bytes
    DATA:   dict

    def __init__(self, **kwargs):
        self.NAME   = kwargs.get("NAME", "")
        self.TIME   = datetime.datetime(**(kwargs.get("TIME"))) if isinstance(kwargs.get("TIME"), dict) \
                        else kwargs.get("TIME")
        self.RAW    = kwargs.get("RAW"  , "")
        self.DATA   = kwargs.get("DATA" , {})
    def __str__(self) -> str:
        return f"[ Packet ]: {self.NAME} from {self.TIME} @\n{str(self.DATA)}"
