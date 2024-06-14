import unittest
from wifisidechannels import units
from wifisidechannels import components as cpt
from wifisidechannels import models as mod
import numpy as np
import os
import shlex
import pathlib
import typing
import joblib


DF = {
    "ID"        : {
        "f" : lambda x: np.sum(np.abs(x))/len(x) if isinstance(x, typing.Iterable) else x,
        "data": {
        }
    },
    "var"       : {
        "f" : lambda x: np.var(x),
        "data" : {

        }
    },
    "sum_angle"     : {
        "f" : lambda x: np.sum(np.angle(x)),
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

class TestStuff(unittest.TestCase):


    def test_qunatized_CBR_extract(
            file: str = None,
            packets: list = None,
            mac_sa: str = None,
            mac_da: str = None,
            v:bool=False,
            timeout: int = None,
            vv: bool = False,
            save_file: pathlib.Path = None,
    ):

        print("[*] Extracting quantised psi & phi from VHT CBR")

        preset = mod.presets.TSHARK_FIELDS_VHT
        if isinstance(mac_sa, str):
            preset.add_filter(mod.models.TsharkDisplayFilter.MAC_SA.value, preset.vrfy_mac(mac_sa))
        if isinstance(mac_da, str):
            preset.add_filter(mod.models.TsharkDisplayFilter.MAC_DA.value, preset.vrfy_mac(mac_da))

        if packets is None:
            TX = units.txbf.TxBf(**{
                "set_up" : os.path.join("bash", "setup_device.sh") 
            })
            pac = TX.process_capture(kwargs={
                "read_file" : shlex.quote(os.path.join("DUMP", "0txbf.pcapng")) if file is None else shlex.quote(file),
                "filter_fields" : str(preset),
            } | ({
                "timeout" : timeout
            } if timeout else {})
            )

        else:
            pac = packets

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

        if save_file:
            print(f"\t[*] Writing packets with parsed CBR to: {save_file}.")
            joblib.dump(new_pac, filename=save_file)
        return new_pac


    def test_angle_plot(
            packets: mod.models.Packet,
            plot_sub: bool = False,
            save_file: pathlib.Path = None,
            show_plots: bool = True,
            v: bool=False
    ):
        TX = units.txbf.TxBf(**{
            "set_up" : os.path.join("bash", "setup_device.sh") 
        })

        for p in packets:
            angles          = p.DATA.get(mod.models.ExtractorField.VHT_CBR_PARSED.value, None)
            time            = p.DATA.get(mod.models.TsharkField.FRAME_TIME.value, None)
            if angles is None or time is None:
                continue

            all = { x: 0 for x in DF.keys() }
            for x in DF.keys():
                if not DF[x]["data"].get("all", False):
                    DF[x]["data"]["all"] = []

                for sub_v in angles.keys():
                    if not (sub := DF[x]["data"].get(sub_v, None)):
                        DF[x]["data"][sub_v] = []
                    if isinstance(angles[sub_v], dict):
                        values = [ angles.get(sub_v, {})[x] for x in angles[sub_v].keys() ]
                    else:
                        values = [ angles[sub_v] ]
                        if v:
                            print(f"[ {x} ]: {[[time , val ]] if not np.isnan((val:= DF[x]['f'](values))) else []}")

                    DF[x]["data"][sub_v] += [[time , val ]] if not np.isnan((val:= DF[x]["f"](values))) else []
                    all[x] += val

                DF[x]["data"]["all"] += [ [time, all[x]/(len(values)*len(angles.keys()))] ]

        if plot_sub:
            for x in DF.keys():
                for i, sub in enumerate((keys:=list(DF[x]["data"].keys()))):
                    TX.m_plotter.plot_data(
                        data=DF[x]["data"][sub],
                        msg=f"[ {x} ][ SUB: {sub} ]",
                        label=f"Sc: {sub}",
                        plot=show_plots,
                        scatter=False,
                        save_file=os.path.join(save_file.parents[0], save_file.stem + f"_{x}_{str(sub)}" + save_file.suffix) if save_file and not show_plots else None
                    )
        else:
            for x in DF.keys():
                TX.m_plotter.plot_data(
                    data=DF[x]["data"].get("all", []),
                    msg=f"[ mean over subs ][ {x} ]",
                    label=f"mean over subs: {x}",
                    plot=show_plots,
                    scatter=False,
                    save_file=os.path.join(save_file.parents[0], save_file.stem + f"_{x}" + save_file.suffix) if save_file and not show_plots else None
                )

        # reset DF
        for x in DF.keys():
            DF[x]["data"] = {}

    def test_V_extract(
            file: str = None,
            packets: mod.models.Packet = None,
            timeout: int = None,
            mac_sa: str = None,
            mac_da: str = None,
            save_file: pathlib.Path = None,
            v:bool = False,
    ):

        print("[*] Extracting Extracting phi & psi from CBR, dequantize and Decompress to extract Feedback Matrix V.")

        TX = units.txbf.TxBf(**{
            "set_up" : os.path.join("bash", "setup_device.sh") 
        })
        preset = mod.presets.TSHARK_FIELDS_VHT
        if isinstance(mac_sa, str):
            preset.add_filter(mod.models.TsharkDisplayFilter.MAC_SA.value, preset.vrfy_mac(mac_sa))
        if isinstance(mac_da, str):
            preset.add_filter(mod.models.TsharkDisplayFilter.MAC_DA.value, preset.vrfy_mac(mac_da))
        if not packets:
            pac = TX.process_capture(kwargs={
                "read_file" : shlex.quote(os.path.join("DUMP", "0txbf.pcapng")) if file is None else shlex.quote(file),
                "filter_fields" : str(preset)
                } | ({
                    "timeout" : timeout
                } if timeout else {})
            )
        else:
            pac = packets

        pac = TX.process_VHT_MIMO_CONTROL(packets=pac)
        pac, V, T = TX.process_VHT_COMPRESSED_BREAMFROMING_REPORT(packets=pac, check=True)
        if v:
            for p in pac:
                M  = p.DATA.get(mod.models.ExtractorField.VHT_STEERING_MATRIX.value)
                Nc = p.DATA.get(mod.models.ExtractorField.VHT_MIMO_CONTROL.value, {}).get("Nc","")
                Nr = p.DATA.get(mod.models.ExtractorField.VHT_MIMO_CONTROL.value, {}).get("Nr","")
                print(f"* Packet @ {str(p.TIME)}:\t Nr x Nc: {str(Nr): <2} x {str(Nc): >2}\tV.shape: {str(M.shape) if isinstance(M, np.ndarray) else 'None'}")

        if save_file:
            print(f"\t[*] Writing Feedbackmatrices V to: {os.path.join(save_file.parents[0], save_file.stem + '_V' + save_file.suffix): >64}.")
            print(f"\t[*] Writing Time T to: {os.path.join(save_file.parents[0], save_file.stem + '_T' + save_file.suffix): >76}.")
            joblib.dump(V, os.path.join(save_file.parents[0], save_file.stem + "_V" + save_file.suffix))
            joblib.dump(T, os.path.join(save_file.parents[0], save_file.stem + "_T" + save_file.suffix))

        return pac

    def test_V_plot(
            packets: mod.models.Packet,
            plot_sub: bool = False,
            save_file: pathlib.Path = None,
            show_plots: bool = True,
            v: bool=False
    ):
        TX = units.txbf.TxBf(**{
            "set_up" : os.path.join("bash", "setup_device.sh") 
        })

        for p in packets:
            V       = p.DATA.get(mod.models.ExtractorField.VHT_STEERING_MATRIX.value, None)
            time    = p.DATA.get(mod.models.TsharkField.FRAME_TIME.value, None)
            if V is None or time is None:
                #print("exit")
                continue
            all = { x: 0 for x in DF.keys() }
            for i, sub_v in enumerate(V[0]):
                for x in DF.keys():
                    if not DF[x]["data"].get("all"):
                        DF[x]["data"]["all"] = []
                    if not (sub := DF[x]["data"].get(i, None)):
                        DF[x]["data"][i] = []
                    if v:
                        print(f"[ {x} ]: {[[time , val ]] if not np.isnan((val:= DF[x]['f'](sub_v))) else []}")
                    DF[x]["data"][i] += [[ time , val ]] if not np.isnan((val:= DF[x]["f"](sub_v))) else []
                    all[x] += val

            for x in DF.keys():
                DF[x]["data"]["all"] += [ [time, all[x]/len(V[0])] ]

        if plot_sub:
            for x in DF.keys():
                for i, sub in enumerate((keys:=list(DF[x]["data"].keys()))):
                    TX.m_plotter.plot_data(
                        data=DF[x]["data"][sub],
                        msg=f"[ {x} ][ SUB: {sub} ]",
                        label=f"Sc: {sub}",
                        plot=show_plots,
                        scatter=False,
                        save_file=os.path.join(save_file.parents[0], save_file.stem + f"_{x}_{str(sub)}" + save_file.suffix) if save_file and not show_plots else None
                    )
        else:
            for x in DF.keys():
                TX.m_plotter.plot_data(
                    data=DF[x]["data"].get("all", []),
                    msg=f"[ mean over subs ][ {x} ]",
                    label="mean_of_sub",
                    plot=show_plots,
                    scatter=False,
                    save_file=os.path.join(save_file.parents[0], save_file.stem + f"_{x}" + save_file.suffix) if save_file and not show_plots else None
                )

        # reset DF
        for x in DF.keys():
            DF[x]["data"] = {}

def main():
    unittest.main()
if __name__ == '__main__':

    main()