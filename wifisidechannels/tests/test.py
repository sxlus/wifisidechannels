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


DFV = {
    "ID"        : {
        "f" : lambda V: { i if j==0 else i+1+j: np.sum(np.abs(V[i][j])) for i in range(len(V)) for j in range(len(V[i]))} if isinstance(V, typing.Iterable) else V,
        "data": {
        }
    },
    "var"       : {
        "f" : lambda V: {i if j==0 else i+1+j:np.var(V[i][j]) for i in range(len(V)) for j in range(len(V[i]))},
        "data" : {
        }
    },
#    "sum_angle"     : {
#        "f" : lambda V: {i:np.sum(np.abs(np.angle(V[i]))) for i in range(len(V))},
#        "data" : {
#        }
#    }
}


DFA = {
    "ID"        : {
        "f" : lambda V: V,
        "data": {
        }
    },
#    "var"       : {
#        "f" : lambda V: {i:np.var(V[i]) for i in range(len(V))},
#        "data" : {
#        }
#    },
#    "sum_angle"     : {
#        "f" : lambda V: {i:np.sum(np.abs(np.angle(V[i]))) for i in range(len(V))},
#        "data" : {
#        }
#    }
}

for l in [2]:
    DFV |= {
        f"l{l}_norm"   : {
            "f" : lambda V, l=l: {i if j==0 else i+1+j:np.power(np.sum(np.power(np.abs(V[i][j]), l)), 1/l) for i in range(len(V)) for j in range(len(V[i]))},
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
            subplots: bool = False,
            v: bool=False
    ):
        TX = units.txbf.TxBf(**{
            "set_up" : os.path.join("bash", "setup_device.sh") 
        })
        v = False
        for p in packets:
            angles          = p.DATA.get(mod.models.ExtractorField.VHT_CBR_PARSED.value, None)
            time            = p.DATA.get(mod.models.TsharkField.FRAME_TIME.value, None)
            if angles is None or time is None:
                continue

            for x in DFA.keys():
                for sub_c in [ x for x in angles.keys() if x != "SNR" ]:
                    if not DFA[x]["data"].get(sub_c, None):
                        DFA[x]["data"][sub_c] = {}

                    if v:
                        print(f"[ {x} ]: {[[time , angles[sub_c] ]] if isinstance(angles[sub_c], dict) else []}")

                    for psiphy in angles[sub_c].keys():
                        if not DFA[x]["data"][sub_c].get(psiphy, None):
                            DFA[x]["data"][sub_c][psiphy] = []
                        DFA[x]["data"][sub_c][psiphy] += [[time , angles[sub_c][psiphy] ]]

        for x in DFA.keys():
            subs = list(DFA[x]["data"].keys())
            if plot_sub == []:
                subs_to_plot = subs
            else:
                subs_to_plot = plot_sub

            for sub_c in [ x for x in subs_to_plot if x in subs ]:
                if not subplots:
                    for i, psyphy in enumerate(list(DFA[x]["data"][sub_c].keys())):
                        TX.m_plotter.plot_data(
                            data=DFA[x]["data"][sub_c][psyphy],
                            msg=f"[ angles ][ {x} ][ SUB: {sub_c} ]",
                            label=f"Angle: {psyphy}",
                            plot=show_plots and (i == (len(list(DFA[x]["data"][sub_c].keys()))-1)),
                            scatter=False,
                            subplots=subplots,
                            save_file=os.path.join(save_file.parents[0], save_file.stem + f"_{x}_{str(sub_c)}" + save_file.suffix) if save_file and not show_plots else None
                        )
                else:
                    data = [ DFA[x]["data"][sub_c][psyphy] for psyphy in DFA[x]["data"][sub_c].keys() ]
                    TX.m_plotter.plot_data(
                            data=data,
                            msg=f"[ angles ][ {x} ][ SUB: {sub_c} ]",
                            label=[f"Angle: {psyphy}" for psyphy in DFA[x]["data"][sub_c].keys() ],
                            plot=show_plots,
                            scatter=False,
                            subplots=subplots,
                            save_file=os.path.join(save_file.parents[0], save_file.stem + f"_{x}_{str(sub_c)}" + save_file.suffix) if save_file and not show_plots else None
                        )
        # reset DF
        for x in DFA.keys():
            DFA[x]["data"] = {}

    def test_V_extract(
            file: str = None,
            packets: mod.models.Packet = None,
            timeout: int = None,
            mac_sa: str = None,
            mac_da: str = None,
            save_file: pathlib.Path = None,
            bandwidth: list[int] | int = None,
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
        pac, V, T = TX.process_VHT_COMPRESSED_BREAMFROMING_REPORT(packets=pac, check=True, bandwidth=bandwidth)

        if v:
            for p in pac:
                M  = p.DATA.get(mod.models.ExtractorField.VHT_STEERING_MATRIX.value)
                Nc = p.DATA.get(mod.models.ExtractorField.VHT_MIMO_CONTROL.value, {}).get("Nc","")
                Nr = p.DATA.get(mod.models.ExtractorField.VHT_MIMO_CONTROL.value, {}).get("Nr","")
                print(f"* Packet @ {str(p.TIME)}:\t Nr x Nc: {str(Nr): <2} x {str(Nc): >2}\tV.shape: {str(M.shape) if isinstance(M, np.ndarray) else 'None'}")

        if save_file:
            v_file = os.path.join(save_file.parents[0], save_file.stem + '_V' + save_file.suffix)
            t_file = os.path.join(save_file.parents[0], save_file.stem + '_T' + save_file.suffix)
            print(f"\t[*] Writing Feedbackmatrices V to: {v_file: >64}.")
            print(f"\t[*] Writing Time T to: {t_file: >76}.")
            joblib.dump(V, v_file)
            joblib.dump(T, t_file)

        return pac

    def test_V_plot(
            packets: mod.models.Packet,
            plot_sub: list[int] = [],
            save_file: pathlib.Path = None,
            show_plots: bool = True,
            subplots: bool = False,
            v: bool=False
    ):

        TX = units.txbf.TxBf(**{
            "set_up" : os.path.join("bash", "setup_device.sh") 
        })
        for p in packets:
            V       = p.DATA.get(mod.models.ExtractorField.VHT_STEERING_MATRIX.value, None)
            time    = p.DATA.get(mod.models.TsharkField.FRAME_TIME.value, None)

            if V is None or time is None:
                continue
            for idx in range(len(V)):
                for sub_c, sub_v in enumerate(V[idx]):
                    for x in DFV.keys():
                        if not DFV[x]["data"].get(sub_c):
                            DFV[x]["data"][sub_c] = {}

                        val = DFV[x]['f'](sub_v)

                        if v:
                            print(f"[ {x} ]: {[ time , [ val[spatial] for spatial in val.keys() ] ] if isinstance(val, dict) else []}")
                        for spatial in val.keys():
                            if DFV[x]["data"][sub_c].get(spatial, None) is None:
                                DFV[x]["data"][sub_c][spatial] = []
                            DFV[x]["data"][sub_c][spatial] += [[ time , val[spatial] ]]

        for x in DFV.keys():
            subs = list(DFV[x]["data"].keys())
            if plot_sub == []:
                subs_to_plot = subs
            else:
                subs_to_plot = plot_sub
            for sub_c in [ x for x in subs_to_plot if x in subs ]:
                data = [ DFV[x]["data"][sub_c][spatial] for spatial in DFV[x]["data"][sub_c].keys() ]
                if not subplots:
                    for i, spatial in enumerate(data):
                        TX.m_plotter.plot_data(
                            data=spatial,
                            msg=f"[ V ][ {x} ][ SUB: {sub_c} ]",
                            label=f"spatial stream: {i}",
                            plot=show_plots and (i == len(data)-1),
                            scatter=False,
                            subplots=subplots,
                            save_file=os.path.join(save_file.parents[0], save_file.stem + f"_{x}_{str(sub_c)}" + save_file.suffix) if save_file and not show_plots else None
                        )
                else:
                    TX.m_plotter.plot_data(
                        data=data,
                        msg=f"[ V ][ {x} ][ SUB: {sub_c} ]",
                        label=[f"spatial stream: {spatial}" for spatial in DFV[x]["data"][sub_c].keys() ],
                        plot=show_plots,
                        scatter=False,
                        subplots=subplots,
                        save_file=os.path.join(save_file.parents[0], save_file.stem + f"_{x}_{str(sub_c)}" + save_file.suffix) if save_file and not show_plots else None
                    )

        # reset DF
        for x in DFV.keys():
            DFV[x]["data"] = {}

def main():
    unittest.main()
if __name__ == '__main__':

    main()