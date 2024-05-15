import unittest
from wifisidechannels import units
from wifisidechannels import components as cpt
from wifisidechannels import models as mod
import numpy as np
import os
import shlex


class TestStuff(unittest.TestCase):


    def test_qunatized_CBR_extract(
            file: str = None,
            v:bool=False,
            vv: bool = False
    ):

        print("[*] Extracting quantised spi & phi from VHT CBR")
        TX = units.txbf.TxBf(**{
            "set_up" : os.path.join("bash", "setup_device.sh") 
        })
        hex_mac = "d83adde5662c"
        MAC = ":".join([hex_mac[i: i+2] for i in range(0, len(hex_mac), 2)])
        preset = mod.presets.TSHARK_FIELDS_VHT
        preset.COM_FILTER.append(mod.models.TsharkDisplayFilter.MAC_TA.value.replace(mod.models.placeholder, MAC))
        pac = TX.process_capture(kwargs={
            "read_file" : shlex.quote(os.path.join("DUMP", "0txbf.pcapng")) if file is None else shlex.quote(file),
            "filter_fields" : str(preset)
        })


        ext_c = cpt.extractor.VHT_MIMO_CONTROL_Extractor()
        processor   = cpt.packet_processor.PacketProcessor()
        new_pac = processor.parse(todo=pac, extract=ext_c)

        for p in new_pac:
            field = mod.models.VHT_CBR(**{
                        "packet" : p
                    }
            )
            ext_r = cpt.extractor.VHT_BEAMFORMING_REPORT_Extractor(**(
                {
                    "FIELD" : field
                }
            ))
            if vv:
                print("EXTRACTOR:", ext_r)
                print("FIELD: ", field)
            if v:
                print("MIMO_C: ", p.DATA.get(mod.models.ExtractorField.VHT_MIMO_CONTROL.value, "NAN"))
                print("CBR: ", p.DATA.get(mod.models.TsharkField.VHT_CBR.value, "NAN"))
            p.DATA  |= ext_r.apply(p)
            if v:
                print("CBR Parsed: ", p.DATA.get(mod.models.ExtractorField.VHT_CBR_PARSED.value, "NAN"))

        return new_pac

    def test_V_extract(
            file: str = None,
            packets: mod.models.Packet = None,
            v:bool = False,
            vv:bool = False
    ):
        print("[*] Extracting Extracting phi & psi from CBR, dequantize and Decompress to extract Feedback Matrix Q.")

        TX = units.txbf.TxBf(**{
            "set_up" : os.path.join("bash", "setup_device.sh") 
        })
        if not packets:
            hex_mac = "d83adde5662c"
            MAC = ":".join([hex_mac[i: i+2] for i in range(0, len(hex_mac), 2)])
            preset = mod.presets.TSHARK_FIELDS_VHT
            preset.COM_FILTER.append(mod.models.TsharkDisplayFilter.MAC_TA.value.replace(mod.models.placeholder, MAC))
            pac = TX.process_capture(kwargs={
                "read_file" : shlex.quote(os.path.join("DUMP", "0txbf.pcapng")) if file is None else shlex.quote(file),
                "filter_fields" : str(preset)
            })
        else:
            pac = packets
        pac = TX.process_VHT_MIMO_CONTROL(packets=pac)
        pac, V, T = TX.process_VHT_COMPRESSED_BREAMFROMING_REPORT(packets=pac, check=True)
        if v:
            for p in pac:
                M  = p.DATA.get(mod.models.ExtractorField.VHT_STEERING_MATRIX.value)
                Nc = p.DATA.get(mod.models.ExtractorField.VHT_MIMO_CONTROL.value, {}).get("Nc","")
                Nr = p.DATA.get(mod.models.ExtractorField.VHT_MIMO_CONTROL.value, {}).get("Nr","")
                print(f"* Packet @ {str(p.TIME)}:\t Nr x Nc: {str(Nr): >3} x {str(Nc): >3}\tV.shape: {str(M.shape) if isinstance(M, np.ndarray) else 'None'}")
        return pac

    def test_V_plot(
            packets: mod.models.Packet,
            v: bool=False
    ):
        TX = units.txbf.TxBf(**{
            "set_up" : os.path.join("bash", "setup_device.sh") 
        })
        DF = {
            "var"       : {
                "f" : lambda x: np.var(x),
                "data" : {

                }
            },
            "angle"     : {
                "f" : lambda x: np.sum(np.angle(x)),
                "data" : {
                }
            },
            "angle_mean": {
                "f" : lambda x: np.sum(np.angle(np.mean(x))),
                "data" : {

                }
            }
        }
        for l in [1, 2, 3]:
            DF |= {
                f"l{l}_norm"   : {
                    "f" : lambda x, l=l: np.power(np.sum(np.power(np.abs(x), l)), 1/l),
                    "data" : {}
                }
            }
        for p in packets:
            V       = p.DATA.get(mod.models.ExtractorField.VHT_STEERING_MATRIX.value, None)
            time    = p.DATA.get(mod.models.TsharkField.FRAME_TIME.value, None)
            if V is None or time is None:
                continue
            #print(V.shape)
            for i, sub_v in enumerate(V[0]):
                #print(sub_v.shape)
                for x in DF.keys():
                    if not (sub := DF[x]["data"].get(i, None)):
                        DF[x]["data"][i] = []
                        sub = DF[x]["data"][i]
                    if v:
                        print(f"[ {x} ]: {[[time , val ]] if not np.isnan((val:= DF[x]['f'](sub_v))) else []}")
                    sub += [[time , val ]] if not np.isnan((val:= DF[x]["f"](sub_v))) else []

        # time_epoch seams to be not unique
        for x in DF.keys():
            domains = []
            domain = []
            #print(x)
            for i, sub in enumerate((keys:=list(DF[x]["data"].keys()))):
                domains += val if ( val:= sorted([[x[0] for x in DF[x]["data"][sub]]])) not in domains else []
                #print(val, "X" if val[0] else "y")
                #print(DF[x]["data"][sub])
                TX.m_plotter.plot_data(
                    data=DF[x]["data"][sub],
                    msg=f"[ {x} ]",
                    label=f"Sc: {sub}",
                    plot=(i == (len(keys) - 1)),
                    scatter=False
                )
            #print(len(domains))

def main():
    unittest.main()
if __name__ == '__main__':

    main()