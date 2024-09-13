from meassure.meassure import Meassure
from experiment.action import Action


meassure = Meassure(
    kwargs={
        "interface": "wlp0s20f3"
    }
)

print("INTERFACE: ", meassure.m_unit.m_interface)

act = Action(
    name="MEASSURE",
    obj=meassure.do,
    kwargs={
        "kwargs":{
            "num": 2,
            "mac_sa": "d83adde5662c",
            "mac_da": "127c6136fcc2",
            "channel": 64,
            "timeout": 5
        }
    }
)

act.start()




