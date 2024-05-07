import wifisidechannels.units as units
import wifisidechannels.components.packet_processor as packet_processor
import wifisidechannels.components.extractor as extractor
import wifisidechannels.models.models as models

import argparse, os

parser = argparse.ArgumentParser(
                    prog='wifisidechannels.py')

parser.add_argument(
    "--interface",
    "-i",
    default="wlan0",
    required=False,
    nargs="*",
    help="Interfaces to use.")
parser.add_argument(
    "--read",
    "-r",
    default=os.path.join(os.getcwd(), "DUMP", "0txbf.pcapng"),
    required=False,
    nargs="?",
    help="Files to read from. (current just one)")
parser.add_argument(
    "--eavesdrop",
    "-E",
    required=False,
    action="store_true",
    help="Use NIC to record packets (and parse them by preset). default")
parser.add_argument(
    "--filter_fields",
    "-F",
    required=False,
    nargs="?",
    help="String that instructs tshark to apply filter and display certain fields on call to _listen\n")
parser.add_argument(
    "--channel",
    "-c",
    required=False,
    type=int,
    nargs="?",
    help="Set NIC to specific channel.")
parser.add_argument(
    "--frequency",
    "-f",
    required=False,
    type=int,
    nargs="?",
    help="Set NIC to specific frequency.")
parser.add_argument(
    "--timeout",
    "-t",
    required=False,
    nargs="?",
    help="Controls how long subprocesses are executed and timeout for queue access.")
parser.add_argument(
    "--name",
    "-n",
    required=False,
    nargs="?",
    help="Name of packets.")
parser.add_argument(
    "--test",
    required=False,
    action="store_true",
    help="Test Stuff.")

def main():
    args = parser.parse_args()
    if args.test:
        TX = units.txbf.TxBf()
        pac = TX.process_capture(kwargs={
            "read_file" : os.path.join("DUMP", "0txbf.pcapng")
        })

        ext_c = extractor.VHT_MIMO_CONTROL_Extractor()
        processor   = packet_processor.PacketProcessor()
        new_pac = processor.parse(todo=pac, extract=ext_c)

        field = models.VHT_COMPRESSED_BEAMFORMINGREPORT(**{
                    "packet" : new_pac[22]
                }
        )
        ext_r = extractor.VHT_BEAMFORMING_REPORT_Extractor(**(
            {
                "FIELD" : field
            }
        ))

        for p in new_pac:
            #print(str(pac.DATA.get(models.TsharkField.VHT_MIMO_CONTROL_CONTROL.value)))
            #print(str(pac.DATA.get(models.TsharkField.VHT_COMPRESSED_BEAMFORMINGREPORT.value)))
            #print(field)
            processor.parse(todo=p, extract=ext_r)
        #dic = ext_r.apply(pac)
        #for x in dic.keys():
        #    print(str(dic[x]))

        #print(new_pac[0].DATA.get(models.TsharkField.VHT_COMPRESSED_BEAMFORMINGREPORT.value))

        for p in new_pac:
            print(str(p.DATA))

    WFI = units.wifi.WiFi(**(
            {
                "interface"   : "wlan0" if not args.interface else args.interface,
            } |
            (
                {
                    "channel" : args.channel
                } if args.channel else {}
            ) |
            (
                {
                    "frequency" : args.frequency
                } if args.frequency else {}
            ) |
            (
                {
                    "name" : args.name
                } if args.name else {}
            )
        )
    )

    if args.eavesdrop:
        WFI.eavesdrop(**(
                (
                    {
                        "timeout" : args.timeout
                    } if args.timeout else {}
                ) | 
                (
                    {
                        "kwargs": {} | (
                            {
                                "filter_fields" : args.filter_fields
                            } if args.filter_fields else {}
                        ) |
                        (
                            {
                                "channel" : args.channel
                            } if args.channel else {}
                        ) |
                        (
                            {
                                "frequency" : args.frequency
                            } if args.frequency else {}
                        )
                    }
                )
            )
        )

    elif args.read:
        WFI.process_capture(kwargs={
            "read_file": "'" + args.read + "'"
        })
if __name__ == '__main__':

    """
    TODO: parser via cli
    TODO: create parser from tshark filter fields
    TODO: filter_fields should be splitted args via cli
    """
    main()
