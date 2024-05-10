from wifisidechannels.components.WiPiCap import wipicap
from wifisidechannels.units.wifi import WiFi
from wifisidechannels.components.extractor import VHT_MIMO_CONTROL_Extractor
from wifisidechannels.models import models
pcap_file = '../../../DUMP/0txbf.pcapng'
addr = 'd8:3a:dd:e5:66:2c'

#v_matrix, time_stamp = wipicap.get_v_matrix(packets = [], bw=20)
#
#for p_cnt, out in enumerate(zip(v_matrix, time_stamp)):
#    print(f"[+] Packet: {p_cnt} @ {out[1]}:")
#    for sub_cnt, sub_v in enumerate(out[0]):
#        print(f"\t-> {sub_cnt:0>3} Subcarrier: {str(sub_v)}")

WFI = WiFi(**{
    "set_up" : "../../../bash/setup_device.sh"
})

packets = WFI.process_capture(kwargs={
            "read_file": "'" + pcap_file + "'"
        })

print("done I ")
ext_mimo = VHT_MIMO_CONTROL_Extractor()

for pac in packets:
    #print(pac.DATA.get(models.TsharkField.FRAME_TIME.value))
    pac.DATA |= ext_mimo.apply(packet=pac)
    #print(str(pac))

print("done II")
v_matrix, time_stamp = wipicap.get_v_matrix(packets = packets, bw=20)

#for p_cnt, out in enumerate(zip(v_matrix, time_stamp)):
#    print(f"[+] Packet: {p_cnt} @ {out[1]}:")
#    for sub_cnt, sub_v in enumerate(out[0]):
#        print(f"\t-> {sub_cnt:0>3} Subcarrier: {str(sub_v)}")