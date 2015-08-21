#!/usr/bin/env python

# Copyright (C) 2015 by Stefan Oslowski
# This work is licensed under a Creative Commons Attribution 4.0 International License.
# This script comes WITHOUT ANY WARRANTY
# 
# The friendly summary of the license terms is:
# 
# You are free to:
#
# Share — copy and redistribute the material in any medium or format
# Adapt — remix, transform, and build upon the material
# for any purpose, even commercially.
#
# The licensor cannot revoke these freedoms as long as you follow the license terms.
#
# Under the following terms:
#
# Attribution — You must give appropriate credit, provide a link to the license, and
# indicate if changes were made. You may do so in any reasonable manner, but not in
# any way that suggests the licensor endorses you or your use.
#
# No additional restrictions — You may not apply legal terms or technological measures
# that legally restrict others from doing anything the license permits.
#
# See the full text at https://creativecommons.org/licenses/by/4.0/legalcode

# NOTE This is still a work in progress.

# coding: utf-8
import psrchive as psr
from optparse import *
from scipy.stats import sigmaclip
from scipy.signal import medfilt
from numpy import concatenate
from numpy import std
from numpy import average
from numpy import where
from numpy import newaxis
from os.path import splitext

def apply_weights(data, weights):
    nsubs, nchans, nbins = data.shape
    for isub in range(nsubs):                                 
        data[isub] = data[isub]*weights[isub,...,newaxis]  
    return data

parser = OptionParser ()

parser.add_option('-a', '--archive', dest='archive_name', type='string', \
                  metavar="ARCHIVE")

parser.add_option('-t', '--threshold', dest='threshold', type='int', \
                  default=4)

parser.add_option('--kernel-size_subint', dest='kernel_subint', type='int', \
                  default=17, help="median filter kernel size for subint clipping. Must be odd.")

parser.add_option('--kernel-size_channel', dest='kernel_channel', type='int', \
                  default=17, help="median filter kernel size for channel clipping. Must be odd.")

parser.add_option('-w','--apply_weights', dest='apply_weights', \
                  action='store_true', default=False)

parser.add_option('-f', '--onpulse_start', dest='opf', type='int', \
                   default=-1, help="first bin of the on-pulse region", \
                   metavar="ONPULSE_START")
parser.add_option('-l', '--onpulse_stop', dest='opl', type='int', \
                  default=-1, help="last bin of the on-pulse region", \
                   metavar="ONPULSE_STOP")

parser.add_option('-s', '--subint', dest='subint_only', \
                  action='store_true', default=False, \
                  help="zap only in time domain")
parser.add_option('-c', '--channel', dest='channel_only', \
                  action='store_true', default=False, \
                  help="zap only in frequency domain")

parser.add_option('-e', '--extension', dest='ext', type='string', \
                  default="ZZ", help="extension of the output file")
parser.add_option('-v', '--verbose', dest='verbose', \
                  action='store_true', default=False, help = "enable verbosity")

#parser.add_options('-n', '--number_of_passes', dest=no_passes, type=int, \ #not implemented
                   #help
                  
(options, args) = parser.parse_args()

ext = "." + options.ext

threshold =  options.threshold
if  (options.opf > 0 or options.opl > 0 ) and options.opf * options.opl < 0:
    print "Please provide both opl and opf!"
    print "You can determine these yourself or use:"
    print "psrstat -c on:start,on:end archive.ar"
    print "Currently only a single on-pulse region is supported"
    exit(1)

if (options.subint_only and options.channel_only):
    print "WARNING: you provided both --subint and --channel, will zap in both"
    options.subint_only = False
    options.channel_only = False

opf = options.opf
opl = options.opl
if not options.archive_name:
    print "ERROR: you must provide an input archive"
    exit(1)
archive_name = options.archive_name

ar = psr.Archive_load(archive_name)
if options.verbose:
    print "Loaded " + archive_name

#prepare the input archive
# will need to reload the archive before zapping to preserve the input state. I
# think the overhead with reloading the archive will be smaller than the memory
# overhead for cloning the archive, especially for LOFAR data
# we don't use polarisation information
ar.pscrunch()
# don't want the baseline - in the past tried without as this has some
# advantages (no zeroes without applying weights) but in the end I think this works better
ar.remove_baseline()
# must dedisperse to get rid of the on-pulse region
ar.dedisperse()

if options.verbose:
    print "finished basic processing: pscrunch, baseline subtraction and dedispersion"

data = ar.get_data()
#apply previous zapping to data:
weights = ar.get_weights()
data_w = apply_weights(data.squeeze(), weights) # squeeze removes the pol dimension

remove_list = []
#zap in time (1) and frequency (0) domains
for _axis in [1, 0]:
    #scrunch the unwanted dimension
    data_ws = data_w.mean(axis=_axis)
    if options.verbose:
        print "scrunched the data in axis with index " + str(_axis)
    # do I need this here? I did it for scoping reasons, not sure if that's
    # necessary for python:
    data_off = data_ws
    # remove the on-pulse region
    if (opf > 0 or opl > 0) and (opf*opl  > 0):
        dataA=data_ws[:,0:opf]
        dataB=data_ws[:,opl:ar.get_nbin()]
        data_off = concatenate((dataA,dataB),1)
        if options.verbose:
            print "prepared off-pulse data by excluding bins from " + str(opf) + " till " + str(opl)
    else:
        print "WARNING: no on-pulse region specified, this zapper is meant to be used on off-pulse only"
        # not necessary as done above for scoping purposes:
        #data_off = data_ws

    # average phase bins
    data_off_mean = data_off.mean(1)
    if options.verbose:
        print "calculated average over phase bins"
    # apply median filter: does this actually help? I think it will if there is
    # a significant baseline trend across the archive. Otherwise the impact is
    # small albeit easy to see (in testing about 5% difference in number of
    # zapped subunits.
    if _axis == 1:
        _kernel_size = options.kernel_subint
    elif _axis == 0:
        _kernel_size = options.kernel_channel
    data_off_mean_medfilt = medfilt(data_off_mean, kernel_size=_kernel_size)
    if options.verbose:
        print "applied a median filter with kernel size of " + str(kernel_size)
    # subtract the median-filtered data from data:
    data_off_mean_subtr_medfilt = data_off_mean - data_off_mean_medfilt
    # apply sigma clipping to enable std dev estimation (could use robust stats
    # here instead)
    sigma_clipped_post_subtr, tmpA, tmpB = sigmaclip(data_off_mean_subtr_medfilt)
    if options.verbose:
        print "prepared a sigma-clipped version of the data"
    # get stats of the sigma clipped data:
    # maybe use robust stats here:
    stddev_post_subtr  = std(sigma_clipped_post_subtr)
    avg_post_subtr = average(sigma_clipped_post_subtr)
    # reform the data as deviations from the sigma-clipped average:
    data_off_mean_subtr_medfilt_renorm = abs( (data_off_mean_subtr_medfilt - avg_post_subtr) / stddev_post_subtr )
    # find data to be zapped:
    remove_post = where(data_off_mean_subtr_medfilt_renorm > threshold) #this returns a tuple with an ndarray
    remove_list.append(remove_post[0].tolist())
    print "removing axis " + str(_axis)
    if options.verbose:
	    print remove_post[0]

# apply the zapping scheme to the original data:
# (this is where the reloading occurs, could clone instead but... see above)
ar = psr.Archive_load(archive_name)
#for isubint in remove_list[0]:
for isubint in range(ar.get_nsubint()):
    integr = ar.get_Integration(int(isubint))
    try:
        #zap the whole subint
        tmp_index = remove_list[0].index(isubint) # index can be discarded
        for ichan in range(ar.get_nchan()):
            integr.set_weight(int(ichan), 0.0)
    except ValueError:
        #zap chosen subints:
        for ichan in remove_list[1]:
            integr.set_weight(int(ichan), 0.0)

ar.unload(splitext(archive_name)[0]+ext)
if options.verbose:
    print "Unloaded " + splitext(archive_name)[0]+ext
