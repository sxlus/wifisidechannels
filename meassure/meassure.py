import wifisidechannels.units.txbf as txbf

class Meassure:
    m_unit : txbf.TxBf = None
    def __init__(self, kwargs: dict = {
        "interface": "wlp0s20f3",
        "channel": 64
    }):
        self.m_unit = txbf.TxBf(**kwargs)

    def do(self, kwargs={
        "num": 1,
        "mac_sa": "d8:3a:dd:e5:66:2c",
        "mac_da": "127c6136fcc2"
}) -> bool:

        print("MEASSURE")
        data = self.m_unit.collect_sample(kwargs=kwargs)
        #print("MEASSURE GETS PACS: ")
        print(len(data))
        for i, pac in enumerate(data):
            print(str(i) , str(pac))
    
        return True