#!/bin/bash

## Read Action No ACK Frames from file:
# file="/home/sxlus/802.11_sidechannels/DUMP/0txbf.pcapng";dmac="f0:2f:74:0a:fb:ec"; 
## ./bash/setup_device.sh -r $file -F "(wlan.da==$dmac)&&(wlan.fc.type_subtype == 0x0e)" -E "frame.time,wlan.ta,wlan.da,wlan.vht.mimo_control.control,wlan.vht.compressed_beamforming_report"

Help()
{
    echo "[ + ] enable/disable monitor mode on NIC"
    echo "[ + ] set NIC to specific channel/frequency"
    echo "[ + ] start capture on NIC and apply tshark capturefilters"
    echo 
    echo "Syntax:"
    echo "  <prog> [-e/-d] [-c/-f] [-n]"
    echo "  <prog> [-l] [-E/-F] [-w] [-n]"
    echo 
    echo "options:"
    echo "      n                   NIC device name."
    echo "      e                   Enable monitor mode."
    echo "      d                   Disable monitor mode."
    echo "      c                   Channel for NIC to operate on."
    echo "      f                   Frequency (GHz) for NIC to operate on."
    echo "      l                   Listen."
    echo "      w                   write dump to .pcapng file"
    echo "      r                   read dump from .pcapng file"
    echo "      F                   (Display/Capture) Filter for tshark."
    echo "      E                   Display Fields. ','-seperated list."
    echo "      v                   Verbose output."
    echo 
    echo "Example:"
    echo "  <prog> -e -c 109 -n wlan0"
    echo "  <prog> -l -w out_file -n wlan0"
    exit
}

if [ "$1" = "-h" ]  || [ "$1" = "--help" ]; then
    Help
fi

# EXTERNAL
device=""
enable=0
disable=0
channel=0
frequency=0
listen=0
FILTER=""
FIELDS=""
output=""
read=""
v=0

# INTERNAL
check=""

# default options
#   -l      flush stdout after each packet
#   
command="tshark -l"

# GET OPTIONS

while getopts 'n:edc:f:ls:E:F:w:r:v' OPT;
do
    case "$OPT" in
        n)  device=${OPTARG};;
        e)  enable=1;;
        d)  disable=1;;
        c)  channel=${OPTARG};;
        f)  frequency=${OPTARG};;
        l)  listen=1;;
        w)  output="\"${OPTARG}\"";; 
        r)  read="\"${OPTARG}\"";;
        E)  FIELDS=${OPTARG};;
        F)  FILTER=${OPTARG};;
        v)  v=1;;
        \?) echo "Invalid option!"; Help;;
    esac
done

if [[ $v -eq 1 ]]; then
    echo
    [[ $device ]]           && echo "Using device $device.";
    [[ $enable -eq 1 ]]     && echo "Enable Monitor Mode.";
    [[ $disable -eq 1 ]]    && echo "Disable Monitor Mode.";
    [[ $channel -ne 0 ]]    && echo "Setting channel to $channel.";
    [[ $frequency -ne 0 ]]  && echo "Setting frequency to $frequency GHz.";
    [[ $listen -eq 1 ]]     && echo "Start listening.";
    [[ $output ]]           && echo "Writing to $output.";
    [[ $read ]]             && echo "Reading from $read."; 
    [[ $FIELDS ]]           && echo "Will display $FIELDS fields.";
    [[ $FILTER ]]           && echo "Applying Filter $FILTER to tshark.";
    [[ $v -eq 1 ]]          && echo "Verbose.";
fi 

# CHECK FOR DEVICE
if [ -z "$device" ] && ( [ -z "$read" ] || [ $listen -eq 1 ] ); then
    echo "Please specify device ( -n ) or file to read from ( -r ) without ( -l )";
    Help
fi

# DO STUFF

if [ $enable -eq 1 ]; then
    [ $v -eq 1 ] && echo "Monitor"
    ip link set $device down
    iw dev $device set type monitor
    ip link set $device up
fi

if [ $disable -eq 1 ]; then
    [ $v -eq 1 ] && echo "Station"
    ip link set $device down
    iw dev $device set type station
    ip link set $device up
fi

if [ $channel -ne 0 ]; then
    [ $v -eq 1 ] && echo "Channel"
    # Test if possible
    check=$(iwlist $device channel | grep -E " Channel [0]?${channel} ")
    if [[ "$check" == "" ]]; then
        echo "Cant set $device to channel $channel."
        iwlist $device channel | grep -E " Channel" | sed 's/^[ \t]*//'
        exit
    fi
    
    #iwconfig $device power off
    iwconfig $device channel $channel
    #iwconfig $device power on
fi

if [ $frequency -ne 0 ]; then
    [ $v -eq 1 ] && echo "Frequency"
    # Test if possible
    check=$(iwlist $device channel | grep -E " $frequency GHz")
    if [[ "$check" == "" ]]; then
        echo "Cant set $device to Frequency $frequency."
        iwlist $device channel | grep -E ": [2,5]\.[0-9]{1,3} GHz" | sed 's/^[ \t]*//'
        exit
    fi
    
    #iwconfig $device power off
    iwconfig $device frequency "${frequency}G"
    #iwconfig $device power on
fi
echo $output
if [ $listen -eq 1 ] || [[ "$read" != "" ]]; then

    [ $v -eq 1 ] && echo "Listen or Read"   
    [ $v -eq 1 ] && echo 
    # select capture "-f" or display filter "-Y"
    # capture filters for listening are desired, but yet not researched
    # I guess they are less 'complete' then display filters 
    # [[ $listen -eq 1 ]] && filter_kind="-f" || filter_kind="-Y";
    [[ $listen -eq 1 ]] && filter_kind="-Y" || filter_kind="-Y";
    # select read file of capture device
    [[ $listen -eq 1 ]] && command="$command -i $device" || command="$command -r $read";
    # apply selected filter
    [[ $FILTER != "" ]] && FILTER="$filter_kind \"$FILTER\""
    command="$command${FILTER:+ $FILTER}" ; 
    # each field shall get its own -e 
    FIELDS=$( echo -n $FIELDS | sed 's/,/ -e /g ' );
    # applay display fields
    [[ $FIELDS != "" ]] && command="$command -T fields -e $FIELDS";
    # apply output to file
    [[ $output != "" ]] && output="-w $output";
    command="$command${output:+ $output}"
    
    [ $v -eq 1 ] && echo "Command: eval ${command}"
    [ $v -eq 1 ] && echo 

    eval $command

fi
