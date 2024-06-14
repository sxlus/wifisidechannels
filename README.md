# 802.11 Sidechannel implementations

## Usage of the app so far

```bash
usage: wifisidechannels.py [-h] [--interface [INTERFACE ...]] [--read [READ]] [--write]
                           [--write_file [WRITE_FILE]] [--eavesdrop]
                           [--filter_fields [FILTER_FIELDS]] [--channel [CHANNEL]]
                           [--frequency [FREQUENCY]] [--timeout [TIMEOUT]]
                           [--name [NAME]] [--test] [--mac_sa [MAC_SA]]
                           [--mac_da [MAC_DA]] [--plot_angles] [--plot_v]
                           [--plot-per-sub] [--show-plots] [--verbose]

options:
  -h, --help            show this help message and exit
  --interface [INTERFACE ...], -i [INTERFACE ...]
                        Interfaces to use.
  --read [READ], -r [READ]
                        Files to read from.
  --write, -w           Write output to disk. Including:
  --write_file [WRITE_FILE], -wf [WRITE_FILE]
                        File to write to if writing. Filename used as Substring. ( ONLY RELATIVE PATH'S or PATH'S
                        CONTAINING CWD)
  --eavesdrop, -E       Use NIC to record packets (and parse them by preset).
  --filter_fields [FILTER_FIELDS], -F [FILTER_FIELDS]
                        String that instructs tshark to apply filter and display
                        certain fields on call to _listen
  --channel [CHANNEL], -c [CHANNEL]
                        Set NIC to specific channel.
  --frequency [FREQUENCY], -f [FREQUENCY]
                        Set NIC to specific frequency.
  --timeout [TIMEOUT], -t [TIMEOUT]
                        Controls how long subprocesses are executed and timeout for
                        queue access.
  --name [NAME], -n [NAME]
                        Name of packets.
  --test                Test Stuff.
  --mac_sa [MAC_SA], -MS [MAC_SA]
                        MAC SOURCE to filter for.
  --mac_da [MAC_DA], -MD [MAC_DA]
                        MAC DESTINATION to filter for.
  --plot_angles, -pa    Plot quantized angles in CBR.
  --plot_v, -pv         Plot Feedbackmatrix.
  --plot-per-sub, -pps  Plot each subplot individually.
  --show-plots, -sp     Show plots. ( Usefull if writing to file & and plotting.)
  --verbose, -v         verbose output.

```

## Installation

It is important to use `pipx` when installing `poetry` to match the intended version of that project.

1) Install `pipx` to install python `poetry` and install `tshark`, `iw` to capture packets and alternate the state if interfaces

    ```bash
    sudo apt install pipx tshark iw && pipx install poetry && pipx ensurepath
    ```

2) Open a new terminal
3) Install the virtual environment with poetry.

    ```bash
    poetry install
    ```

4) Build modified part of `wipicap` - Cython parts,to recover `V`.

    ```bash
      cd wifisidechannels/components/wipicap/ && poetry run python setup.py build_ext --inplace && cd ../../../../
    ```

### Troubeshoot Installation

#### Installing `virtual environment` for Capturing in monitor Mode
  
  The Framework will modify system devices to enable monitor mode, set channel and frequency on interfaces provided. For that it should be run with sufficient perminssions.
  Installation under `root` seems fiddlely. Needs investigation.

## Usage

- Read `DUMP/noack_places.pcapng` & filter for `Action NoAck` from `MAC` source addres & reconstruct `V` & plot the mean over all subs ( in all metricies ).

```bash
  python wifisidechannels/app/app.py -r DUMP/AP_to_Phone_default_mac_sa_127c6136fcc2_capture.pcapng --mac_sa "d83adde5662c" -pv
```

- Read `DUMP/noack_places.pcapng` & filter for `Action NoAck` to `MAC` destination address & reconstruct `V` & plot each sub seperately

```bash
  python wifisidechannels/app/app.py -r DUMP/AP_to_Phone_default_mac_sa_127c6136fcc2_capture.pcapng --mac_da "d83adde5662c" -pv -pps
```

- Read `DUMP/noack_places.pcapng` & filter for `Action NoAck` from `MAC` source address & parse `CBR` & plot the mean over all subs and angles ( in all metricies ).

```bash
  python wifisidechannels/app/app.py -r DUMP/AP_to_Phone_default_mac_sa_127c6136fcc2_capture.pcapng --mac_sa "127c6136fcc2" -pa 
```

- Read `DUMP/noack_places.pcapng` for max. `60` seconds & filter for `Action NoAck` from `MAC` source address & reconstruct `V` & plot each sub seperately and write `-w` them to `DUMP0/default`

```bash
  python wifisidechannels/app/app.py -r DUMP/AP_to_Phone_default_mac_sa_127c6136fcc2_capture.pcapng -pv -t 60 -w --mac_sa "127c6136fcc2" -dsd DUMP0/default/
```

- `Enable Monitor`, set `channel` and capture trafic on `wlx00c0caaba724` for `60 seconds` & filter `Action NoAck` and recover `V` from `CBR` & plot each sub seperately & `save` output in directory `DUMP0` (default)

```bash
  python wifisidechannels/app/app.py -E -i "d83adde5662c" -c 64 -t 60 -pv -pps -w
```

- `Enable Monitor`, set `channel` and capture trafic on `wlx00c0caaba724` for `60 seconds` & filter `Action NoAck` and recover `V` from `CBR` & plot mean over all subs & `save` output to fixed substring filename `text` in directory `DUMP1`

```bash
  python wifisidechannels/app/app.py -E -i "d83adde5662c" -c 64 -t 60 -pv -pps -w -wf "test" -dsd `DUMP1`
```

### Troubeshoot Usage

#### Capturing `-E` and writing `-w`/`-wf` - `Permission denied` in subProc sdterr

  It is important that the `-wf` argument is relative path to the current working directory as for now pyshark does not accept absolute paths for outputfiles.
  Further it is important that the `user executing the framework OWNS the output directory`.

____

## Look into bash/setup_device.sh

- some hints about tsgark interface
- could be replaced at least partially by pyshark

## Status Log

- **10.05.24**
  - used `WiPiCap` for calculation of V
  - adjusted the interface and signature
  - extracted and calculated all required data
  - need for way to capture targeted with storage system to aquire live data
  - use UDP trafic from axiliary client to target to increase CBR rate
  - find a way to compile pyx code in a manny that is useable

- **11.05.24**
  AP MAC:     10:7c:61:36:fc:c2
  Phone MAC:  60:3a:af:1b:08:93

