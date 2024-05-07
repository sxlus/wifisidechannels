import enum
import wifisidechannels.models.models as models
import wifisidechannels.components.extractor as extractor


class TsharkDisplayConfig():
    NAME: str                                   = ""
    COM_FIELD: list[models.TsharkField]                = []
    COM_FILTER: list[models.TsharkDisplayFilter]       = []

    def __init__(
            self,
            name: str = "",
            fields: list[models.TsharkField] = [],
            filter: list[models.TsharkDisplayFilter] = [],
    ):
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

TSHARK_FIELDS_VHT = TsharkDisplayConfig(
    name="[ VHT ]",
    fields=[
        models.TsharkField.FRAME_TIME,
        models.TsharkField.MAC_SA,
        models.TsharkField.MAC_DA,
        models.TsharkField.VHT_MIMO_CONTROL_CONTROL,
        models.TsharkField.VHT_COMPRESSED_BEAMFORMINGREPORT,
    ],
    filter=[
        models.TsharkDisplayFilter.VHT_ACTION_NO_ACK
    ]
)