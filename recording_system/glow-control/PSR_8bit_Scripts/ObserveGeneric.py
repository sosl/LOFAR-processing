#!/usr/bin/python

import socket
import time, calendar
from argparse import ArgumentParser
import os
import subprocess as sb
import sys

class flushfile(object):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()

parser = ArgumentParser();
    
parser.add_argument("-P", "--psr", "--pulsar", dest="Pulsar",
        help="Name of the pulsar to be observed")
parser.add_argument("-T","--tint", dest="TInt",
        help="Integration time in minutes (default: 5.0)")
parser.add_argument("-S","--starttime", dest="StartTime",
        help="Time when to start the observation. "
        "(For LuMP: String in format yyyy-mm-ddThh:mm:ssZ) "
        "(default: start \"now\")")
parser.add_argument("-W","--wait", dest="Wait",
        help="Maximum wait time after observation is supposed "
        "to be finished in minutes (default: 3.0)")
parser.add_argument("-v", "--verbose", dest="Verbose", action="store_true",
        help="Verbose (more detailed output)")
parser.add_argument("-s", "--station", dest="Station",
        help="Which station to control. Mandatory.")
parser.add_argument("-R", "--recorder", nargs='+', dest="Recorders",
        help="Recording machines to be used, white-space separated."
        " Must be a list of three or four machines to record three "
        " or four lanes. E.g., '-R C1 C2 C2' will record lane 1 to "
        "C1 and lanes 2 and 3 to C2")

args = parser.parse_args()

lanes = 0
if len(args.Recorders) == 3:
    if args.Verbose:
        print "Will record three lanes"
    lanes = 3
elif len(args.Recorders) == 4:
    if args.Verbose:
        print "Will record four lanes"
    lanes = 4
    print "Currently recording four lanes not supported. Need to upgrade the RunLuMP scripts first!"
    exit(1)
else:
    print "You must provide exactly three or four recording machines!"
    exit(1)

if not args.Station:
    print "You must choose a station!"
    exit(1)
else:
    # extract the last three characters of station
    station_id=args.Station[-3:]
    if not station_id == "601" and not station_id == "602" and not station_id == "603" and not station_id == "604" and not station_id == "605" and not station_id == "609":
        print "Station " + args.Station + " with id " + station_id + " is unknown!"
        exit(1)

if args.Verbose:
    sys.stdout = flushfile(sys.stdout)
 
if not args.Pulsar:
    print "Need pulsar name! Use \"-h\" for help."
    exit(1)
Pulsar = args.Pulsar

inttime = 5.
if args.TInt:
    inttime = float(args.TInt)

endwait = 3.
if args.Wait:
    endwait = float(args.Wait)

#get the Python-style time-tuple for 2 min from now and in UTC
timesoon = time.gmtime(calendar.timegm(time.gmtime())+120)
starttime = time.strftime("%Y-%m-%dT%H:%M:00Z",timesoon)

if args.StartTime:
    starttime = args.StartTime


sleeptime = 30.

# Kill any remaining pointings first.
lcucommand = "ssh glow"+station_id+" ssh de"+station_id+"c killpointing"
lcuproc = os.popen( lcucommand )
if args.Verbose:
    print "Killing existing pointings with:"
    print " - ", lcucommand
lcuproc = False

# start beams on the LCU
lcucommand = "ssh glow" + station_id + " ssh de"+station_id + "c /data/home/user9/LCU-scripts/PSR_8bit_Scripts/observe-psr-universal.sh " + Pulsar + " " + str(lanes)
if args.Verbose:
    print "Starting beams on the LCU with:"
    print " - ", lcucommand
lcuproc = os.popen(lcucommand)

# Use LuMP
if args.Verbose:
    print "Using LuMP"
data_dir=time.strftime("%Y-%m-%d-%H:%M",timesoon)
recorder_command = []
for lane in range(0, lanes):
    recorder_command.append("")
    recorder_command[lane] = "ssh lofar" + args.Recorders[lane] + " '~/PSR_8bit_Scripts/RunLuMP_universal_3quarters.sh " + Pulsar + " " + str(inttime)  + " " + data_dir
    recorder_command[lane] += " " + starttime + " DE"+station_id+" 1 1"
    recorder_command[lane] += " >> ~/PSR_Logs/LuMP_"+data_dir+"_"+Pulsar+"_lane1.log 2>&1' "

if args.Verbose:
    print "Starting dumps on lofarN with:"
    for lane in range(0, lanes):
        print recorder_command[lane]

time.sleep(30)

recorder_processes = []
for lane in range(0, lanes):
    recorder_processes.append("")
    recorder_processes[lane] = sb.Popen(recorder_command[lane], shell=True,
            stdin=sb.PIPE, stdout=sb.PIPE, stderr=sb.PIPE, close_fds=True)

waitminutes = inttime+1.
print "Waiting "+str(waitminutes)+" min for the observation to finish"
time.sleep(waitminutes*60.) #wait till udpdump starts

def done(p):
    # poll the return code. If still running, will return None
    return p.poll() is not None

nsleeps = int((endwait*60)/sleeptime)

for n in range(nsleeps):
    if all(done(record_process) for record_process in recorder_processes):
        break
    if args.Verbose:
        print "Apparently not finished yet, waiting "+str(sleeptime)+" seconds."        
    time.sleep(sleeptime)

for lane in range(0, lanes):
    if not done(recorder_processes[lane]):
        if args.Verbose:
            print "Process for lane"+ str(lane) + " still running, killing it softly."
        recorder_processes[lane].terminate()

#Give processes a chance to terminate gracefully
time.sleep(1)

for lane in range(0, lanes):
    if not done(recorder_processes[lane]):
        if args.Verbose:
            print "Process for lane" + str(lane) + " still running, killing it!"
        recorder_processes[lane].kill()

print "stopping beams:"
lcucommand = "ssh glow"+station_id+" ssh de"+station_id+"c killpointing " # + Pulsar
lcuproc = os.popen(lcucommand)
