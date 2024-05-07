import re
import wifisidechannels.models.models as models

class Extractor:
    """
    Interface for Extractor of various kinds.
    """
    KEY: str
    def __init__(self, **kwargs):
        self.KEY = kwargs.get("KEY", "")

    def apply(self, packet):#: models.Packet) -> dict: -> cyclic imports :)
        """Perform extraction"""
        return {}
    def __str__(self):
        return f"[ Extractor ] : {str(self.KEY)}"

class StringExtractor(Extractor):
    """
    Used to extract from string packets
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def __str__(self):
        return super().__str__() + " - < String >"

class RegexExtractor(StringExtractor):
    """
    Extract from string packets delivered by tshark by regex.
    """
    REGEX:  str
    GROUP:  int = 0
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.REGEX = kwargs.get("REGEX","")
        self.GROUP = kwargs.get("GROUP", 0)
    def __str__(self):
        return super().__str__() + f"[ REGEX ]: {str(self.REGEX)}"
    
    def apply(self, packet):#: models.Packet) -> dict:
        found: dict[list] = {}
        data = packet.RAW if isinstance(packet.RAW, str) else packet.RAW.decode("utf-8") 
        if (match:= re.finditer(re.compile(self.REGEX), data)):
            found[self.KEY] = []
            for mat in match:
                found[self.KEY].append(mat.group(self.GROUP))
        return found

class ColumnExtractor(StringExtractor):
    """
    Extract from string packets delivered by tshark by columns
    """
    COLUMN: int
    DELIM:  str
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.COLUMN = kwargs.get("COLUMN", 0)
        self.DELIM  = kwargs.get("DELIM", ",")
    def __str__(self):
        return super().__str__() + f"[ COMUMN ]: {str(self.COLUMN)} - DELIM: {str(self.DELIM)}"

    def apply(self, packet):#: models.Packet) -> dict:
        raw = [
            x.strip() for x in (packet.RAW.decode("utf-8").strip() \
                                if isinstance(packet.RAW, bytes) \
                                    else str(packet.RAW.strip())).split(self.DELIM)
        ]
        return {
                self.KEY: [ raw[self.COLUMN] ]
            } if len(raw) > self.COLUMN else {
                self.KEY: []
            }

class VHT_MIMO_CONTROL_Extractor(StringExtractor):
    """
    Parse VHT_MIMO_CONTROL FIELD
    """

class VHT_BEAMFORMING_REPORT_Extractor(StringExtractor):
    """
    Parse VHT_MIMO_CONTROL FIELD
    """