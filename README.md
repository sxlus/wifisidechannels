# 802.11 Sidechannel implementations

## Usage of the app so far

```bash
usage: wifisidechannels.py [-h] [--interface [INTERFACE ...]] [--read [READ]] [--eavesdrop EAVESDROP] [--filter_fields [FILTER_FIELDS]] [--channel [CHANNEL]] [--frequency [FREQUENCY]] [--timeout [TIMEOUT]]

options:
  -h, --help            show this help message and exit
  --interface [INTERFACE ...], -i [INTERFACE ...]
                        Interfaces to use.
  --read [READ], -r [READ]
                        Files to read from. (current just one)
  --eavesdrop EAVESDROP, -E EAVESDROP
                        Use NIC to record packets (and parse them by preset). default
  --filter_fields [FILTER_FIELDS], -F [FILTER_FIELDS]
                        String that instructs tshark to apply filter and display certain fields on call to _listen
  --channel [CHANNEL], -c [CHANNEL]
                        Set NIC to specific channel.
  --frequency [FREQUENCY], -f [FREQUENCY]
                        Set NIC to specific frequency.
  --timeout [TIMEOUT], -t [TIMEOUT]
                        Controls how long subprocesses are executed and timeout for queue access.
```

### some functions that are currently being tested can be executed with `--test` flag

### How to setup? - compile cython & maybe move `wipicap*`.so to `components/wipicap`

```bash
python components/wipicap/setup.py build_ext --inplace
```

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
  - 