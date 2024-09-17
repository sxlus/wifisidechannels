import wifisidechannels.units.txbf as txbf
import pathlib
import multiprocessing as mp
import typing
import time

class Meassure:
    m_unit  :   txbf.TxBf       = None
    m_channel:  int | None      = None
    m_num:      int | None      = None
    m_mac_sa:   str | None      = None
    m_mac_da:   str | None      = None
    m_procs:    list[mp.Process]= []
    PROCESSES:  int             = 4
    m_read_file: str | None     = None

    def __init__(self, kwargs: dict = {
        "interface": "wlp0s20f3",
        "channel": 44,
        "num": 1,
        "mac_sa": None,
        "mac_da": None
    }):
        self.m_interface= kwargs.get("interface", None)
        self.m_mac_da   = kwargs.pop("mac_da", None)
        self.m_mac_sa   = kwargs.pop("mac_sa", None)
        self.m_num      = kwargs.pop("num", None)
        self.m_channel  = kwargs.get("channel", None)
        self.m_read_file= kwargs.pop("read_file", None)
        self.m_unit = txbf.TxBf(**kwargs)

    def do(self, kwargs: dict = {
        "num": None,
        "channel": None,
        "mac_sa": None,
        "mac_da": None,
        "read_file": None
}) -> bool:

        #print("MEASSURE")

        if kwargs.get("mac_da", None) is None:
            kwargs |= {"mac_da": self.m_mac_da} 

        if kwargs.get("mac_sa", None) is None:
            kwargs |= {"mac_sa": self.m_mac_sa} 

        if kwargs.get("channel", None) is None:
            kwargs |= {"channel": self.m_channel}
        
        if kwargs.get("num", None) is None:
            kwargs |= {"num": self.m_num}

        if  kwargs.get("read_file", None) is None and self.m_read_file is not None:
            kwargs |= {"read_file": self.m_read_file}

        #print("######### KWARGS:\n\t", kwargs)
        data = self.m_unit.collect_sample(kwargs=kwargs)
        #print("MEASSURE GETS PACS: ")

        #for i, pac in enumerate(data):
        #    print(str(i) , str(pac))
    
        return True

    def _process_and_store(
        self,
        write_file: pathlib.Path | str | None = "test",
        meta_info: dict = {},
    ) -> bool:

        # gives packets, V, T
        # should be good as objects are mutable 
        stuff = self.m_unit.process_VHT_COMPRESSED_BREAMFROMING_REPORT(
            packets=None,
            check = True,
        )
        self.m_unit.store(
            data= None, #stuff[0],
            write_file=write_file,
            meta_info=meta_info | {
                "interface": self.m_interface if self.m_interface is not None else  "",
                "channel": self.m_channel if self.m_channel is not None else        0,
                "mac_sa" : self.m_mac_sa if self.m_mac_sa is not None else          "",
                "mac_da" : self.m_mac_da if self.m_mac_da is not None else          "",
                "samples_per_state" : self.m_num if self.m_num is not None else     0,
            }
        )
        return True

    def process_and_store(
        self,
        write_file: pathlib.Path | str | None = "test",
        meta_info: dict = {},
    ) -> bool:

        proc = self.launch_process(
            function=self._process_and_store,
            kwargs = {
                "write_file": str(write_file),
                "meta_info":  meta_info
            },
            blocking = False
        )
        if proc is None:
            print(
                f"[ MEASSURE ][ ERROR ] Cant parse & store samples due to to many active processes."
            )
            return False
        return True

    # lauches processes for tasks in the form of funtions
    def launch_process(
            self,
            function: typing.Callable,
            blocking: bool | None = False,
            kwargs: dict = {}
    ) -> mp.Process:

        """Shedules tasks to be handled."""
        abort = 10
        i = 0
        while len(self.procs_alive()) == self.PROCESSES:
            print("[DEBUG]: lauch_task - waiting for processes to finish.")
            i+=1
            if i >= abort:
                return None
            print(f"CANT LAUNCH NEW PROCESS!")
            time.sleep(1)
        proc = mp.Process(target=function, kwargs=kwargs)
        if not blocking:
            self.m_procs.append(proc)
        proc.start()
        if blocking:
            proc.join()
        return proc

    # stuff on procs that might have been spawned
    def procs_alive(
            self,
            procs: list[mp.Process] | None = None
    ) -> list[mp.Process]:

        if procs is None or procs == self.m_procs:
            self.m_procs = [x for x in self.m_procs if x.is_alive()]
            return self.m_procs
        else:
            return [x for x in procs if x.is_alive()]

    def terminate(
            self,
            procs: list[mp.Process] | None = None
    ):
        #self.m_unit.terminate()
        if procs is None:
            procs = self.m_procs
        for x in [x for x in procs if x.is_alive()]:
            x.terminate()
            x.join()
