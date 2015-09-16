#!/usr/bin/env python
# coding=utf-8

country_codes = [ "PL", "DE", "SE", "FR", "UK" ]

def append_observation(obs_id, psr, Tint, site, recorders, observers,
        expectedStart, log, LCUPath, list):
    list.append("date" + log)
    notification = "echo 'Starting observation " + obs_id + " on " + psr
    if len(expectedStart) > 0:
        notification += "(expected at " + expectedStart + " )"
    notification += "' " + log
    list.append(notification)
    obs_command  = "~/PSR_8bitScripts/ObserveGeneric.py -P " + psr
    obs_command += "-T " + Tint + " -s " + site + " -R "
    for recorder in recorders:
        obs_command += recorder + " "
    if len(observers) > 0:
        obs_comand += "-O "
        for observer in observers:
            obs_command += observer + " "
    if len(LCUPath) > 0:
        obs_command += " --LCU " + LCUPath
    obs_command += " -v >> " + args.inputFile[0] + ".log\n\n"
    list.append(obs_command)

"""
Convert the output of observePulsars.py into an executable schedule file
Copyright Stefan Oslowski 2015
Based on an old script by Joris P.W. Verbiest
"""
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('inputFile', metavar='INPUT', nargs=1,
        help="Input list of pulsars for observations.")

parser.add_argument('-s', '--site', dest='location', help="Telescope")
parser.add_argument('-S', '--auto-site', dest='autoLocation', action="store_true",
        help="Try to determine location automatically from the input file name")

parser.add_argument("-R", "--recorder", nargs='+', dest="Recorders",
        help="Recording machines to be used, white-space separated."
        " Must be a list of three or four machines to record three "
        " or four lanes. E.g., '-R C1 C2 C2' will record lane 1 to "
        "C1 and lanes 2 and 3 to C2")

parser.add_argument("-T", "--include-test", dest="includeTest", action="store_true",
        help="Include a test observation at the beginning of the run")
parser.add_argument("-A", "--automatic-test", dest="autoTest", action="store_true",
        help="Try to determine automatically a suitable test pulsar. Implies -T")

parser.add_argument("-p", "--power-down", dest="LCUPowerDown", action="store_true",
        help="Power down the LCU after observations are finished.")
parser.add_argument("-P", "--prefix-to-LCU", dest="LCUPath",
        help="How to ssh to the LCU. Use SID to use station id,"
        " STATION to use full station name, and LSTATION to use lower-case "
        "full station name. E.g., '-P \"ssh glowSID ssh LSTATIONc\"' is needed "
        " for use with the German GLOW stations.")

parser.add_argument("-O", "--observer", nargs='*', dest="Observers",
        help="Email of the observer(s) for observing notifications")

parser.add_argument("-v", "--verbose", dest="Verbose", action="store_true",
        help="Verbose (more detailed output)")

args = parser.parse_args()

if not (args.location or args.autoLocation):
    print "Must provide site or allow automatic determination."
    exit(1)

if not args.Recorders or len(args.Recorders) < 3 or len(args.Recorders) > 4:
    print "Must provide exactly three or four recording machines for each lane."
    print "The machines may be reused for multiple lanes."
    exit(1)

if args.includeTest and args.autoTest:
    print "Please use either -A or -T, not both"
    exit(1)

site = ""
if args.location:
    site = args.location.upper()
else:
    for country_code in country_codes:
        if args.inputFile[0].upper().find(country_code) >= 0:
            index = args.inputFile[0].upper().find(country_code)
            site_country_code = country_code
            site_id = args.inputFile[0][index+2:index+5]
            site = site_country_code + site_id
            if args.Verbose:
                print "determined site to be " + site
if args.Verbose:
    print "processing " + args.inputFile[0]
    print "will use the following recorders:"
    print args.Recorders

observers = []
if args.Observers:
    observers = args.Observers

f = open(args.inputFile[0], "r")
lines = f.readlines()
f.close()

print len(lines)

outputLines = []

outputLines.append("#!/bin/bash\n\n")

LCUPath = ""
if args.LCUPath:
    LCUPath = args.LCUPath.replace("SID", site[2:]).replace("LSTATION", site.lower()).replace("STATION", site)
#if args.includeTest:
#    append_observation("TEST", "TEST", "4", site, args.Recorders, args.Observers

print_to_tty_and_log = " | tee -a " + args.inputFile[0] + ".log\n"
first_obs = True
obs_id = 1
for line in lines:
    elements = line.split()
    if len(elements) != 7:
        print "Unsupported format of the input!"
        print "Please ensure the following 7-column format:"
        print "psr Tint LST: hh:mm UTC: yyyy-mm-dd hh:mm"
        exit(1)
    psr = elements[0]
    Tint = elements[1]
    if elements[2] != "LST:":
        print "The third column should indicate type of time in fourth column"
        print "Currently only LST is accepted."
        exit(1)
    LST = elements[2] + " " + elements[3]
    if elements[4] != "UTC:":
        print "The fifth column should indicate timezone of expected start time"
        print "Currently only UTC is accepted"
        exit(1)
    UTC = elements[4] + " " + elements[5] + " " + elements[6]
    #print line
    #print "PSR: " + psr
    #print "Tint: " + Tint
    #print "LST: " + LST
    #print "UTC: " + UTC
    append_observation(str(obs_id), psr, str(Tint), site, args.Recorders,
            observers, UTC, print_to_tty_and_log, LCUPath, outputLines)
    obs_id += 1

if args.LCUPowerDown:
    powerDownCommand  = "date" + print_to_tty_and_log
    powerDownCommand += "echo 'Finished observing'" + print_to_tty_and_log 
    powerDownCommand += LCUPath + " 'swlevel 0'" + print_to_tty_and_log
    outputLines.append(powerDownCommand)

f = open(args.inputFile[0] + ".sched", "w")
f.writelines(outputLines)
f.close()
