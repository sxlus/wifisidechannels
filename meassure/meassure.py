import wifisidechannels.units.txbf as txbf

class Meassure:
    m_unit  :   txbf.TxBf       = None
    m_channel:  int | None      = None
    m_num:      int | None      = None
    m_mac_sa:   str | None      = None
    m_mac_da:   str | None      = None

    def __init__(self, kwargs: dict = {
        "interface": "wlp0s20f3",
        "channel": 44,
        "num": 1,
        "mac_sa": None,
        "mac_da": None
    }):

        self.m_mac_da   = kwargs.pop("mac_da", None)
        self.m_mac_sa   = kwargs.pop("mac_sa", None)
        self.m_num      = kwargs.pop("num", None)
        self.m_channel  = kwargs.get("channel", None)

        self.m_unit = txbf.TxBf(**kwargs)

    def do(self, kwargs: dict = {
        "num": 1,
        "channel": 44,
        "mac_sa": None,
        "mac_da": None
}) -> bool:

        print("MEASSURE")

        if kwargs.get("mac_da", None) is None:
            kwargs |= {"mac_da": self.m_mac_da} 

        if kwargs.get("mac_sa", None) is None:
            kwargs |= {"mac_sa": self.m_mac_sa} 

        if kwargs.get("channel", None) is None:
            kwargs |= {"channel": self.m_channel}
        
        if kwargs.get("num", None) is None:
            kwargs |= {"num": self.m_num}

        data = self.m_unit.collect_sample(kwargs=kwargs)
        #print("MEASSURE GETS PACS: ")
        print(len(data))
        for i, pac in enumerate(data):
            print(str(i) , str(pac))
    
        return True