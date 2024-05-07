# 802.11 Sidechannel implementations

## Going for Transmitbeamforming first

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
