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
    help="Plot Feedbackmatrix timeseries per subcarrier x spatial streams.")
parser.add_argument(
    "--plot_v_spec",
    "-pvspec",
    required=False,
    action="store_true",
    help="Plot Feedbackmatrix timeseries as spectogram.")
parser.add_argument(
    "--plot-bandwidth",
    "-pb",
    required=False,
    nargs="*",
    default=None,
    help="Plot for selection of bandwidths. ( usefull for spectogram )")
parser.add_argument(
    "--plot_v_sample",
    "-pvs",
    required=False,
    action="store_true",
    help="Plot Feedbackmatrices per spatial stream of single samples.")

parser.add_argument(
    "--plot-sub",
    "-ps",
    required=False,
    nargs="*",
    default=None,
    help="Plot for selection of subcarriers or samples or spatial streams (indexed from zero).")
parser.add_argument(
    "--subplots",
    required=False,
    action="store_true",
    default=False,
    help="Plot spatial streams in individual subplots.")
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
    OUTPUT_DIR = pathlib.Path(os.path.join(CWD, args.data_store_dir))
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
        write_file = pathlib.Path(os.path.join(OUTPUT_DIR, write_file)).relative_to(CWD)
    else:
        if args.write:
            if args.read:
                read_file = pathlib.Path(args.read)
                write_file = pathlib.Path(os.path.join(OUTPUT_DIR, read_file.stem.replace("_capture", ""))).relative_to(CWD)
            elif args.eavesdrop:
                write_file = OUT_FILE_DEFAULT.relative_to(CWD)

    WFI = units.txbf.TxBf(**(
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
                                "write_file" :  str(pathlib.Path(os.path.join(write_file.parents[0],write_file.stem + "_capture.pcapng")))
                            } if args.write or args.write_file else {}
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
            save_file = pathlib.Path(os.path.join(write_file.parents[0], write_file.stem + "_data_angles.dat")) if write_file else None,
            )
        try:
            test.TestStuff.test_angle_plot(
                packets=pac,
                plot_sub=[ int(x, 10) for x in args.plot_sub ] if args.plot_sub is not None else [],
                v=args.verbose,
                save_file = pathlib.Path(os.path.join(write_file.parents[0], write_file.stem + "_graph_qangles_sum.png")) if write_file else None,
                show_plots = args.show_plots if (write_file or args.write) else True
            )
        except KeyboardInterrupt:
            pass

    if args.plot_v or args.plot_v_spec or args.plot_v_sample:
        pac = test.TestStuff.test_V_extract(
            file = args.read if args.read else "../DUMP/0txbf.pcapng",
            mac_sa = args.mac_sa if args.mac_sa else None,
            mac_da = args.mac_da if args.mac_da else None,
            packets = WFI.m_data if WFI.m_data else None,
            timeout= args.timeout if args.timeout else 60,
            v = args.verbose if args.verbose else False,
            bandwidth = [ int(x, 10) for x in args.plot_bandwidth ] if args.plot_bandwidth else None,
            save_file = pathlib.Path(os.path.join(write_file.parents[0], write_file.stem + ((f"_bw_{'-'.join([str(y) for y in args.plot_bandwidth])}" if args.plot_bandwidth else "")) + "_data.dat")) if write_file else None,
        )

    if args.plot_v_spec:
        try:
            WFI.plot_feedback_hist(
                packets=pac,
                save_file=pathlib.Path(os.path.join(write_file.parents[0], write_file.stem + ((f"_bw_{'-'.join([str(y) for y in args.plot_bandwidth])}" if args.plot_bandwidth else "")) + ((f"_st_{'-'.join([str(y) for y in args.plot_sub])}" if args.plot_sub else "")) + "_spectogram.png")) if write_file else None,
                dpi= 200,
                size= (10,5),
                plot=args.show_plots if write_file or args.write else True,
                v=args.verbose if args.verbose else False,
                bandwidth = [ int(x, 10) for x in args.plot_bandwidth ] if args.plot_bandwidth is not None else None,
                plot_spatial=[ int(x, 10) for x in args.plot_sub ] if args.plot_sub is not None else None,
                window_title=f"Spectorgram of Sample {str(write_file)}" + (f" @ bandwidth {''.join(args.plot_bandwidth)}" if args.plot_bandwidth else "")
            )
        except KeyboardInterrupt:
            pass

    if args.plot_v_sample:
        try:
            for i in [ val for x in args.plot_sub if (val:= int(x, 10) < len(pac)) ] if args.plot_sub is not None else range(len(pac)):
                WFI.plot_feedback_packet(
                    packet=pac[i],
                    save_file=pathlib.Path(os.path.join(write_file.parents[0], write_file.stem + ((f"_bw_{'-'.join([str(y) for y in args.plot_bandwidth])}" if args.plot_bandwidth else "")) + f"_sample_{i}.png")) if write_file else None,
                    dpi= 200,
                    size= (10,5),
                    plot=args.show_plots if write_file or args.write else True,
                    v=args.verbose if args.verbose else False,
                    window_title=f"[ Packet {i} ]"
                )
        except KeyboardInterrupt:
            pass

    if args.plot_v:
        try:
            test.TestStuff.test_V_plot(
                packets=pac,
                plot_sub=[ int(x, 10) for x in args.plot_sub ] if args.plot_sub is not None else [],
                v=args.verbose,
                save_file = pathlib.Path(os.path.join(write_file.parents[0], write_file.stem + ((f"_bw_{'-'.join([str(y) for y in args.plot_bandwidth])}" if args.plot_bandwidth else "")) + "_graph_V.png")) if write_file else None,
                show_plots = args.show_plots if write_file or args.write else True,
                subplots = args.subplots
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
