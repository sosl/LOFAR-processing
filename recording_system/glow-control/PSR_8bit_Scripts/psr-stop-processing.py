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


parser = OptionParser(usage='Usage: %prog [options]\n\n'\
				     'Will kill all instances of:\n'\
 				     'sleep, run_process*sh, main_daemon.sh')

parser.add_option(
    '--BN',
    '--lofarBN',
    dest='RunBN',
    action='store_true',
    help='Stop master daemon and its children on lofarBN.',
    )
parser.add_option(
    '--C12',
    '--lofarC12',
    dest='RunC12',
    action='store_true',
    help='Stop master daemon and its children on lofarC12.',
    )
parser.add_option(
    '--C34',
    '--lofarC34',
    dest='RunC34',
    action='store_true',
    help='Stop master daemon and its children on lofarC34.',
    )
parser.add_option(
    '--D12',
    '--lofarD12',
    dest='RunD12',
    action='store_true',
    help='Stop master daemon and its children on lofarD12.',
    )
parser.add_option(
    '--D34',
    '--lofarD34',
    dest='RunD34',
    metavar='STATION',
    action='store_true',
    help='Stop master daemon and its children on lofarD34.',
    )
parser.add_option('-v', '--verbose', dest='Verbose', action='store_true'
                  , help='turn on verbosity')

(options, args) = parser.parse_args()

if options.Verbose:
    sys.stdout = flushfile(sys.stdout)

if not (options.RunBN or options.RunC12 or options.RunC34
        or options.RunD12 or options.RunD34):
    print 'Need to specify at least one set of machines to run processes on!'
    exit(1)

# start the commands

runningJobs = []

if options.RunBN:
    for x in range(1, 5):
        lofarcommand = 'ssh lofarB' + str(x) +" 'killall sleep run_process_normal_pulsars.sh run_process_highdm_pulsars.sh main_daemon.sh'"
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
        lofarcommand = 'ssh lofarC' + str(x) +" 'killall sleep run_process_normal_pulsars.sh run_process_highdm_pulsars.sh main_daemon.sh'"
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
        lofarcommand = 'ssh lofarC' + str(x) +" 'killall sleep run_process_normal_pulsars.sh run_process_highdm_pulsars.sh main_daemon.sh'"
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
        lofarcommand = 'ssh lofarD' + str(x) +" 'killall sleep run_process_normal_pulsars.sh run_process_highdm_pulsars.sh main_daemon.sh'"
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
        lofarcommand = 'ssh lofarD' + str(x) +" 'killall sleep run_process_normal_pulsars.sh run_process_highdm_pulsars.sh main_daemon.sh'"
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

