#!/usr/bin/python

import socket
import time, calendar
from argparse import ArgumentParser
import os
import subprocess as sb
import sys
#for email notifications:
import smtplib
from email.mime.text import MIMEText

class flushfile(object):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()

# poll the return code. If still running, will return False
def done(p):
    return p.poll() is not None

me = "observer@glow-control"
def send_message( subject, text, recipients, smtp ):
    message = MIMEText(text)
    message['Subject']=subject
    message['From'] = me
    message['To'] = recipients[0]
    for i in range (1,len(recipients)):
        message['To'] += "," + recipients[i]
    smtp.sendmail(me, recipients, msg.as_string())


#monitor execution of a command and if it is not finished after a certain time
#undertake an action, either notify the observer, or interrupt the command
#timeout sleepinterval in seconds!
#If process finished successfully return True. Otherwise return False
def monitor_process( p, observers, interrupt, verbose_out, timeout, sleep_interval ):
    #First allow the process to run for some amount of time (timeout) and check every sleep_interval seconds
    iterations = int(timeout/sleep_interval)
    for n in range(iterations):
        if not done(p):
            time.sleep(sleep_interval)
    #If still running, undertake some action:
    if len(observers) > 0:
        title = "[LOFAR-observing] " + args.Station + " problem with a child process"
        body  = "Dear observer,\n\n"
        body += "The observation of " + Pulsar + " with "
        body += args.Station + " is having issues:\n\n"
        body += verbose_out
        body += "\n\nObservation monitoring system"
        send_message( title, body, observers, s)
    if interrupt:
        #kill the process
        p.terminate()
        time.sleep(1)
        #Give processes a chance to terminate gracefully
        if not done(p):
            p.kill()
    if len(verbose_out) > 0:
        print verbose_out
    final_status = p.poll()
    if (type(final_status) == bool):
        return final_status
    elif (type (final_status) == int):
        return final_status == 0
    else:
        return False


parser = ArgumentParser();

s = None
    
parser.add_argument("-P", "--psr", "--pulsar", dest="Pulsar",
        help="Name of the pulsar to be observed")
parser.add_argument("-T","--tint", dest="TInt",
        help="Integration time in minutes (default: 5.0)")
parser.add_argument("--tolerance", dest="Tolerance",
        help="If observation late by these many minutes, print a warning and notify the observer")
parser.add_argument("--hard-tolerance", dest="HardTolerance",
        help="If observation late by these many minutes, shorten the observation")
parser.add_argument("-O", "--observer", nargs='*', dest="Observers",
        help="Email of the observer(s) for observing notifications")
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
subband_offset = None
if len(args.Recorders) == 3:
    if args.Verbose:
        print "Will record three lanes"
    lanes = 3
    subband_offset = 93
elif len(args.Recorders) == 4:
    if args.Verbose:
        print "Will record four lanes"
    lanes = 4
    subband_offset = 12
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

observers = []
if args.Observers:
    observers = args.Observers
    s = smtplib.SMTP('localhost')

#get the Python-style time-tuple for 2 min from now and in UTC
timesoon = time.gmtime(calendar.timegm(time.gmtime())+120)
starttime = time.strftime("%Y-%m-%dT%H:%M:00Z",timesoon)

# Tolerance for late observations, in minutes. Beyond this, email the observer
tolerance = 12.
if args.Tolerance:
    tolerance = args.Tolerance

# Hard tolerance for late observations. Beyond this, shorten the observation
hardTolerance = 30.
if args.HardTolerance:
    hardTolerance  = args.HardTolerance

if args.StartTime:
    starttime = args.StartTime
    # if starttime is significantly later than now, notify the observer
    # could use:
    #    strptime to construct a tuple from requested start time
    #    use calendar.timegm() to convert to seconds since Epoch
    starttime_tuple = time.strptime(starttime, "%Y-%m-%dT%H:%M:00Z")
    timediff = calendar.timegm(timesoon) - calendar.timegm(starttime_tuple)
    if timediff/60. > hardTolerance:
        #shorten the observation:
        inttime-=int(timediff/60.)
        if inttime < 0:
            print "Observation late by " +str(timediff/60.)+ " minutes which is more than requested integration time of " +str(inttime) + ", skipping."
            if args.Verbose and len(observers) > 0:
                title="[LOFAR-observing] " + args.Station + " problem with  observation of "
                title += Pulsar
                body  = "Dear observer,\n\n"
                body += "The observation of " + Pulsar + " with "
                body += args.Station + " was late by more than the requested "
                body += "integration time and was skipped. You may want to "
                body += "investigate the cause of the delay.\n\n"
                body += "Observation monitoring system" 
                send_message( title, body, observers, s)
            exit(1)
        elif args.Verbose:
            print "Shortened the observation by " + str(int(timediff/60.)) + " minutes"
    elif timediff/60. > tolerance:
        if args.Verbose:
            print "Observation late by " + str(int(timediff/60.)) + " minutes."
        if args.Verbose and len(observers) > 0:
            title="[LOFAR-observing] " + args.Station + " problem with  observation of "
            title += Pulsar
            body  = "Dear observer,\n\n"
            body += "The observation of " + Pulsar + " with "
            body += args.Station + " was late by more than " + str(int(timediff/60.))
            body += " minutes. You may want to investigate the cause of the delay.\n\n"
            body += "Observation monitoring system" 
            send_message( title, body, observers, s)

sleeptime = 30.

# Kill any remaining pointings first.
lcucommand = ["ssh", "glow"+station_id, "ssh de"+station_id+"c killpointing"]
lcuproc = sb.Popen( lcucommand )
if args.Verbose:
    print "Killing existing pointings with:"
    print " - ", lcucommand
ssh_success = monitor_process( lcuproc, observers, interrupt=False, verbose_out="killpointing on LCU of " + station_id + " failed", timeout=180, sleep_interval=5 )
# Wait for successful end of the ssh or an intervation of the observer:
while not ssh_success:
    print "in the while loop"
    ssh_success = monitor_process( lcuproc, observers, interrupt=False, verbose_out="killpointing on LCU of " + station_id + " failed", timeout=180, sleep_interval=5 )
    time.sleep(5)

# start beams on the LCU
lcucommand = "ssh glow" + station_id + " ssh -f de"+station_id + "c" + " '/data/home/user9/LCU-scripts/PSR_8bit_Scripts/observe-psr-universal.sh " + Pulsar + " " + str(lanes)+ "&'"
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
    recorder_command[lane] = "ssh lofar" + args.Recorders[lane] + " '~/PSR_8bit_Scripts/RunLuMP_universal.sh "
    recorder_command[lane] += Pulsar + " " + str(inttime)  + " " + data_dir
    recorder_command[lane] += " " + starttime + " DE"+station_id + " " + str(lane+1) + " "
    recorder_command[lane] += str(subband_offset) + " 1" # 1 here is the verbosity level 
    recorder_command[lane] += " >> ~/PSR_Logs/LuMP_"+data_dir+"_"+Pulsar+"_lane"
    recorder_command[lane] += str(lane+1) + ".log 2>&1' "

if args.Verbose:
    print "Starting dumps on lofarN with:"
    for lane in range(0, lanes):
        print recorder_command[lane]

#sleep half a minute as there is a delay before beam formation
time.sleep(30)

recorder_processes = []
for lane in range(0, lanes):
    recorder_processes.append("")
    recorder_processes[lane] = sb.Popen(recorder_command[lane], shell=True,
            stdin=sb.PIPE, stdout=sb.PIPE, stderr=sb.PIPE, close_fds=True)

waitminutes = inttime+1.
print "Waiting "+str(waitminutes)+" min for the observation to finish"
nsleeps = int((waitminutes*60)/sleeptime)
for n in range(nsleeps):
    for lane in range(0, lanes):
        #the process should be still running and thus poll should return None
        if recorder_processes[lane].poll() != None:
            print "Recording of lane " + str(lane) + " finished after " + str(n*sleeptime/60) + " minutes while the observation should have lasted " + str(waitminutes-1) + " minutes."
            #TODO email the observer
#time.sleep(waitminutes*60.) #wait till udpdump starts. TODO Could instead monitor the status of the process. If failed, notify the observer
        time.sleep(sleeptime)

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
            print "Process for lane"+ str(lane+1) + " still running, killing it softly."
        recorder_processes[lane].terminate()

#Give processes a chance to terminate gracefully
time.sleep(1)

for lane in range(0, lanes):
    if not done(recorder_processes[lane]):
        if args.Verbose:
            print "Process for lane" + str(lane+1) + " still running, killing it!"
        recorder_processes[lane].kill()

print "stopping beams:"
lcucommand = "ssh glow"+station_id+" ssh de"+station_id+"c killpointing " # + Pulsar
lcuproc = os.popen(lcucommand)

if len(observers) > 0:
    if (args.Verbose):
        print "quitting an instance of smtplib"
    s.quit()
