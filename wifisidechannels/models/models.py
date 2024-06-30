import datetime
import enum
import typing

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
    VHT_NDP_ANNOUNCE_I:str          = "(wlan.fc.type_subtype == 0x15)"
    VHT_ACTION_NO_ACK:str           = "(wlan.fc.type_subtype == 0x0e)"
    BEAMFORMING_REPORT_POLL:str     = "\"(wlan.fc.type==1 && wlan.fc.subtype==4) || wlan.fc.type_subtype==20\""

    # GENERAL
    MAC_RA: str                     = f"(wlan.ra == {placeholder})"
    MAC_TA: str                     = f"(wlan.ta == {placeholder})"
    MAC_SA: str                     = f"(wlan.sa == {placeholder})"
    MAC_DA: str                     = f"(wlan.da == {placeholder})"

class TsharkField(enum.Enum):

    FRAME_TIME:str                          = "frame.time_epoch"
    MAC_RA:str                              = "wlan.ra"
    MAC_TA:str                              = "wlan.ta"
    MAC_SA:str                              = "wlan.sa"
    MAC_DA:str                              = "wlan.da"
    VHT_MIMO_CONTROL_CONTROL:str            = "wlan.vht.mimo_control.control"
    VHT_CBR:str   = "wlan.vht.compressed_beamforming_report"

class ExtractorField(enum.Enum):
    VHT_MIMO_CONTROL                        = "mimo_control"
    VHT_STEERING_MATRIX                     = "V"
    VHT_CBR_PARSED                          = "cbr_parsed"

# this shall get simplified to function from wipicap or simplpy replaced
class VHT_MIMO_CONTROL_NA(enum.Enum):
    """
    Access with str(Nr) + str(Nc)
    """
    VAL = {
        "21" : 2,
        "22" : 2,
        "31" : 4,
        "32" : 6,
        "33" : 6,
        "41" : 6,
        "42" : 10,
        "43" : 12,
        "44" : 12,
        "51" : 8,
        "52" : 14,
        "53" : 18,
        "54" : 20,
        "55" : 20,
        "61" : 10,
        "62" : 18,
        "63" : 24,
        "64" : 28,
        "65" : 30,
        "66" : 30
    }

# this shall get simplified to function from wipicap or simplpy replaced
class VHT_MIMO_CONTROL_OA(enum.Enum):
    """
    Access with Nr, Nc from MIMO_CONTROL
    """
    def VAL(nr, nc):
        angle_bits_order_len = min([nc, nr - 1]) * (2 * (nr - 1) - min(nc, nr - 1) + 1)
        cnt = nr - 1
        angle_type = []
        phi_indices = [0, 0]
        psi_indices = [1, 0]
        while len(angle_type) < angle_bits_order_len:
            for i in range(cnt):
                angle_type.append(f"phi{phi_indices[0] + i}{phi_indices[1]}")
            phi_indices[0] += 1
            phi_indices[1] += 1
            for i in range(cnt):
                angle_type.append(f"psi{psi_indices[0] + i}{psi_indices[1]}")
            psi_indices[0] += 1
            psi_indices[1] += 1
            cnt -= 1
        return angle_type

    #VAL = {
    #    "21" : ["psi11", "phi21"],
    #    "22" : ["psi11", "phi21"],
    #    "31" : ["psi11", "psi21", "phi21", "phi31"],
    #    "32" : ["psi11", "psi21", "phi21", "phi31", "psi22", "phi32"],
    #    "33" : ["psi11", "psi21", "phi21", "phi31", "psi22", "phi32"],
    #    "41" : ["psi11", "psi21", "psi31", "phi21", "phi31", "phi41"],
    #    "42" : ["psi11", "psi21", "psi31", "phi21", "phi31", "phi41", "psi22", "psi32", "phi32", "phi42"],
    #    "43" : ["psi11", "psi21", "psi31", "phi21", "phi31", "phi41", "psi22", "psi32", "phi32", "phi42", "psi33", "phi43"],
    #    "44" : ["psi11", "psi21", "psi31", "phi21", "phi31", "phi41", "psi22", "psi32", "phi32", "phi42", "psi33", "phi43"],
    #    "51" : ["psi11", "psi21", "psi31", "psi41", "phi21", "phi31", "phi41", "phi51"],
    #    "52" : ["psi11", "psi21", "psi31", "psi41", "phi21", "phi31", "phi41", "phi51", "psi22", "psi32", "psi42", "phi32", "phi42", "phi52"],
    #    "53" : ["psi11", "psi21", "psi31", "psi41", "phi21", "phi31", "phi41", "phi51", "psi22", "psi32", "psi42", "phi32", "phi42", "phi52", "psi33", "psi43", "phi43", "phi53"],
    #    "54" : ["psi11", "psi21", "psi31", "psi41", "phi21", "phi31", "phi41", "phi51", "psi22", "psi32", "psi42", "phi32", "phi42", "phi52", "psi33", "psi43", "phi43", "phi53", "psi44", "phi54"],
    #    "55" : ["psi11", "psi21", "psi31", "psi41", "phi21", "phi31", "phi41", "phi51", "psi22", "psi32", "psi42", "phi32", "phi42", "phi52", "psi33", "psi43", "phi43", "phi53", "psi44", "phi54"],
    #}

# ok
class VHT_MIMO_CONTROL_NS(enum.Enum):
    """
    Access with str(channel_width) + str(grouping)
    """
    VAL = {
        "201" : 52,
        "202" : 30,
        "204" : 16,
        "401" : 108,
        "402" : 58,
        "404" : 30,
        "801" : 234,
        "802" : 122,
        "804" : 62,
    }

class WifiField():
    """
    Used to specify FIELD for FieldExtractors.
    It includes bitmasks and a way to interpret data masked.
    `translate` should be called by the corresponding extractor to apply.
    `create` can be used in init to create fields dynamically dependent on data in packet or to create VALUE and TRANSLATE 
    @VALUE: dict of names as keys for bitmasks
    @TRANSLATE: dict of same names as keys for interpretation callable
    """
    VALUE       : dict[str : int]
    TRANSLATE   : dict[str : typing.Callable]

    def __init__(self, **kwargs):
        self.VALUE      = kwargs.get("VALUE", {})
        self.TRANSLATE  = kwargs.get("TRANSLATE", {})

    def __str__(self):
        return "[ WifiField ]"

    def create(self, packet: Packet) -> list[dict[str : int], dict[str : typing.Callable]]:
        return self.VALUE, self.TRANSLATE

    def translate(self, data: str | bytes, base: int = 16) -> dict:
        if not ( isinstance(data, str) or isinstance(data, bytes) ):
            #print(f"[ERROR][ wififield ]: translate - data type incorrect. {str(data)}")
            return {}
        if isinstance(data, bytes):
            data = int(data.decode("utf-8"), base)
        elif isinstance(data, str):
            data = int(data, base)
        return {
                key : self.TRANSLATE.get(key, lambda x: x)(data & self.VALUE[key]) for key in self.VALUE.keys()
            }

class VHT_MIMO_CONTROL_CONTROL(WifiField):
    VALUE = {
        "Nc"                        : int("111"+0*"0"       , 2),       # how many cols
        "Nr"                        : int("111"+3*"0"       , 2),       # how many rows
        "channel_width"             : int("11"+6*"0"        , 2),       # channel_width -> #subcarrier
        "grouping"                  : int("11"+8*"0"        , 2),       # grouping      -> #subcarrier
        "codebook"                  : int("1"+10*"0"        , 2),      # quantizising steps for phi, psi
        "feedback_type"             : int("1"+11*"0"        , 2),       # `SU` or `MU`
        "remaining_fedback_segments": int("111"+12*"0"      , 2),
        "first_fedback_segment"     : int("1"+15*"0"        , 2),
        "reserved"                  : int("11"+16*"0"       , 2),
        "sounding_dialog_seg_num"   : int("111111"+18*"0"   , 2),
    }

    TRANSLATE = {
        "Nc"                        : lambda x: (x >> 0) + 1,
        "Nr"                        : lambda x: (x >> 3) + 1,
        "channel_width"             : lambda x: 
                                                20 if (x >> 6) == 0 else \
                                                    40 if (x >> 6) == 1 else 80 if (x >> 6) == 2 else 160,
        "grouping"                  : lambda x: 2**(x >> 8),
        "codebook"                  : lambda x, codebook="SU": 
                                            {"phi":2, "psi":4} if ((x >> 10) == 0 and codebook == "SU") else \
                                            {"phi":5, "psi":7} if ((x >> 10) == 0 and codebook == "MU") else \
                                            {"phi":4, "psi":6} if ((x >> 10) == 1 and codebook == "SU") else \
                                            {"phi":7, "psi":9}, #  if ((x >> 10) == 0 and codebook == "MU")
        "feedback_type"             : lambda x: "SU" if (x >> 11) == 0 else "MU",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs | (
                {
                    "VALUE" : kwargs.get("VALUE") if kwargs.get("VALUE", None) else self.VALUE
                }
            ) | 
            (
                {
                    "TRANSLATE" : kwargs.get("TRANSLATE") if kwargs.get("TRANSLATE", None) else self.TRANSLATE
                }
            )
        )

    def __str__(self):
        return super().__str__() + "[ VHT_MIMO_CONTROL ]:" + \
            ("\n\t[-] " + "\n\t[-] ".join([f"{str(x): <30} : {str(self.VALUE[x]): >30}" for x in self.VALUE.keys()]))

    def translate(self, data: str | bytes, base: int = 16) -> dict:
        parsed = super().translate(data=data, base=base)
        return parsed | {
            "Ns" : VHT_MIMO_CONTROL_NS.VAL.value.get((targ := (str(parsed.get("channel_width", "")) + str(parsed.get("grouping", "")))), f"{targ} not in Mapping"),
            #"Na" : VHT_MIMO_CONTROL_NA.VAL.value.get((targ := (str(parsed.get("Nr", "")) + str(parsed.get("Nc", "")))), f"{targ} not in Mapping"),
            "OA" : VHT_MIMO_CONTROL_OA.VAL(parsed.get("Nr", 0), parsed.get("Nc", 0)),
        }


# this works somewhat. its dead while dev bc found WiPicap that does this in cython
# could rework this code with info from wipicap
# but rather use modified version of wipicap as its known to work and its fast
# its not a complete loss one could check if there is a difference when working with q. angles instead of matrices V

class VHT_CBR(WifiField):

    VALUE       : dict[str:dict] = {}
    TRANSLATE   : dict[str:dict] = {}
    def __init__(self, **kwargs):

        VALUE, TRANSLATE = {}, {}
        if (pac:=kwargs.get("packet", None)):
            VALUE, TRANSLATE = self.create(pac)

        super().__init__(**kwargs | (
                {
                    "VALUE" : kwargs.get("VALUE")if kwargs.get("VALUE") else VALUE if VALUE else self.VALUE 
                } 
            ) | 
            (
                {
                    "TRANSLATE" : kwargs.get("TRANSLATE")  if kwargs.get("TRANSLATE") else TRANSLATE if TRANSLATE else self.TRANSLATE
                }
            )
        )

    def create(self, packet: Packet):

        value       = {}
        translate   = {}
        mimo_control = val if isinstance((val:= packet.DATA.get(ExtractorField.VHT_MIMO_CONTROL.value, {})), dict) else None
        if not mimo_control:
            return value, translate

        bphi = mimo_control.get("codebook", {}).get("phi", 0)
        bpsi = mimo_control.get("codebook", {}).get("psi", 0)
        angle_order =  mimo_control.get("OA", [])[::-1]
        ns = mimo_control.get("Ns", 0)

        shift = 0
        for sub in range(ns-1, -1, -1):
            value[sub]      = {}
            translate[sub]  = {}
            for angle in angle_order:
                bit = bphi if "phi" in angle else bpsi
                value[sub][angle]       = int("1"*bit+"0"*shift, 2)
                #print(value[sub][angle])
                translate[sub][angle]   = lambda x, s=shift: x>>s
                #print(translate[sub][angle](value[sub][angle]))
                shift += bit
        value["SNR"]       = int("1"*8+"0"*shift, 2)
        translate["SNR"]   = lambda x, s=shift: (((x>>s) ^ 0xff) + 0x1) * 0.25 - 10 # prob no good
        return value, translate

    def __str__(self):
        return super().__str__() + "[ VHT_CBR ]:" + \
            ("\n\t[-] " + "\n\t[-] ".join([f"{str(x): <30} : {str(self.VALUE[x]): >30}" for x in self.VALUE.keys()]))
    
    def translate(self, data: str | bytes, base: int = 16) -> dict:
        if not ( isinstance(data, str) or isinstance(data, bytes) ):
            #print(f"[ERROR][ wififield ]: translate - data type incorrect. {str(data)}")
            return {}
        if isinstance(data, bytes):
            data = int(data.decode("utf-8"), base)
        elif isinstance(data, str):
            data = int(data, base)
        out = {}
        #print(self.VALUE, self.TRANSLATE)
        for sub in self.VALUE.keys():
            #print(self.VALUE.get(sub))
            if isinstance((ang:= self.VALUE.get(sub)), dict):
                f = self.TRANSLATE.get(sub, {})
                #print("DATA:", str([f.get(key)(data & ang.get(key, 0)) for key in ang.keys()]))
                out[sub] = {
                    key : f.get(key)(data & ang.get(key, 0)) for key in ang.keys()
                }
                #print(out[sub])
            else:
                out[sub] = self.TRANSLATE.get(sub, lambda x: x)(data & ang)
        #print(out)
        return out