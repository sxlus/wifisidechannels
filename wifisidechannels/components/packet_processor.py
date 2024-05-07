import pathlib, typing, datetime

import wifisidechannels.models.models as models
import wifisidechannels.components.extractor as extractor

class PacketProcessor():
    """
    @JOB:   reads packets from m_source and parses m_source according to m_values.
        Parsed packets are kept in m_data.
        Read string ( preparsed pcap ) from m_source, where m_values is '{"value_name": column_number}'
        TODO: Else pcap format is required @ m_source. Then m_value should contain valid scappy Filters. 
    """
    m_name          : str                           = "PackProc"
    # IN
    m_todo          : list[models.Packet]           = []
    m_extractor     : list[extractor.Extractor]     = []
    m_max_keep      : int                           = 1000

    # OUT
    m_data          : list[models.Packet]           = []


    # INTERNAL currently unused
    #m_source        : list[pathlib.Path]            = []
    m_source_type   : type                          = str
    m_source_fp     : typing.IO                     = None
    
    def __init__(
            self,
            **kwargs
    ):
        self.m_name     = self.m_name + str(kwargs.get("name")) if kwargs.get("name") else self.m_name
        #self.m_source       = [
        #        pathlib.Path(kwargs.get("source"))
        #    ] if isinstance(kwargs.get("source"), str) else [
        #        kwargs.get("source")
        #    ]   if isinstance(kwargs.get("source"), pathlib.Path) else kwargs.get("source") \
        #            if isinstance(kwargs.get("source"), list) else []
        self.m_extractor    = [
                kwargs.get("extractor") 
            ] if isinstance(kwargs.get("extractor"), extractor.Extractor) else kwargs.get("extractor") \
                if isinstance(kwargs.get("extractor"), list) else []
        self.m_max_keep     = kwargs.get("max_keep") if isinstance(kwargs.get("max_keep"), int) else self.m_max_keep
        self.m_data         = [ 
            kwargs.get("data")
            ] if isinstance(kwargs.get("data"), models.Packet) else kwargs.get("data") \
                if isinstance(kwargs.get("data"), list) else []

    def __str__(self):
        s = f"PacketProcessor: {len(self.m_data)} Packets available.\n"
        for pac in self.m_data[-20:]:
            row = ""
            for key in pac:
                row += f"{key: >20} : {pac.get(key, ''): >30}"
            s += row + "\n"             
        return s

    def __len__(self):
        return len(self.m_data)

    def handle(
            self,
            raw: list[str | bytes],
            name: str = "",
            extract: extractor.Extractor | list[extractor.Extractor] = None
    ) -> list[models.Packet]:

        todo = self.add_todo(raw=raw, name=name)
        return self.extract(todo=todo, extract=extract)

    def add_todo(
            self,
            raw: list[str | bytes],
            name: str = ""
    ) -> list[models.Packet]:
        """Take array of raw data and add to todo"""
        data = []
        for entry in raw:
            now = datetime.datetime.now()
            data.append(models.Packet(
                **{
                    "NAME": self.m_name if not name else name,
                    "TIME": now,
                    "RAW" : entry
                }
        ))
        self.m_todo += data
        return self.m_todo

    def parse_packet(
            self,
            inp: models.Packet,
            extract: list[extractor.Extractor] = None
    ) -> dict:

        if extract is None:
            extract = self.m_extractor
        out = {}
        for ex in extract:
            out = self.join_dict(a=ex.apply(packet=inp), b=out)
        return out

    def join_dict(
            self,
            a: dict,
            b: dict
    ) -> dict:
        out = {}

        for k in [ x for x in a.keys() if x not in b.keys()]:
            out[k] = a[k]
        for k in [ x for x in a.keys() if x in b.keys()]:
            out[k] = list(set(a[k] + [b[k]])) if type(a[k]) == list and type(b[k]) != list else \
                    list(set([a[k]] + b[k])) if type(a[k]) != list and type(b[k]) == list else \
                    list(set(a[k] + b[k])) if type(a[k]) == list and type(b[k]) == list else  \
                    list(set([a[k]] + [b[k]]))
        for k in [ x for x in b.keys() if x not in a.keys()]:
            out[k] = b[k]
        return out

    def extract(
            self,
            todo: models.Packet | list[models.Packet]                     = None,
            extract: extractor.Extractor | list[extractor.Extractor]      = None
    ) -> list[models.Packet]:

        """Extract num packets from m_todo @ """
        todo        = self.m_todo       if todo is None     else [ todo ]       if isinstance(todo, models.Packet)          else todo
        extract     = self.m_extractor  if extract is None  else [ extract ]    if isinstance(extract, extractor.Extractor) else extract
        data: list[models.Packet] = []
        for pack in todo:
            pack.NAME = self.m_name if not pack.NAME else pack.NAME
            pack.DATA = self.join_dict(pack.DATA, self.parse_packet(pack))
            data.append(pack)
        if todo == self.m_todo:
            self.m_todo = []

        return self.save(data)

    def save(
            self,
            data: list[models.Packet]
    ):
        if len(self.m_data) > self.m_max_keep:
            print(f"{self.m_name}[ INFO ]: save - len(data) > max_keep. Keeping last max_keep samples.")
            self.m_data = data[self.m_max_keep:]
        elif (len(self.m_data) + len(data)) > self.m_max_keep:
            low = self.m_max_keep-len(data)
            self.m_data = self.m_data[low:] + data
        else:
            self.m_data += data
        print(f"{self.m_name}[ INFO ]: Currently holding {len(self.m_data)} samples.")
        return data
