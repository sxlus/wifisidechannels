import wifisidechannels.components.extractor as extractor
import wifisidechannels.models.models as models

## done
class PacketParser:
    NAME: str                           = ""
    EXTRACT: list[extractor.Extractor]  = []
    
    def __init__(self, **kwargs):
        self.NAME = kwargs.get("NAME") if kwargs.get("NAME") else self.NAME
        self.EXTRACT = [ kwargs.get("EXTRACT") ] if isinstance(kwargs.get("EXTRACT"), extractor.Extractor) \
                        else kwargs.get("EXTRACT", [])
    
    def __str__(self):
        return f"[ PacketParser ]: {self.NAME} with Extarctors:\n" + "\n".join([str(ex) for ex in self.EXTRACT][-5:])
    
    def parse(self, inp: models.Packet):
        out = {}
        for ex in self.EXTRACT:
            if type(ex) == extractor.ColumnExtractor:
                for line in inp.RAW.split("\n"):
                    out = self.join_dict(a=ex.apply(inp=line), b=out)
            elif type(ex) == extractor.RegexExtractor:
                out = self.join_dict(a=ex.apply(inp=line), b=out)
        return out

    def join_dict(self, a: dict, b: dict) -> dict:
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