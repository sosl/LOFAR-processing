#!/usr/bin/python

import socket
import time, calendar
from optparse import OptionParser
import os
import subprocess as sb
import sys

class flushfile(object):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()

parser = OptionParser();
    
parser.add_option("-P", "--psr", "--pulsar", dest="Pulsar",
                  help="Name of the pulsar to be observed")
parser.add_option("-T","--tint", dest="TInt",
                  help="Integration time in minutes (default: 5.0)")
parser.add_option("-S","--starttime", dest="StartTime",
                  help="Time when to start the observation. "
                  "(For LuMP: String in format yyyy-mm-ddThh:mm:ssZ) "
                  "(default: start \"now\")")
parser.add_option("-W","--wait", dest="Wait",
                  help="Maximum wait time after observation is supposed "
                  "to be finished in minutes (default: 3.0)")
parser.add_option("-v", "--verbose", dest="Verbose", action="store_true",
                  help="Verbose (more detailed output)")

(options, args) = parser.parse_args()

if options.Verbose:
    sys.stdout = flushfile(sys.stdout)
 
if not options.Pulsar:
    print "Need pulsar name! Use \"-h\" for help."
    exit(1)
Pulsar = options.Pulsar

inttime = 5.
if options.TInt:
    inttime = float(options.TInt)

endwait = 3.
if options.Wait:
    endwait = float(options.Wait)

#get the Python-style time-tuple for 2 min from now and in UTC
timesoon = time.gmtime(calendar.timegm(time.gmtime())+120)
starttime = time.strftime("%Y-%m-%dT%H:%M:00Z",timesoon)

if options.StartTime:
    starttime = options.StartTime


sleeptime = 30.

# Kill any remaining pointings first.
lcucommand = "ssh glow602 ssh de602c killpointing"
lcuproc = os.popen( lcucommand )
if options.Verbose:
    print "Killing existing pointings with:"
    print " - ", lcucommand
lcuproc = False

# start beams on the LCU
lcucommand = "ssh glow602 ssh de602c /data/home/user9/LCU-scripts/PSR_8bit_Scripts/observe.csh psr " + Pulsar
if options.Verbose:
    print "Starting beams on the LCU with:"
    print " - ", lcucommand
lcuproc = os.popen(lcucommand)

# Use LuMP
print "Using LuMP"
data_dir=time.strftime("%Y-%m-%d-%H:%M",timesoon)
lofar1command = "ssh lofarC3 '~/PSR_8bit_Scripts/RunLuMP_universal.sh " + Pulsar + " " + str(inttime)  + " " + data_dir
lofar1command += " " + starttime + " DE602 1 1"
# the last thre arguments there are: station lane verbosity
lofar1command += " >> ~/PSR_Logs/LuMP_"+data_dir+"_"+Pulsar+"_lane1.log 2>&1' "

lofar2command = "ssh lofarC3 '~/PSR_8bit_Scripts/RunLuMP_universal.sh " + Pulsar + "  " + str(inttime)  + " " + data_dir
lofar2command += " " + starttime + " DE602 2 1"
lofar2command += " >> ~/PSR_Logs/LuMP_"+data_dir+"_"+Pulsar+"_lane2.log 2>&1' "

lofar3command = "ssh lofarC4 '~/PSR_8bit_Scripts/RunLuMP_universal.sh " + Pulsar + " " + str(inttime)  + " " + data_dir
lofar3command += " " + starttime + " DE602 3 1"
lofar3command += " >> ~/PSR_Logs/LuMP_"+data_dir+"_"+Pulsar+"_lane3.log 2>&1' "

lofar4command = "ssh lofarC4 '~/PSR_8bit_Scripts/RunLuMP_universal.sh " + Pulsar + " " + str(inttime)  + " " + data_dir
lofar4command += " " + starttime + " DE602 4 1"
lofar4command += " >> ~/PSR_Logs/LuMP_"+data_dir+"_"+Pulsar+"_lane4.log 2>&1' "


if options.Verbose:
    print "Starting dumps on lofarN with:"
    print lofar1command
    print lofar2command
    print lofar3command
    print lofar4command

time.sleep(30)

#lofar1proc = os.popen(lofar1command)
#lofar2proc = os.popen(lofar2command)
#lofar3proc = os.popen(lofar3command)
#lofar4proc = os.popen(lofar4command)
lofar1proc = sb.Popen(lofar1command,shell=True,stdin=sb.PIPE, stdout=sb.PIPE, stderr=sb.PIPE, close_fds=True)
lofar2proc = sb.Popen(lofar2command,shell=True,stdin=sb.PIPE, stdout=sb.PIPE, stderr=sb.PIPE, close_fds=True)
lofar3proc = sb.Popen(lofar3command,shell=True,stdin=sb.PIPE, stdout=sb.PIPE, stderr=sb.PIPE, close_fds=True)
lofar4proc = sb.Popen(lofar4command,shell=True,stdin=sb.PIPE, stdout=sb.PIPE, stderr=sb.PIPE, close_fds=True)

waitminutes = inttime+1.
print "Waiting "+str(waitminutes)+" min for the observation to finish"
time.sleep(waitminutes*60.) #wait till udpdump starts

def done(p):
    return p.poll() is not None

nsleeps = int((endwait*60)/sleeptime)

for n in range(nsleeps):
    if done(lofar1proc) and done(lofar2proc) and done(lofar3proc) and done(lofar4proc):
        break
    if options.Verbose:
        print "Apparently not finished yet, waiting "+str(sleeptime)+" seconds."        
    time.sleep(sleeptime)

if not done(lofar1proc):
    if options.Verbose:
        print "Process for lofar1 still running, killing it softly."
    lofar1proc.terminate()
if not done(lofar2proc):
    if options.Verbose:
        print "Process for lofar2 still running, killing it softly."
    lofar2proc.terminate()
if not done(lofar3proc):
    if options.Verbose:
        print "Process for lofar3 still running, killing it softly."
    lofar3proc.terminate()
if not done(lofar4proc):
    if options.Verbose:
        print "Process for lofar4 still running, killing it softly."
    lofar4proc.terminate()

#Give processes a chance to terminate gracefully
time.sleep(1)

if not done(lofar1proc):
    if options.Verbose:
        print "Process for lofar1 still running, killing it!"
    lofar1proc.kill()
if not done(lofar2proc):
    if options.Verbose:
        print "Process for lofar2 still running, killing it!"
    lofar2proc.kill()
if not done(lofar3proc):
    if options.Verbose:
        print "Process for lofar3 still running, killing it!"
    lofar3proc.kill()
if not done(lofar4proc):
    if options.Verbose:
        print "Process for lofar4 still running, killing it!"
    lofar4proc.kill()

print "stopping beams:"
lcucommand = "ssh glow602 ssh de602c killpointing " # + Pulsar
lcuproc = os.popen(lcucommand)
