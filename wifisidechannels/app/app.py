import wifisidechannels.units as units
import wifisidechannels.components.packet_processor as packet_processor
import wifisidechannels.components.extractor as extractor
import wifisidechannels.models.models as models
import wifisidechannels.tests.test as test

import argparse, os, pathlib
import datetime


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
    default=None,
    required=False,
    nargs="?",
    help="Files to read from.")
parser.add_argument(
    "--write",
    "-w",
    default=False,
    required=False,
    action="store_true",
    help="Write output to disk. Including:")
parser.add_argument(
    "--data-store-dir",
    "-dsd",
    required=False,
    default="DUMP0",
    nargs="?",
    help="Output directory. (ONLY PATHS RELATIVE TO CWD or PATHS CONTAINING CWD)")
parser.add_argument(
    "--write_file",
    "-wf",
    required=False,
    nargs="?",
    help="File to write to if writing. Filename used as Substring.")
parser.add_argument(
    "--eavesdrop",
    "-E",
    required=False,
    action="store_true",
    help="Use NIC to record packets (and parse them by preset).")
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
    type=int,
    default=60,
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
    "--plot_angles",
    "-pa",
    required=False,
    action="store_true",
    help="Plot quantized angles in CBR.")
parser.add_argument(
    "--plot_v",
    "-pv",
    required=False,
    action="store_true",
    help="Plot Feedbackmatrix.")
parser.add_argument(
    "--plot-per-sub",
    "-pps",
    required=False,
    action="store_true",
    help="Plot each subplot individually.")
parser.add_argument(
    "--show-plots",
    "-sp",
    required=False,
    action="store_true",
    help="Show plots. ( Usefull if writing to file & and plotting.)")
parser.add_argument(
    "--verbose",
    "-v",
    required=False,
    action="store_true",
    help="verbose output."
)

def main():
    args = parser.parse_args()

    CWD = pathlib.Path(os.getcwd())
    OUTPUT_DIR = pathlib.Path(os.path.join(CWD), args.data_store_dir)
    OUT_FILE_DEFAULT = pathlib.Path(
        os.path.join(OUTPUT_DIR, f'{datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")}')
        )

    write_file = args.write_file

    if (write_file or args.write):
        os.makedirs(OUTPUT_DIR, mode=0o777, exist_ok=True)
        if args.eavesdrop:
            os.chown(OUTPUT_DIR, uid=os.geteuid(),gid=os.getegid())
        os.chmod(OUTPUT_DIR, mode=0o777)

    if write_file:
        if args.data_store_dir:
            write_file = pathlib.Path(os.path.join(OUTPUT_DIR, write_file))
        else:
            write_file = pathlib.Path(write_file)

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
                                "write_file" : str(pathlib.Path(os.path.join(write_file.parents[0],write_file.stem + "_capture.pcapng")).relative_to(CWD)) if write_file and write_file.is_absolute() \
                                                    else str(pathlib.Path(os.path.join(write_file.parents[0],write_file.stem + "_capture.pcapng"))) if write_file \
                                                        else str(pathlib.Path(OUT_FILE_DEFAULT.parents[0],OUT_FILE_DEFAULT.stem + "_capture.pcapng").relative_to(CWD))
                            } if args.write else {}
                        ) |
                        (
                            {
                                "mac_sa" : args.mac_sa
                            } if args.mac_sa else {}
                        ) |
                        (
                            {
                                "mac_da" : args.mac_da
                            } if args.mac_da else {}
                        )
                    }
                )
            )
        )

    elif args.read:
        WFI.process_capture(
            kwargs=
                        {
                            "read_file": "'" + args.read + "'"
                        } | (
                            {
                                "timeout" : args.timeout
                            } if args.timeout else {}
                        ) | (
                            {
                                "mac_sa" : args.mac_sa
                            } if args.mac_sa else {}
                        ) | (
                            {
                                "mac_da" : args.mac_da
                            } if args.mac_da else {}
                        ) 
        )

    if args.plot_angles:
        pac = test.TestStuff.test_qunatized_CBR_extract(
            file = args.read if args.read else "../DUMP/0txbf.pcapng",
            mac_sa = args.mac_sa if args.mac_sa else None,
            mac_da = args.mac_da if args.mac_da else None,
            packets = WFI.m_data if WFI.m_data else None,
            v = args.verbose if args.verbose else False,
            timeout= args.timeout if args.timeout else 60,
            vv = args.verbose if args.verbose else False,
            save_file = pathlib.Path(os.path.join(write_file.parents[0], write_file.stem + "_data_angles.dat")) if write_file \
                            else pathlib.Path(os.path.join( OUT_FILE_DEFAULT.parents[0], OUT_FILE_DEFAULT.stem + "_data_angles.dat")).relative_to(CWD) if args.write \
                                else None
            )
        try:
            test.TestStuff.test_angle_plot(
                packets=pac,
                plot_sub=args.plot_per_sub,
                v=args.verbose,
                save_file = pathlib.Path(os.path.join(write_file.parents[0], write_file.stem + "_graph_angles.png")).relative_to(CWD) if write_file and write_file.is_absolute() \
                                else pathlib.Path(os.path.join(write_file.parents[0], write_file.stem + "_graph_angles.png")) if write_file \
                                    else pathlib.Path(os.path.join( OUT_FILE_DEFAULT.parents[0], OUT_FILE_DEFAULT.stem + "_graph_angles.png")).relative_to(CWD) if args.write \
                                        else None,
                show_plots = args.show_plots if write_file or args.write else True
            )
        except KeyboardInterrupt:
            pass
    if args.plot_v:
        pac = test.TestStuff.test_V_extract(
            file = args.read if args.read else "../DUMP/0txbf.pcapng",
            mac_sa = args.mac_sa if args.mac_sa else None,
            mac_da = args.mac_da if args.mac_da else None,
            packets = WFI.m_data if WFI.m_data else None,
            timeout= args.timeout if args.timeout else 60,
            v = args.verbose if args.verbose else False,
            save_file = pathlib.Path(os.path.join(write_file.parents[0], write_file.stem + "_data.dat")).relative_to(CWD) if write_file and write_file.is_absolute() \
                            else pathlib.Path(os.path.join(write_file.parents[0], write_file.stem + "_data.dat")) if write_file \
                                else pathlib.Path(os.path.join( OUT_FILE_DEFAULT.parents[0], OUT_FILE_DEFAULT.stem + "_data.dat")).relative_to(CWD) if args.write \
                                    else None
        )
        try:
            test.TestStuff.test_V_plot(
                packets=pac,
                plot_sub=args.plot_per_sub,
                v=args.verbose,
                save_file = pathlib.Path(os.path.join(write_file.parents[0], write_file.stem + "_graph_V.png")).relative_to(CWD) if write_file and write_file.is_absolute() \
                                else pathlib.Path(os.path.join(write_file.parents[0], write_file.stem + "_graph_V.png")) if write_file \
                                    else pathlib.Path(os.path.join( OUT_FILE_DEFAULT.parents[0], OUT_FILE_DEFAULT.stem + "_graph_V.png")).relative_to(CWD) if args.write \
                                        else None,
                show_plots = args.show_plots if write_file or args.write else True
            )
        except KeyboardInterrupt:
            pass
        return


if __name__ == '__main__':

    """
    TODO: parser via cli
    TODO: create parser from tshark filter fields
    TODO: filter_fields should be splitted args via cli
    TODO: record via cli for time with storage possebility
    TODO: live capture + extraction test
    TODO: get live data
    TODO: use other client sending UDPs trough AP to generate trafic
    TODO: 
    """
    main()
