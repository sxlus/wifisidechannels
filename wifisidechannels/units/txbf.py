import numpy as np

import wifisidechannels.units.wifi as wifi
import wifisidechannels.models.models as models
import wifisidechannels.components.packet_processor as packet_processor
import wifisidechannels.components.extractor as extractor
import wifisidechannels.components.wipicap.wipicap as wipicap

class TxBf(wifi.WiFi):

    """
    @Job:   Decodes and Decompresses "VHT compressed beamfroming reports"

    """

    m_name: str = "[ txbf ]"

    def __init__(self, **kwargs):
        super().__init__(
            **(kwargs | 
                (
                    {
                            "name": self.m_name if not kwargs.get("name") else kwargs.get("name")
                    }
                )
            )
        )

    def process_VHT_MIMO_CONTROL(
            self,
            packets: list[models.Packet]
    ) -> list[models.Packet]:
        extract     = extractor.VHT_MIMO_CONTROL_Extractor()
        processor   = packet_processor.PacketProcessor(
            name = extract.KEY,
            extracttor = extract,
            todo = packets
        )
        return processor.parse()

    def process_VHT_COMPRESSED_BREAMFROMING_REPORT(
            self,
            packets: list[models.Packet],
            check=True
    ) -> list[list[models.Packet], list, list]:

        """
        The cython function used need uniform sized packets with respect to CBR
        SO: Nc, Nr, Ns, channel_width, grouping of all packets to `get_v_matrix` should be the same.
        In order to make use of `get_v_matrix` one should provide `mimo_control` dict in packet.DATA.
        This can be done using process_VHT_MIMO_CONTROL
        @PARAM:     check: False -> exspects packets to be uniform and in posession of `mimo_control` data. if not silent skip.
                    check: True  -> batches uniform packets with respect to CBR size and generates if necessary mimo_control. ( convenient, but slower )
        """

        if check:
            out_v = []
            out_t = []
            ## setup MIMO_CONTROL_EXTRACTOR
            extract_MIMO_CONTROL = extractor.VHT_MIMO_CONTROL_Extractor()

            # grouping is not precise
            groups = {}
            for packet in packets:
                if not (cbr := packet.DATA.get(models.TsharkField.VHT_CBR.value)):
                    continue
                if not (l_cbr:=len(cbr)) in groups.keys():
                    # allow one byte off -> does not imply different dims of V
                    if not l_cbr+8 in groups.keys() and not l_cbr-8 in groups.keys():
                        groups[l_cbr] = []
                    elif l_cbr-8 in groups.keys():
                        l_cbr -= 8
                    elif l_cbr+8 in groups.keys():
                        l_cbr += 8

                groups[l_cbr].append(packet)
                if not packet.DATA.get(models.ExtractorField.VHT_MIMO_CONTROL.value):
                    packet.DATA |= extract_MIMO_CONTROL.apply(packet)
            for size in groups.keys():
                v, t = wipicap.get_v_matrix(packets=groups[size])
                out_v.append(v)
                out_t.append(t)

            return packets, out_v, out_t

        return packets, wipicap.get_v_matrix(packets)

    def classify(self):
        """
        1D CNN with adversarial learning framework optimizing domain discriminator and value predictor.
        In its own class. Here interface with purpose.
        """
        pass

    def preprocess_data(self):
        """
        Does all that is necessary to prepare data for training.
        """
        pass

    def SRA(self):
        """
        Sparse recovery algorithm as proposed by Hu et. al. Autoencoder framework with 1D CNN.
        In its own class. Here interface with purpose.
        """
        pass

    def segment(self):
        """
        Segmentation of samples using Constant false alarm rate algorithm.
        """
        pass