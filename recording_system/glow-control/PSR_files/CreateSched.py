#!/usr/bin/env python
# coding=utf-8

"""
Convert the output of observePulsars.py into an executable schedule file
Copyright Stefan Oslowski 2015
Based on an old script by Joris P.W. Verbiest
"""
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-s', '--site', dest='location', help="Telescope")

parser.add_argument("-R", "--recorder", nargs='+', dest="Recorders",
        help="Recording machines to be used, white-space separated."
        " Must be a list of three or four machines to record three "
        " or four lanes. E.g., '-R C1 C2 C2' will record lane 1 to "
        "C1 and lanes 2 and 3 to C2")

parser.add_argument("-T", "--include-test", dest="includeTest", action="store_true",
        help="Include a test observation at the beginning of the run")
parser.add_argument("-A", "--automatic-test", dest="autoTest", action="store_true",
        help="Try to determine automatically a suitable test pulsar. Implies -T")

