#!/usr/bin/python
# Stefan Oslowski, Jan 16 2015


import socket
import time
import calendar
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

    def flush(self):
        self.f.flush()


parser = OptionParser()

parser.add_option('--psr', '--pulsar', dest='Pulsar', type='string',
                  metavar='PULSAR')

parser.add_option(
    '--BN',
    '--lofarBN',
    dest='RunBN',
    metavar='STATION',
    type='string',
    help='Run processes on lofarBN.',
    )
parser.add_option(
    '--C12',
    '--lofarC12',
    dest='RunC12',
    metavar='STATION',
    type='string',
    help='Run processes on lofarC12.',
    )
parser.add_option(
    '--C34',
    '--lofarC34',
    dest='RunC34',
    metavar='STATION',
    type='string',
    help='Run processes on lofarC34.',
    )
parser.add_option(
    '--D12',
    '--lofarD12',
    dest='RunD12',
    metavar='STATION',
    type='string',
    help='Run processes on lofarD12.',
    )
parser.add_option(
    '--D34',
    '--lofarD34',
    dest='RunD34',
    metavar='STATION',
    type='string',
    help='Run processes on lofarD34.',
    )
parser.add_option('-v', '--verbose', dest='Verbose', action='store_true'
                  , help='turn on verbosity')

(options, args) = parser.parse_args()

if options.Verbose:
    sys.stdout = flushfile(sys.stdout)

if not options.Pulsar:
    print 'Need pulsar name! Use "-h" for help.'
    exit(1)
Pulsar = options.Pulsar

if not (options.RunBN or options.RunC12 or options.RunC34
        or options.RunD12 or options.RunD34):
    print 'Need to specify at least one set of machines to run processes on!'
    exit(1)

# start the commands

runningJobs = []

if options.RunBN:
    for x in range(1, 5):
        lofarcommand = 'ssh lofarB' + str(x) \
            + " '~/PSR_8bit_Scripts/process_test_pulsar.sh " + Pulsar \
            + " " + options.RunBN + " 4'"
        if options.Verbose:
            print 'Executing:', lofarcommand
        runningJobs.append([sb.Popen(
            lofarcommand,
            shell=True,
            stdin=None,
            stdout=sb.PIPE,
            stderr=sb.STDOUT,
            close_fds=True,
            ), 'lofarB' + str(x)])

if options.RunC12:
    for x in range(1, 3):
        lofarcommand = 'ssh lofarC' + str(x) \
            + " '~/PSR_8bit_Scripts/process_test_pulsar.sh " + Pulsar \
            + " " + options.RunC12 + " 8'"
        if options.Verbose:
            print 'Executing:', lofarcommand
        runningJobs.append([sb.Popen(
            lofarcommand,
            shell=True,
            stdin=None,
            stdout=sb.PIPE,
            stderr=sb.STDOUT,
            close_fds=True,
            ), 'lofarC' + str(x)])

if options.RunC34:
    for x in range(3, 5):
        lofarcommand = 'ssh lofarC' + str(x) \
            + " '~/PSR_8bit_Scripts/process_test_pulsar.sh " + Pulsar \
            + " " + options.RunC34 + " 8'"
        if options.Verbose:
            print 'Executing:', lofarcommand
        runningJobs.append([sb.Popen(
            lofarcommand,
            shell=True,
            stdin=None,
            stdout=sb.PIPE,
            stderr=sb.STDOUT,
            close_fds=True,
            ), 'lofarC' + str(x)])

if options.RunD12:
    for x in range(1, 3):
        lofarcommand = 'ssh lofarD' + str(x) \
            + " '~/PSR_8bit_Scripts/process_test_pulsar.sh " + Pulsar \
            + " " + options.RunD12 + " 8'"
        if options.Verbose:
            print 'Executing:', lofarcommand
        runningJobs.append([sb.Popen(
            lofarcommand,
            shell=True,
            stdin=None,
            stdout=sb.PIPE,
            stderr=sb.STDOUT,
            close_fds=True,
            ), 'lofarD' + str(x)])

if options.RunD34:
    for x in range(3, 5):
        lofarcommand = 'ssh lofarD' + str(x) \
            + " '~/PSR_8bit_Scripts/process_test_pulsar.sh " + Pulsar \
            + " " + options.RunD34 + " 8'"
        if options.Verbose:
            print 'Executing:', lofarcommand
        runningJobs.append([sb.Popen(
            lofarcommand,
            shell=True,
            stdin=None,
            stdout=sb.PIPE,
            stderr=sb.STDOUT,
            close_fds=True,
            ), 'lofarD' + str(x)])


def done(p):
    return p.poll() is not None


while len(runningJobs) > 0:
    time.sleep(20)
    for job in runningJobs:
        if not done(job[0]) and options.Verbose:
            print 'Processing on ', job[1], ' still running'
        else:
            if options.Verbose:
                print 'Job on ', job[1], ' finished, copying plots'

            #mkdircommand = "mkdir -p ~/PSR_files/test_obs/"+job[1]+"/"+Pulsar
            #if options.Verbose:
                #print 'executing ', mkdircommand
            
            #sb.call(mkdircommand, shell=True, stdin=None,
                    #stdout=sb.PIPE, stderr=sb.STDOUT)

            #scpcommand = 'scp ' + job[1] \
                #+ ":/media/scratch/observer/LuMP_DE60'*/" + Pulsar \
                #+ "/201*/*png' ~/PSR_files/test_obs/" + job[1] + "/" \
                #+ Pulsar + "/."
            #if options.Verbose:
                #print 'executing ', scpcommand

            #sb.call(scpcommand, shell=True, stdin=None,
                    #stdout=sb.PIPE, stderr=sb.STDOUT)

            #rmcommand= "ssh " + job[1] \
                #+ " 'rm /media/scratch/observer/LuMP_DE60*/" + Pulsar \
                #+ "/201*/*png'"
            #if options.Verbose:
                #print 'executing ', rmcommand
            
            #sb.call(rmcommand, shell=True, stdin=None,
                    #stdout=sb.PIPE, stderr=sb.STDOUT)

            #scpcommand = 'scp ' + job[1] \

            runningJobs.remove(job)
            if options.Verbose:
                print 'removed the job from the list, now have ', \
                    str(len(runningJobs)), ' jobs left'

