import wifisidechannels.units.wifi as wifi
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
    action="store",
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
    nargs="?", help="Controls how long subprocesses are executed and timeout for queue access.")

if __name__ == '__main__':

    """
    TODO: parser via cli
    TODO: create parser from tshark filter fields
    TODO: filter_fields should be splitted args via cli
    """
    args = parser.parse_args()


    WFI = wifi.WiFi(
        (
            {
            "interface"   : "wlan0" if not args.interface else args.interface,
            }
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
            "name" : args.name
            } if args.name else {}
        )
    )

    if args.eavesdrop:
        WFI.eavesdrop(
            (
                {
                    "timeout" : args.timeout
                } if args.timeout else {}
            ) | 
            (
                {
                    "filter_fields" : args.filter_fields
                } if args.filter_fields else {}
            )
        )

    elif args.read:
        WFI.process_capture(kwargs={
            "read_file": "'" + args.read + "'"
        })