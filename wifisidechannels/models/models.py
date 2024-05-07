import datetime
import enum
import wifisidechannels.components.extractor as extractor

placeholder = "FUZZ"

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
        return f"[ Packet ]: {self.NAME} from {self.TIME} with content:\n{str(self.RAW)} @\n{str(self.DATA)}"

class TsharkDisplayFilter(enum.Enum):

    # these can be used with -F flag of set_up script

    # TXBF STUFF
    VHT_NDP_ANNOUNCE:str            = "\"(wlan.fc.type==0 && wlan.fc.subtype==5) || (wlan.fc.type_subtype==21)\""
    VHT_NDP_ANNOUNCE_I:str          = "\"(wlan.fc.type_subtype == 0x15)\""
    VHT_ACTION_NO_ACK:str           = "\"(wlan.fc.type_subtype == 0x0e)\""
    BEAMFORMING_REPORT_POLL:str     = "\"(wlan.fc.type==1 && wlan.fc.subtype==4) || wlan.fc.type_subtype==20\""


    # GENERAL
    MAC_RA: str                     = f"\"(wlan.ra == {placeholder})\""
    MAC_TA: str                     = f"\"(wlan.ta == {placeholder})\""
    MAC_SA: str                     = f"\"(wlan.sa == {placeholder})\""
    MAC_DA: str                     = f"\"(wlan.da == {placeholder})\""

class TsharkField(enum.Enum):

    FRAME_TIME:str                          = "frame.time"
    MAC_RA:str                              = "wlan.ra"
    MAC_TA:str                              = "wlan.ta"
    MAC_SA:str                              = "wlan.sa"
    MAC_DA:str                              = "wlan.da"
    VHT_MIMO_CONTROL_CONTROL:str            = "wlan.vht.mimo_control.control"
    VHT_COMPRESSED_BEAMAFORMINGREPORT:str   = "wlan.vht.compressed_beamforming_report"

class TsharkDisplayConfig():
    NAME: str                                   = ""
    COM_FIELD: list[TsharkField]                = []
    COM_FILTER: list[TsharkDisplayFilter]       = []

    def __init__(self, name: str = "", fields: list[TsharkField] = [], filter: list[TsharkDisplayFilter] = []):
        self.NAME           = str(name)
        self.COM_FIELD      = fields
        self.COM_FILTER     = filter

    def __str__(self):
        return ("-F " + "||".join([ str(filt.value) for filt in self.COM_FILTER]) + " " if self.COM_FILTER else "") \
            + ("-E " + ",".join( [ str(field.value) for field in self.COM_FIELD ] ) if self.COM_FIELD else "")

    def extractor(self):
        return [
            extractor.ColumnExtractor(
                **{
                    "KEY" : field.value,
                    "COLUMN": i,
                    "DELIM": "\t"
                }
            ) for i, field in enumerate(self.COM_FIELD)
        ]