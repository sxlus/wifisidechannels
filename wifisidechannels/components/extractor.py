import re
import wifisidechannels.models.models as models

class Extractor:
    """
    Interface for Extractor of various kinds.
    """
    KEY: str
    def __init__(self, **kwargs):
        self.KEY = kwargs.get("KEY", "")
    def apply(self, packet: models.Packet) -> dict:
        """Perform extraction"""
        return {}
    def __str__(self):
        return f"[ Extractor ][ {str(self.KEY)} ]"

class StringExtractor(Extractor):
    """
    Used to extract from string packets
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def __str__(self):
        return super().__str__() + f"[ String ]"

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

    def apply(self, packet: models.Packet) -> dict:
        found: dict[list] = {}
        data = packet.RAW if isinstance(packet.RAW, str) else packet.RAW.decode("utf-8") 
        if (match:= re.finditer(re.compile(self.REGEX), data)):
            found[self.KEY] = []
            for mat in match:
                found[self.KEY].append(mat.group(self.GROUP))
        return found

class ColumnExtractor(StringExtractor):
    """
    Extract from string packets delivered by tshark by columns.
    """
    COLUMN: int
    DELIM:  str
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.COLUMN = kwargs.get("COLUMN", 0)
        self.DELIM  = kwargs.get("DELIM", ",")
    def __str__(self):
        return super().__str__() + f"[ COMUMN ]: {str(self.COLUMN)} - [ DELIM ]: {hex(ord(self.DELIM))}"

    def apply(self, packet: models.Packet) -> dict:
        raw = (packet.RAW.decode("utf-8") \
                    if isinstance(packet.RAW, bytes) \
                        else str(packet.RAW)
                            ).strip().split(self.DELIM)
        self.RAW = raw
        #print("COL: ", str(raw[self.COLUMN]))
        return {
                self.KEY: raw[self.COLUMN] 
            } if len(raw) > self.COLUMN and raw[self.COLUMN] else {
                #self.KEY: ""
            }

class FieldExtractor(Extractor):
    """
    Parse specific Fields of 802.11.
    """
    FROM        :       str
    FIELD       :       models.WifiField = models.WifiField()
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.FIELD = kwargs.get("FIELD", self.FIELD)
        self.FROM = kwargs.get("FROM", self.FROM)

    def __str__(self):
        return super().__str__() + f" < Field >\n{str(self.FIELD)}"

    def apply(self, packet: models.Packet) -> dict:
        return {
            self.KEY : self.FIELD.translate(val, base = 16)
        } if (val := packet.DATA.get(self.FROM, None)) else {}

class VHT_MIMO_CONTROL_Extractor(FieldExtractor):
    """
    EXTRACT VHT_MIMO_CONTROL_CONTROL.
    """
    FROM        :       str                 = models.TsharkField.VHT_MIMO_CONTROL_CONTROL.value
    KEY         :       str                 = models.ExtractorField.VHT_MIMO_CONTROL.value
    FIELD       :       models.WifiField    = models.VHT_MIMO_CONTROL_CONTROL()

    def __init__(self, **kwargs):
        super().__init__(**(
            kwargs | (
                    {
                        "FIELD" : kwargs.get("FIELD") if isinstance(kwargs.get("FIELD"), models.WifiField) else self.FIELD
                    }
                ) |
                (
                    {
                        "KEY" : kwargs.get("KEY") if isinstance(kwargs.get("KEY"), str) else self.KEY
                    }
                )
            )
        )

class VHT_BEAMFORMING_REPORT_Extractor(FieldExtractor):
    """
    EXTRACT VHT_CBR.
    """
    FROM        :       str                 = models.TsharkField.VHT_CBR.value
    KEY         :       str                 = models.ExtractorField.VHT_CBR_PARSED.value
    FIELD       :       models.WifiField    = models.VHT_CBR()
    def __init__(self, **kwargs):
        super().__init__(**(
            kwargs | (
                    {
                        "FIELD" : kwargs.get("FIELD") if isinstance(kwargs.get("FIELD"), models.WifiField) else self.FIELD
                    }
                ) |
                (
                    {
                        "KEY" : kwargs.get("KEY") if isinstance(kwargs.get("KEY"), str) else self.KEY
                    }
                )
            )
        )