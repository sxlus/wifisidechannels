import numpy as np
import pathlib

import wifisidechannels.units.wifi as wifi
import wifisidechannels.models.models as models
import wifisidechannels.components.packet_processor as packet_processor
import wifisidechannels.components.extractor as extractor
import wifisidechannels.components.wipicap.wipicap as wipicap

class TxBf(wifi.WiFi):

    """
    @Job:   Decodes and Decompresses "VHT compressed beamfroming reports"

    """

    def __init__(self, **kwargs):
        super().__init__(
            **(kwargs | 
                (
                    {
                            "name": "[ txbf ]" if not kwargs.get("name") else kwargs.get("name")
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
            packets: list[models.Packet] | None = None,
            check: bool = True,
            bandwidth: list[int] | int | None = None,
    ) -> list[list[models.Packet], list, list] | None:

        """
        The cython function used need uniform sized packets with respect to CBR
        SO: Nc, Nr, Ns, channel_width, grouping of all packets to `get_v_matrix` should be the same.
        In order to make use of `get_v_matrix` one should provide `mimo_control` dict in packet.DATA.
        This can be done using process_VHT_MIMO_CONTROL
        @PARAM:     check: False -> exspects packets to be uniform and in posession of `mimo_control` data. if not silent skip.
                    check: True  -> batches uniform packets with respect to CBR size and generates if necessary mimo_control. ( convenient, but slower )
        """
        if packets is None:
            packets = self.m_data
        if not packets:
            print(f"{self.m_name}[ process_VHT_COMPRESSED_BREAMFROMING_REPORT ][ WARN ] Got no packets to parse! CHECK!")
            return None
    
        if isinstance(bandwidth, int):
            bandwidth = [bandwidth]
        if check:
            out_v = []
            out_t = []
            ## setup MIMO_CONTROL_EXTRACTOR
            extract_MIMO_CONTROL = extractor.VHT_MIMO_CONTROL_Extractor()
            check_bw = lambda x: x in bandwidth if bandwidth is not None else True
            # grouping is not precise
            groups = {}
            for packet in packets:
                if not (cbr := packet.DATA.get(models.TsharkField.VHT_CBR.value)):
                    continue
                if not packet.DATA.get(models.ExtractorField.VHT_MIMO_CONTROL.value):
                    packet.DATA |= extract_MIMO_CONTROL.apply(packet)
                if not (check_bw(( bw := packet.DATA.get(models.ExtractorField.VHT_MIMO_CONTROL.value, {}).get("channel_width","")))):
                    continue
                if not bw in groups.keys():
                    # allow one byte off -> does not imply different dims of V
                    if not bw in groups.keys():
                        groups[bw] = []
                groups[bw].append(packet)

            for size in groups.keys():
                v, t = wipicap.get_v_matrix(packets=groups[size])
                out_v.append(v)
                out_t.append(t)

            return packets, out_v, out_t

        return packets, wipicap.get_v_matrix(packets)


    def plot_V_time_series(self) -> None:
        pass
    def plot_A_time_series(self) -> None:
        pass

    def plot_feedback_hist(
            self,
            packets: models.Packet | None = None,
            bfi_data: np.ndarray | None = None,
            dpi: int = 200,
            size: tuple = (20,10),
            plot: bool = True,
            save_file: pathlib.Path = None,
            window_title: str = None,
            bandwidth: list[int] | int = None,
            plot_spatial: list[int] = None,
            v: bool=False
    ) -> None:

        if bfi_data is None and packets is None:
            print(f"{self.m_name}[ plot_feedback_hist ][ ERROR ] Need data or packets")
            return
        if packets is not None:
            input_data = packets
        else:
            input_data = bfi_data

        if isinstance(bandwidth, int):
            bandwidth = [bandwidth]

        data = {}
        for w, packet in enumerate(input_data):
            if packets is not None:
                V       = packet.DATA.get(models.ExtractorField.VHT_STEERING_MATRIX.value, None)
                if V is None:
                    continue
                if bandwidth:
                    bw = packet.DATA.get(models.ExtractorField.VHT_MIMO_CONTROL.value, {}).get("channel_width","")
                    if bw not in bandwidth:
                        continue
            else:
                V       = packet

            if v: print(f"P_{w}.shape: {V.shape}")

            V = V[0]
            new = {}
            for sub_c, sub_v in enumerate(V):
                for i in range(len(sub_v)):
                    #for j in range(len(sub_v[i])):
                    key = f"{i},{0}"
                    if key not in new.keys():
                        new[key] = []
                    
                    new[key].append(np.abs(sub_v[i][0]))
                    #print(f"\t{key}: {sub_v[i][0]} {np.abs(sub_v[i][0])}")
            for x in new.keys():
                if x not in data.keys():
                    data[x] = [ [y] for y in new[x] ]
                else:
                    for i in range(len(new[x])):
                        if i < len(data[x]):
                            data[x][i].append(new[x][i])
                        else:
                            #print(x)
                            #print(data[x])
                            #print(new[x])
                            data[x].append( [ 0 for _ in range(len(data[x][0]) - 1) ] + [ new[x][i] ] )
            for x in data.keys():
                if x not in new.keys():
                    for i in range(len(data[x])):
                        data[x][i].append(0)
                else:
                    if len(data[x]) > len(new[x]):
                        for l in range(len(new[x]), len(data[x])):
                            data[x][l].append(0)
            for x in data.keys():
                i = len(data[x][0])
                j = len(data[x][-1])
                if i != j:
                    print("Error", i, j)
                    return
        self.m_plotter.plot_data(
            data=[ data[spatial] for spatial in data.keys() if int(spatial[0],10) in plot_spatial] if plot_spatial and len(plot_spatial) > 1 \
                    else [ data[spatial] for spatial in data.keys() if int(spatial[0],10) in plot_spatial][0] if plot_spatial and len(plot_spatial) == 1 \
                        else [ data[spatial] for spatial in data.keys() ],
            msg=[ f"[ abs(V_{spatial}) ]" for spatial in data.keys() if int(spatial[0],10) in plot_spatial] if plot_spatial  and len(plot_spatial) > 1 \
                    else [ f"[ abs(V_{spatial}) ]" for spatial in data.keys() if int(spatial[0],10) in plot_spatial][0] if plot_spatial and len(plot_spatial) == 1 \
                        else [ f"[ abs(V_{spatial}) ]" for spatial in data.keys() ],
            xlabel="Time",
            ylabel="Sub carrier index",
            subplots=True if not plot_spatial or len(plot_spatial) > 1 else False,
            save_file=save_file,
            dpi=dpi,
            size=size,
            plot=plot,
            window_title=window_title,
            imshow=True
            )

    def plot_feedback_packet(
            self,
            packet: models.Packet,
            save_file: pathlib.Path = None,
            dpi: int = 200,
            size: tuple = (20,10),
            plot: bool = True,
            v: bool=False,
            window_title: str = None
            ) -> None:

        data = {}
        V       = packet.DATA.get(models.ExtractorField.VHT_STEERING_MATRIX.value, None)

        if V is None:
            return
        if v: print(V.shape)
        V = V[0]
        for sub_v in V:
            for i in range(len(sub_v)):
                #for j in range(len(sub_v[i])):
                key = f"{i},{0}"
                if v: print(f"\t{key}: {sub_v[i][0]}")
                if key not in data.keys():
                    data[key] = []
                data[key].append(np.abs(sub_v[i][0]))
                #print(f"\t{key}: {sub_v[i][0]} {np.abs(sub_v[i][0])}")
        
        if v: print([ data[spatial] for spatial in data.keys() ])
        self.m_plotter.plot_data(
            data=[ data[spatial] for spatial in data.keys() ],
            msg=[ f"[ abs(V_{key}) ]" for key in data.keys() ],
            xlabel="Sub carrier index",
            ylabel="Magnitude",
            subplots=True,
            save_file=save_file,
            dpi=dpi,
            size=size,
            plot=plot,
            window_title=window_title
            )
        return True


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