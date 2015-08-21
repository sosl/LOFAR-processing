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

parser.add_option(
    '--BN',
    '--lofarBN',
    dest='RunBN',
    metavar='STATION',
    type='string',
    help='Run master daemon for station STATION on lofarBN.',
    )
parser.add_option(
    '--C12',
    '--lofarC12',
    dest='RunC12',
    metavar='STATION',
    type='string',
    help='Run master daemon for station STATION on lofarC12.',
    )
parser.add_option(
    '--C34',
    '--lofarC34',
    dest='RunC34',
    metavar='STATION',
    type='string',
    help='Run master daemon for station STATION on lofarC34.',
    )
parser.add_option(
    '--D12',
    '--lofarD12',
    dest='RunD12',
    metavar='STATION',
    type='string',
    help='Run master daemon for station STATION on lofarD12.',
    )
parser.add_option(
    '--D34',
    '--lofarD34',
    dest='RunD34',
    metavar='STATION',
    type='string',
    help='Run master daemon for station STATION on lofarD34.',
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
        lofarcommand = 'ssh lofarB' + str(x) \
            + " '~/PSR_8bit_Scripts/aux_scripts/main_daemon.sh " \
            + " " + options.RunBN + "'"
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
            + " '~/PSR_8bit_Scripts/aux_scripts/main_daemon.sh " \
            + " " + options.RunC12 + "'"
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
            + " '~/PSR_8bit_Scripts/aux_scripts/main_daemon.sh " \
            + " " + options.RunC34 + "'"
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
            + " '~/PSR_8bit_Scripts/aux_scripts/main_daemon.sh " \
            + " " + options.RunD12 + "'"
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
            + " '~/PSR_8bit_Scripts/aux_scripts/main_daemon.sh " \
            + " " + options.RunD34 + "'"
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
    time.sleep(600)
    for job in runningJobs:
        if done(job[0]):
            runningJobs.remove(job)
