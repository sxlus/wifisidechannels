import wifisidechannels.units as units
import wifisidechannels.components.packet_processor as packet_processor
import wifisidechannels.components.extractor as extractor
import wifisidechannels.models.models as models
import wifisidechannels.tests.test as test

import argparse, os, datetime

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
    "--write",
    "-w",
    default=None, #os.path.join(os.getcwd(), "DUMP", f'capture_{datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")}.pcapng'),
    required=False,
    nargs="?",
    help="File to write to if listening.")
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
parser.add_argument(
    "--mac",
    "-M",
    required=False,
    action="store_true",
    help="Test Stuff.")
parser.add_argument(
    "--verbose",
    "-v",
    required=False,
    nargs="?",
    help="MAC to filter for ( currently only supported with --test )")

def main():
    args = parser.parse_args()

    if args.test:
        pac = test.TestStuff.test_qunatized_CBR_extract(
            v = args.verbose if args.verbose else False)
        pac = test.TestStuff.test_V_extract(
            file = args.read if args.read else "../DUMP/0txbf.pcapng",
            v = args.verbose if args.verbose else False
        )
        test.TestStuff.test_V_plot(packets=pac)
        return

    print(os.getcwd())

    WFI = units.wifi.WiFi(**(
            {
                "interface"   : "wlan0" if not args.interface else args.interface[0],
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
    print(WFI.m_interface)
    print(args.interface)
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
                        ) |
                        (
                            {
                                "write_file" : args.write
                            } if args.write else {}
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
    TODO: record via cli for time with storage possebility
    TODO: live capture + extraction test
    TODO: get live data
    TODO: use other client sending UDPs trough AP to generate trafic
    """
    main()
