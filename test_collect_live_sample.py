import wifisidechannels.units.txbf as txbf

import argparse


parser = argparse.ArgumentParser(
                    prog='wifisidechannels.py')

parser.add_argument(
    "--interface",
    "-i",
    default="wlp0s20f3",
    required=False,
    nargs="?",
    help="Interfaces to use.")
parser.add_argument(
    "--channel",
    "-c",
    required=False,
    type=int,
    default=64,
    nargs="?",
    help="Set NIC to specific channel.")
parser.add_argument(
    "--timeout",
    "-t",
    required=False,
    type=int,
    default=60,
    nargs="?",
    help="Controls how long subprocesses are executed and timeout for queue access.")
parser.add_argument(
    "--mac_sa",
    "-MS",
    required=False,
    nargs="?",
    help="MAC SOURCE to filter for.")
parser.add_argument(
    "--mac_da",
    "-MD",
    required=False,
    nargs="?",
    help="MAC DESTINATION to filter for.")
parser.add_argument(
    "--verbose",
    "-v",
    required=False,
    action="store_true",
    help="verbose output."
)

parser.add_argument(
    "--number",
    "-n",
    type=int,
    required=False,
    nargs="?",
    help="Number of packets to collect."
)

if __name__ == "__main__":
    args = parser.parse_args()

    print(args.interface)
    TX = txbf.TxBf(
        **{
            "interface": args.interface,
            "channel": args.channel,
        }
    )
    print(TX.m_interface)
    if not TX.m_interface:
        exit()
    TX.collect_sample(
        timeout=10,
        kwargs={
            "num": 2 if not args.number else args.number,
            "mac_sa": "d8:3a:dd:e5:66:2c" if not args.mac_sa else args.mac_sa,
        }
    )