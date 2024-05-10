import enum
import wifisidechannels.models.models as models
import wifisidechannels.components.extractor as extractor


class TsharkDisplayConfig():
    NAME: str                                   = ""
    COM_FIELD: list[str]                = []
    COM_FILTER: list[str]               = []

    def __init__(
            self,
            name: str = "",
            fields: list[str] = [],
            filter: list[str] = [],
    ):
        self.NAME           = str(name)
        self.COM_FIELD      = fields
        self.COM_FILTER     = filter

    def __str__(self):
        return ("-F '" + " && ".join([ str(filt) for filt in self.COM_FILTER]) + "' " if self.COM_FILTER else "") \
            + ("-E " + ",".join( [ str(field) for field in self.COM_FIELD ] ) if self.COM_FIELD else "")

    def extractor(self):
        return [
            extractor.ColumnExtractor(
                **{
                    "KEY" : field,
                    "COLUMN": i,
                    "DELIM": "\t"
                }
            ) for i, field in enumerate(self.COM_FIELD)
        ]

TSHARK_FIELDS_VHT = TsharkDisplayConfig(
    name="[ VHT ]",
    fields=[
        models.TsharkField.FRAME_TIME.value,
        models.TsharkField.MAC_SA.value,
        models.TsharkField.MAC_DA.value,
        models.TsharkField.VHT_MIMO_CONTROL_CONTROL.value,
        models.TsharkField.VHT_CBR.value,
    ],
    filter=[
        models.TsharkDisplayFilter.VHT_ACTION_NO_ACK.value
    ]
)