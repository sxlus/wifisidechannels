import enum
import wifisidechannels.models.models as models

TSHARK_FIELDS_VHT = models.TsharkDisplayConfig(
    name="[ VHT ]",
    fields=[
        models.TsharkField.FRAME_TIME,
        models.TsharkField.MAC_SA,
        models.TsharkField.MAC_DA,
        models.TsharkField.VHT_MIMO_CONTROL_CONTROL,
        models.TsharkField.VHT_COMPRESSED_BEAMAFORMINGREPORT,
    ],
    filter=[
        models.TsharkDisplayFilter.VHT_ACTION_NO_ACK
    ]
)