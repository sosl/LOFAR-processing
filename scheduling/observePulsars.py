#!/usr/bin/env python
# coding=utf-8

"""
Python module / application to create a pulsar observation schedule with good visibility

Jörn Künsemöller
"""


import errno
import argparse
import dateutil.parser
import astropysics.obstools as obstools
import astropysics.coords as coords
import matplotlib
matplotlib.use('Agg')
import datetime
import os
import re
from matplotlib.dates import HOURLY, DateFormatter, rrulewrapper, RRuleLocator
from pylab import *
import subprocess
import time



# Default Settings:
defaultObservationCmd = "~/PSR_8bit_Scripts/Observe_DE601_C34.py"
defaultOutputPath = os.getcwd()+"/schedule.txt"
defaultAllowIdle = False
defaultIdlePenalty = 2
defaultInitialRetries = 20
defaultTimePenalty = 1
defaultDropPenalty = 500
defaultLocation='DE609'
defaultLogPath= os.getcwd()
defaultObserverSetupTime = 2
defaultInputPath = None

# Config:
maxObsDays = 4  # in case no limit is specified
sites = dict(DE609=obstools.Site(lat=coords.AngularCoordinate('53d42m0s'),
                                       long=coords.AngularCoordinate('9d85m50s'),
                                       name="DE609"),
             DE601=obstools.Site(lat=coords.AngularCoordinate('50d31m0s'),
                                 long=coords.AngularCoordinate('6d53m0s'),
                                 name="DE601"),
             DE602=obstools.Site(lat=coords.AngularCoordinate('48d30m4s'),
                                 long=coords.AngularCoordinate('11d17m13s'),
                                 name="DE602"),
             DE603=obstools.Site(lat=coords.AngularCoordinate('50d59m0s'),
                                 long=coords.AngularCoordinate('11d43m0s'),
                                 name="DE603"),
             DE605=obstools.Site(lat=coords.AngularCoordinate('50d55m0s'),
                                 long=coords.AngularCoordinate('6d21m0s'),
                                 name="DE605"),
             SE607=obstools.Site(lat=coords.AngularCoordinate('57d23m54s'),
                                 long=coords.AngularCoordinate('11d55m50s'),
                                 name="SE607")
            )
colorNormalizeBadness = 300.0
verbose = 1

# Tuning config: Faster processing vs. quality:
minshift = datetime.timedelta(seconds=60)  # stop fair shifting for small overlaps and flatten out schedule
#initialRetries = defaultInitialRetries    # Minimize penalty over so many initial spreadings on observation days (random sequence order)
# Stefan: added an option for initialRetries and a default value

# Create directories with tolerance for existence, exception handling...
def safeMakedirs(directory, permissions):
    try:
        directory = os.path.normpath(os.path.expanduser(directory))
        if verbose > 0:
            print "...creating directory", directory
        os.makedirs(directory,permissions)
        if verbose > 0:
            print "...done."
    except OSError as err:
        if err.errno == errno.EEXIST and os.path.isdir(directory):
            if verbose > 0:
                print "...done. (Already there.)"
            pass
        else:
            if verbose > 0:
                print "! ERROR--> Could not create directory: ", err.message
            exit(2)

# Determine total overlap in given schedule (in minutes)
def determineoverlap(schedule):
    schedule = sorted(schedule, key=lambda x: x[3])
    overlap = 0
    tmpschedule = list(schedule)
    for (pulsar, start, stop, optimalUTC, priority) in schedule:
        tmpschedule.remove((pulsar, start, stop, optimalUTC, priority))
        for(comparepulsar, comparestart, comparestop, compareoptimalUTC, comparepriority) in tmpschedule:
            overlapping = min(stop, comparestop) - max(start, comparestart)
            if overlapping.days >= 0:  # we have overlap
                overlap += overlapping.days * 24 * 60 + overlapping.seconds / 60

    return overlap


# Estimate required total shift to solve all overlaps in given schedule (in minutes)
# Note that this only returns a lower limit! (when several observations overlap, each
# shift might impact the following shifts, which is not considered here...)
def estimateshift(schedule):
    schedule = sorted(schedule, key=lambda x: x[3])
    shift = 0
    tmpschedule = list(schedule)
    for (pulsar, start, stop, optimalUTC, priority) in schedule:
        tmpschedule.remove((pulsar, start, stop, optimalUTC, priority))
        for (comparepulsar, comparestart, comparestop, compareoptimalUTC, comparepriority) in tmpschedule:
            thisshift = min((stop - comparestart), (comparestop - start))
            if thisshift.days >= 0:  # we have to shift
                shift += thisshift.days * 24 * 60 + thisshift.seconds / 60

    return shift


# time badness of single observation
def determinetimebadness(start, stop, optimalUTC, timePenalty=defaultTimePenalty):
    delta = (optimalUTC - start) + (optimalUTC - stop)
    if delta.days < 0:
        delta = -delta
    badness = delta.days * 24 * 60 + delta.seconds / 60 * timePenalty

    return badness

# total time badness of alls observation in a schedule
def determinetotaltimebadness(schedule, timePenalty=defaultTimePenalty):

    badness = 0
    for (pulsar, start, stop, optimalUTC, priority) in schedule:
        badness += determinetimebadness(start, stop, optimalUTC)
    return badness

# display gantt chart of a schedule
def plotschedule(begin, end, deadline, schedule, title='Schedule',
                 timePenalty=defaultTimePenalty, blocking=True, display=False):

    fig = plt.figure()
    fig.set_size_inches(18,13.5)
    ax = fig.add_axes([0.2,0.2,0.75,0.7])  #[left,bottom,width,height]
    ax.set_title(title)

    ax.axvline(x=begin, color="green")
    if end is not None:
        ax.axvline(x=end, color="blue")
    if deadline is not None:
        ax.axvline(x=deadline, color="red")

    # Plot the data
    for (pulsar,start,stop, optimalUTC, priority) in reversed(schedule):
        start_date = matplotlib.dates.date2num(start)
        stop_date = matplotlib.dates.date2num(stop)
        duration = stop_date - start_date
        optimal_start = matplotlib.dates.date2num(optimalUTC) - 0.5*duration

        ax.axhline(y=schedule.index((pulsar,start,stop, optimalUTC, priority)), color=(0.8, 0.8, 0.8), zorder=0)

        ax.barh((schedule.index((pulsar,start,stop, optimalUTC, priority))), duration, left=optimal_start, height=0.5,align='center',label=pulsar, color=(0.9, 0.9, 0.9), edgecolor = "none")
        ax.barh((schedule.index((pulsar,start,stop, optimalUTC, priority))), duration, left=start_date, height=0.6, align='center',label=pulsar, color=(min(determinetimebadness(start, stop, optimalUTC, timePenalty), int(colorNormalizeBadness))/colorNormalizeBadness,  0.0, 0.0))

    # Format y-axis
    pos = range(len(schedule))
    locsy, labelsy = yticks(pos, zip(*schedule)[0])
    plt.setp(labelsy,size='medium')


    # Format x-axis
    ax.axis('tight')
    ax.xaxis_date()

    rule = rrulewrapper(HOURLY, interval=3)
    loc = RRuleLocator(rule)
    formatter = DateFormatter("%d %h - %H h")

    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(formatter)
    labelsx = ax.get_xticklabels()
    plt.setp(labelsx, rotation=30, fontsize=10)

    if begin is None:
        begin = datetime.datetime.now()
    if deadline is not None:
        plt.xlim(begin - datetime.timedelta(hours=1) ,deadline + datetime.timedelta(hours=1))
    elif end is not None:
        plt.xlim(begin - datetime.timedelta(hours=1) ,end + datetime.timedelta(hours=1))
    else:
        plt.xlim(begin)

    fig.autofmt_xdate()
    plt.savefig('gantt.svg')
    plt.show(block=blocking)



# shifts observations in the schedule to get rid of any overlap. Some observations may be dropped in the process.
# Note: This is not very efficient!
def solveschedule(begin, end, deadline, schedule, timePenalty=defaultTimePenalty, dropPenalty=defaultDropPenalty):

    if verbose > 1:
        print "...Solving overlap in schedule"
    # sort by optimalUTC
    schedule = sorted(schedule, key=lambda x: x[3])

    # solve overlap:
    shifting = True     # observations were shifted in last run
    dropping = True     # observations were dropped in last run

    count = 0
    while shifting or dropping:
        if verbose > 2:
            print "  ...Next interation"
        if dropping:
            tmpschedule = list(schedule)    # start again with fresh schedule (where observations have optimal timing)
        dropping = False
        shifting = False
        fixed = []
        for (pulsar, start, stop, optimalUTC, priority) in tmpschedule:
            if verbose > 2:
                print "  ...Now handling observation of ",pulsar
            i = tmpschedule.index((pulsar, start, stop, optimalUTC, priority))
            if determinetimebadness(start, stop, optimalUTC, timePenalty) > dropPenalty * int(priority):
                if verbose > 2:
                    print "  ...Dropping",pulsar,"due to high time badness",determinetimebadness(start, stop, optimalUTC, timePenalty), dropPenalty
                schedule.pop(i)
                dropping = True
                break
            if i == len(tmpschedule)-1:
                break
            (nextpulsar, nextstart, nextstop, nextoptimalUTC, nextpriority) = tmpschedule[i+1]
            deltanext = stop - nextstart
            if deltanext.days >= 0 and deltanext.seconds > 0:
                shifting = True
                if verbose > 3:
                    print "    ...Conflicting with next observation by ", deltanext
                #deltaformer =  start - begin
                # if deltanext/2 > deltaformer:
                #     if verbose > 3:
                #         print "    ...Not enough space for early start. Shifting backwards by", deltaformer," and pushing",nextpulsar," observation by", deltanext - deltaformer
                #     shift = (begin - start)
                #     start = start + shift
                #     stop = stop + shift
                #     nextstart = nextstart + (deltanext - shift)
                #     nextstop = nextstop + (deltanext - shift)
                #     fixed.append((pulsar, start, stop, optimalUTC, priority))
                #     fixed.append((nextpulsar, nextstart, nextstop, nextoptimalUTC, nextpriority))
                # el
                if (pulsar, start, stop, optimalUTC, priority) in fixed:
                    if verbose > 3:
                        print "    ...",pulsar,"is fixed. Shifting",nextpulsar,"by", deltanext
                    dropped = False
                    for (tmppulsar, tmpstart, tmpstop, tmpUTC, tmppriority) in fixed:
                        if (nextstop + deltanext) > tmpstart and (nextstop + deltanext) < tmpstop:
                            if verbose > 3:
                                print "    ...cannot shift", nextpulsar, "since the new time is blocked by", tmppulsar
                            tmpschedule.remove(nextpulsar, nextstart, nextstop, nextoptimalUTC, nextpriority)
                            dropped = True
                            break
                    if not dropped:
                        nextstart += deltanext
                        nextstop += deltanext
                        fixed.append((nextpulsar, nextstart, nextstop, nextoptimalUTC, nextpriority))
                        if verbose > 3:
                            print "    ...", nextpulsar,"was fixed!"
                elif (nextpulsar, nextstart, nextstop, nextoptimalUTC, nextpriority) in fixed:
                    if verbose > 3:
                        print "    ...",nextpulsar,"is fixed. Shifting",pulsar,"by", deltanext
                    dropped = False
                    for (tmppulsar, tmpstart, tmpstop, tmpUTC, tmppriority) in fixed:
                        if (nextstop + deltanext) > tmpstart and (nextstop + deltanext) < tmpstop:
                            if verbose > 3:
                                print "    ...cannot shift", pulsar, "since the new time is blocked by", tmppulsar
                            tmpschedule.remove(pulsar, start, stop, optimalUTC, priority)
                            dropped = True
                            break
                    if not dropped:
                        start -= deltanext
                        stop -= deltanext
                        fixed.append((pulsar, start, stop, optimalUTC, priority))
                        if verbose > 3:
                            print "    ...", pulsar,"was fixed!"
                elif deltanext < minshift:
                    if verbose > 3:
                        print "    ...Minimum for shift splitting is not reached. Shifting",nextpulsar,"by", deltanext
                    nextstart += deltanext
                    nextstop += deltanext
                else:
                    shift = (deltanext / (int(nextpriority) + int(priority))) * int(nextpriority)
                    nextshift = (deltanext / (int(nextpriority) + int(priority))) * int(priority)
                    if verbose > 3:
                        print "    ...Shifting",pulsar,"by", shift,"and",nextpulsar,"by", nextshift, " --> ",priority," vs. ", nextpriority
                    start -= shift
                    stop -= shift
                    nextstart += nextshift
                    nextstop += nextshift

            tmpschedule[i] = (pulsar,start,stop, optimalUTC, priority)
            tmpschedule[i+1] = (nextpulsar, nextstart, nextstop, nextoptimalUTC, nextpriority)

        count += 1
        if count%10000 == 0:
            print "    ...action counter:", count
        #    plotschedule(begin, end, deadline, tmpschedule, "count: "+str(count)+" - "+str(determineoverlap(tmpschedule)),blocking=True)


    # drop all observation that exceed the deadline
    tmpschedule = sorted(tmpschedule, key=lambda x: x[3])
    toremove = []
    for (pulsar, start, stop, optimalUTC, priority) in tmpschedule:
        if deadline is not None and stop > deadline:
            if verbose > 1:
                print "  ...dropping observation of", pulsar,"because of strict deadline overhang. (Maybe your schedule is too crowded?)"
            toremove.append((pulsar, start, stop, optimalUTC, priority))
        if start < begin:
            if verbose > 1:
                print "  ...dropping observation of", pulsar,"because of too early start. (Maybe your schedule is too crowded?)"
            toremove.append((pulsar, start, stop, optimalUTC, priority))

    # remove separately to avoid interference with first loop
    for (pulsar, start, stop, optimalUTC, priority) in toremove:
        tmpschedule.remove((pulsar, start, stop, optimalUTC, priority))

    return tmpschedule


# turns a list of planned observations into a schedule within the specified time constraints
def makeSchedule(observationList, site, begin, end, deadline, timePenalty,
                 idlePenalty, dropPenalty, initialRetries):

    if verbose > 0:
        print "Creating schedule for",len(observationList),"observations"
        print "...site is", site.name+ ", lat:",site.latitude,"long:",site.longitude

    schedule = []

    # time constraints:
    softTimeframe = None
    strictTimeframe = None
    if begin is None:
        begin = datetime.datetime.now()
        if verbose > 0:
            print "!  Begin time is set to NOW."
    if verbose > 0:
        print "...begin UTC:",begin
    if end is not None:
        softTimeframe = end-begin
        if verbose > 0:
            print "...end UTC:", end
            print "...soft timeframe duration:", softTimeframe
    if deadline is not None:
        strictTimeframe = deadline-begin
        if verbose > 0:
            print "...deadline UTC:", deadline
            print "...strict timeframe duration:", strictTimeframe
    if end is None and deadline is None and verbose > 0:
        print "...no time limits specified"

    # create initial schedule with optimal timing (but overlap):
    for (pulsar, dur, priority) in observationList:
        duration = int(dur)
        lststring = re.split("[JB+-]", pulsar)[1]
        if verbose > 2:
            print "...shall observe pulsar",pulsar,"for", duration,"minutes..."
        optimalLST = begin.replace(hour=int(lststring[:2]), minute=int(lststring[2:]), second=0, microsecond=0)
        optimalUTC = site.localTime(lsts=optimalLST.hour+optimalLST.minute/60.0, date=optimalLST.date() , returntype='datetime', utc=True)
        if verbose > 2:
            print "  ...optimal visibility at LST:",optimalLST
        optimalUTC = optimalUTC.replace(tzinfo=None)
        if verbose > 2:
            print "  ...optimal visibility at UTC:",optimalUTC
        start = optimalUTC - datetime.timedelta(seconds=30*duration)
        stop = optimalUTC + datetime.timedelta(seconds=30*duration)
        if verbose > 2:
            print "  ...optimal UTC observation time start:", start,"stop:",stop

        job = (pulsar, start, stop, optimalUTC, priority)
        schedule.append(job)

    # sort initial schedule by optimal UTC
    schedule = sorted(schedule, key=lambda x: x[3])

    if verbose > 2:
        # print schedule
        print "...These are the optimal observation times in sequential order:"
        print "... ---------------------"
        for (pulsar, start, stop, optimalUTC, priority) in schedule:
            print "... pulsar:",pulsar,"\tfrom:", start,"  to:", stop,"  badness:", (optimalUTC - start) + (optimalUTC - stop)
        print "... ---------------------"


    bestschedule = None

    # for several random sequence orders:
    #   for each observation in schedule:
    #       check observation time limits and move to day with lowest overlap
    orig_schedule = list(schedule)
    best_i = None
    for i in range(initialRetries):
        if verbose > 2:
            print "...Run", i,"..."
        schedule = list(orig_schedule)
        shuffle(schedule)
        for (pulsar, start, stop, optimalUTC, priority) in schedule:
            if verbose > 2:
                print "...",pulsar
            obsdays = maxObsDays
            if deadline is not None:
                obsdays = (deadline.date() - begin.date()).days + 1
            elif end is not None:
                obsdays = (end.date() - begin.date()).days + 1

            # create base schedule (copy schedule, drop observation in focus)
            dropschedule = list(schedule)
            dropschedule.remove((pulsar, start, stop, optimalUTC, priority))
            dropbadness = estimateshift(dropschedule) + dropPenalty * int(priority)

            # Badness for each day of the observation time
            # Schedule for each day
            badnesses = [0]*obsdays
            newschedules = [list(dropschedule) for _ in range(obsdays)]

            # check for time limits and determine badness for each observation day
            shiftbadness = 0
            for day in range(obsdays):
                #print "  ...considering scheduling",pulsar,"on day ", day
                deltabegin = begin - (start + datetime.timedelta(days=day))
                if deltabegin > datetime.timedelta(0):
                    if verbose > 2:
                        print "  ..."+pulsar+" starts too early on day",day," -- necessary shift:", deltabegin
                    badness = deltabegin.seconds / 60.0 * timePenalty
                    badnesses[day] += badness
                elif deadline is not None:
                    deltadeadline = deadline - (stop + datetime.timedelta(days=day))
                    if deltadeadline < datetime.timedelta(0):
                        if verbose > 2:
                            print "  ..."+pulsar+" stops too late for strict limit on day",day," -- necessary shift:", deltadeadline
                        badness = -deltadeadline.days * 24 * 60 - deltadeadline.seconds / 60.0 * timePenalty
                        badnesses[day] += badness

                if end is not None:
                    deltaend = end - (stop + datetime.timedelta(days=day))
                    if deltaend < datetime.timedelta(0):
                        if deltadeadline is not None:
                            deltaend -= deltadeadline  # no penalty for performed deadline shift
                        badness = -deltaend.days * 24 * 60 - deltaend.seconds / 60.0 * timePenalty
                        badnesses[day] += badness
                        if verbose > 2:
                            print "  ..."+pulsar+" stops too late for soft limit on day",day," -- overtime:", deltaend, optimalUTC

                # new schedule where the observation is moved to the the day in focus:
                if deltabegin > datetime.timedelta(0):
                    newschedules[day].append((pulsar, start + datetime.timedelta(days=day) + deltabegin, stop  + datetime.timedelta(days=day) + deltabegin, optimalUTC+datetime.timedelta(days=day), priority))
                elif deadline is not None and deltadeadline < datetime.timedelta(0):
                    newschedules[day].append((pulsar, start + datetime.timedelta(days=day) + deltadeadline, stop  + datetime.timedelta(days=day) + deltadeadline, optimalUTC+datetime.timedelta(days=day),priority))
                else:
                    newschedules[day].append((pulsar, start + datetime.timedelta(days=day), stop  + datetime.timedelta(days=day), optimalUTC+datetime.timedelta(days=day),priority))

                # Reset for next day
                badness = 0

                # time penalty for the day: shifting of observations results in time penalty
                badnesses[day] += estimateshift(newschedules[day]) * timePenalty

            # Determine best day for the observation (spreads observations amongst observation days):
            if verbose > 2:
                print "  ..."+pulsar,"-- dropbadness:",dropbadness,"-- day badnesses:", badnesses
            bestday = badnesses.index(min(badnesses))
            if bestday > dropbadness:
                # drop pulsar
                if verbose > 2:
                    print "  ...dropping ", pulsar, dropbadness,"<",badnesses[bestday]
                schedule = dropschedule
            else:
                # shift on start day or move to 'bestday'
                if verbose > 2:
                    print "  ...scheduling for observation day", bestday
                schedule = newschedules[bestday]

        # Create simple sequential schedule as initial solution:
        if bestschedule is None:
            schedule = sorted(schedule, key=lambda x: x[1])
            bestschedule = []
            laststop = None
            for j in range(len(schedule)):
                (pulsar, start, stop, optimalUTC, priority) = schedule[j]
                if j == 0:
                    dur = stop - start
                    start = begin
                    stop = start + dur
                elif laststop is not None:
                    delta = start - laststop
                    start -= delta
                    stop -= delta
                laststop = stop
                bestschedule.append((pulsar, start, stop, optimalUTC, priority))
            if verbose > 0:
                print "...Sequential base schedule -->",determinetotaltimebadness(bestschedule, timePenalty)
                plotschedule(begin, end, deadline, bestschedule,'Base schedule',timePenalty, True, True )

        # randomly drop observations as long as this improves the total result
        bestsolvedschedule = solveschedule(begin, end, deadline, list(schedule), timePenalty, dropPenalty)
        dropping = True
        shuffle(schedule)
        while dropping:
            dropping = False
            penalty = 0
            for (pulsar, start, stop, optimalUTC, priority) in schedule:
                if verbose > 1:
                    print "...Trying to improve result by dropping", pulsar
                dropschedule = list(schedule)
                dropschedule.remove((pulsar, start, stop, optimalUTC, priority))
                penalty += dropPenalty * int(priority)
                dropschedule = solveschedule(begin, end, deadline, dropschedule, timePenalty, dropPenalty)
                if determinetotaltimebadness(bestsolvedschedule, timePenalty) > determinetotaltimebadness(dropschedule, timePenalty) + penalty:
                    if verbose > 1:
                        print "...Run",i,"- Dropping",pulsar,"improved result from", determinetotaltimebadness(bestsolvedschedule, timePenalty),"to",determinetotaltimebadness(dropschedule, timePenalty),"+",penalty
                    bestsolvedschedule = dropschedule
                    dropping = True
                    break


        schedule = bestsolvedschedule

        # Is this result better then the best so far?
        if verbose > 0:
            print "...Run",i,"-->",determinetotaltimebadness(schedule, timePenalty),'+', dropPenalty * (len(orig_schedule) - len(schedule))
        if determineoverlap(bestschedule) > 0 or determinetotaltimebadness(schedule, timePenalty) < determinetotaltimebadness(bestschedule, timePenalty) +  dropPenalty * (len(schedule) - len(bestschedule)):
            bestschedule = schedule
            best_i = i
    if verbose > 0:
        if best_i is not None:
            print "...Found best schedule in",i+1,"runs. (i = "+str(best_i)+")"
        else:
            print "...Base schedule was already the best."


    bestschedule = sorted(bestschedule, key=lambda x: x[1])

    return bestschedule


# Extends observations to fill up idle times:
def fillIdleTimes(begin, end, deadline, schedule):

    schedule = sorted(schedule, key=lambda x: x[1])

    if verbose > 0:
        print "...Now extending scheduled observations to fill idle time..."

    for i in range(len(schedule)-1):
        (pulsar, start, stop, optimalUTC, priority) = schedule[i]
        (nextpulsar, nextstart, nextstop, nextoptimalUTC, nextpriority) = schedule[i+1]
        deltanext = nextstart - stop

        # remove old observations
        schedule.remove((pulsar, start, stop, optimalUTC, priority))
        schedule.remove((nextpulsar, nextstart, nextstop, nextoptimalUTC, nextpriority))

        if deltanext > datetime.timedelta(seconds=2):
            if verbose > 0:
                print "  ...extending observations of",pulsar,"and",nextpulsar,"by",deltanext/2

            # modify times:
            stop += deltanext/2
            nextstart -= deltanext/2

        if i == 0:
            if begin is None:
                begin = datetime.datetime.now() - datetime.timedelta(minutes = 2)
            if verbose > 0:
                print "  ...extending observation of",pulsar,"by",start-begin,"to start from beginning of observation time"
            start = begin

        if i == len(schedule): # Note: It's two short at this point since the currently modified obs were removed above!
            if end is not None:
                if verbose > 0:
                    print "  ...extending observation of",nextpulsar,"by",end-stop,"to stop at the end of observation time"
                nextstop = end
            elif deadline is not None:
                if verbose > 0:
                    print "  ...extending observation of",nextpulsar,"by",deadline-stop,"to stop at the deadline"
                nextstop = deadline


        # save modified observations to schedule
        schedule.append((pulsar, start, stop, optimalUTC, priority))
        schedule.append((nextpulsar, nextstart, nextstop, nextoptimalUTC, nextpriority))
        schedule = sorted(schedule, key=lambda x: x[1])


    return schedule


# Print schedule to stdout
def printSchedule(schedule, dropObservationList, timePenalty, dropPenalty, msg):

    print msg
    print "---------------------"
    for (pulsar, start, stop, optimalUTC, priority) in schedule:
        print "pulsar:",pulsar,"\tfrom:", start,"  to:", stop,"  badness:",  determinetimebadness(start,stop,optimalUTC, timePenalty)
    print "---------------------"
    dropped = 0
    for(pulsar, dur, priority) in dropObservationList:
        print "Dropped:", pulsar, dur, priority
        dropped += 1 * int(priority)
    print "---------------------"
    print "Overlap control value (should be zero):",determineoverlap(schedule)
    print "Total time badness:",  determinetotaltimebadness(schedule, timePenalty)
    print "Total overall badness:",  determinetotaltimebadness(schedule, timePenalty) + dropPenalty * dropped
    print "---------------------"


# Call observer scripts for each item in the schedule:
def observe(schedule, observationCmd):

    observerSetupTime = defaultObserverSetupTime
    schedule = sorted(schedule, key=lambda x: x[1])
    for (pulsar, start, stop, optimalUTC, priority) in schedule:
        while datetime.datetime.now() < start - datetime.timedelta(minutes = 1):
            if verbose > 0:
                print "  ...gotta wait! It's", datetime.datetime.now(),"but next observation starts at", start
            delta = start - datetime.datetime.now()
            time.sleep(delta.seconds)
        if verbose > 0:
            print "  ...It's",datetime.datetime.now()," - Starting observation of pulsar", pulsar ,"("+str(datetime.datetime.now()-start)," off)"
        cmd = observationCmd+" -p " +pulsar +" -T "+str((stop-start).seconds / 60 - observerSetupTime)
        if verbose > 1:
            print "  ...calling",cmd
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        print process.communicate()[0]


# Main application
#def main(argv):
def main():
    observationList = []
    observationCmd = defaultObservationCmd
    keepIdle = defaultAllowIdle
    timePenalty = defaultTimePenalty
    idlePenalty = defaultIdlePenalty
    initialRetries = defaultInitialRetries
    dropPenalty = defaultDropPenalty
    outputPath=defaultOutputPath
    inputPath=defaultInputPath
    location=defaultLocation
    logPath=defaultLogPath
    global verbose
    begin = None
    end = None
    deadline = None

    #parser = argparse.ArgumentParser(description="This code will create a"
    #" schedule by randomly shuffling the input list of pulsars to find the"
    #" optimal observing time")
    parser = argparse.ArgumentParser()

    parser.add_argument('-o', '--output-file', dest='outputPath', help="Output file")

    parser.add_argument('-b', '--begin-date', nargs=2, dest='begin', help="Start date, format mm.dd.yy hh:mm")
    parser.add_argument('-e', '--end-date', nargs=2, dest='end', help="End date, format mm.dd.yy hh:mm")
    parser.add_argument('-d', '--deadline-date', nargs=2, dest='deadline', help="Strict end date, format mm.dd.yy hh:mm")
    parser.add_argument('-s', '--site', dest='location', help="Telescope")

    parser.add_argument('-k', '--keep-idle-times', dest='keepIdle', help="Keep idle times(?)")

    parser.add_argument('-I', '--iterations', dest='initialRetries', type=int, help="Number of iterations")
    parser.add_argument('-T', '--penalty-non-optimal', dest='timePenalty', help="Penalty for non-optimal observing time")
    parser.add_argument('-D', '--penalty-drop-pulsar', dest='dropPenalty', type=int, help="Penalty for dropping a pulsar from the schedule", default=500)

    parser.add_argument('-c', '--observing-command', dest='observationCmd', help="Custom observing command")
    parser.add_argument('-i', '--input-schedule', dest='inputPath', help="Input schedule")

    parser.add_argument('-v', '--verbosity', dest='verbose', type=int)
    parser.add_argument('-l', '--log-file', dest='logPath', help="Logfile")

    parser.add_argument('inputList', metavar='INPUT_FILE', nargs=1, help="Input file with a list of pulsars")

    args = parser.parse_args()

    if args.outputPath :
        outputPath = args.outputPath
    if args.inputPath :
        inputPath = args.inputPath
    if args.initialRetries :
        initialRetries = args.initialRetries
    if args.begin :
        begin = dateutil.parser.parse(args.begin[0] + " " + args.begin[1])
    if args.end :
        end = dateutil.parser.parse(args.end[0] + " " + args.end[1])
    if args.deadline :
        deadline = dateutil.parser.parse(args.deadline[0] + " " + args.deadline[1])
    if args.location :
        location = args.location
    if args.keepIdle :
        keepIdle = args.keepIdle
    if args.timePenalty :
        timePenalty = args.timePenalty
    if args.dropPenalty :
        dropPenalty = args.dropPenalty
    if args.observationCmd :
        observationCmd = args.observationCmd
    if args.verbose :
        verbose = args.verbose
    if args.logPath :
        logPath = args.logPath
    inputList = args.inputList[0]

    ## Parse arguments and change settings accordingly:
    #try:
        #opts, args = getopt.getopt(argv, "ho:b:e:d:ki:I:T:D:c:v:s:")
    #except getopt.GetoptError:
        #print "! ERROR--> Could not parse arguments!", os.linesep, "Try 'reducePulsars.py -h' for help!"
        #sys.exit(1)
    #except:
        #raise
    #for opt, arg in opts:
        #if opt == '-h':
            #print "================="
            #print "observePulsars.py"
            #print "================="
            #print "Executes a list of desired observations that are specified in the input file."
            #print "The observations are scheduled in an appropriate sequential order based on"
            #print "visibility. The script will terminate after all observations have finished."
            #print "An optional begin time or timeframe can be specified: "
            #print "No observation will start before the begin time, but it might start later."
            #print "Observations may be scheduled to stop after the specified end time, but with"
            #print "a penalty."
            #print "No observation will take place after the deadline."
            #print "------"
            #print "Usage: "
            #print "observePulsars.py [options] <file_with_pulsars/durations>"
            #print "------"
            #print "Options:"
            #print "-h            --> Display this help"
            #print "-o <path>     --> Output for final schedule"
            #print "-i <path>     --> Input schedule from file (You may add new observations, but this schedule's times are fixed)"
            #print "-I <int>      --> Number of iterations (default 20)"
            #print "-b <datetime> --> Begin time"
            #print "-e <datetime> --> End time (soft)"
            #print "-d <datetime> --> Deadline (strict)"
            #print "-s <string>   --> Telescope site"
            #print "-k            --> Keep idle times"
            #print "-T <int>      --> Penalty for non-optimal timing  (default: 2/min)"
            #print "-D <int>      --> Penalty for dropped observation (default: 500)"
            #print "-c <string>   --> Custom observator command"
            #print "-v <int>      --> Verbose level (0-4), where 4 is a lot (I mean, seriously! Don't do it.)"
            #print "-l <path>     --> Log to path"
            #print "-----------------"
            #sys.exit()
        #elif opt == '-o':
            #outputPath = os.path.expanduser(arg)
        #elif opt == '-i':
            #inputPath = os.path.expanduser(arg)
        #elif opt == '-I':
            #initialRetries = int(arg)
        #elif opt == '-b':
            #begin = dateutil.parser.parse(arg)
            #print "Begin time:",begin
        #elif opt == '-e':
            #end = dateutil.parser.parse(arg)
            #print "End time:",end
        #elif opt == '-d':
            #deadline = dateutil.parser.parse(arg)
            #print "Deadline:",deadline
        #elif opt == '-k':
            #keepIdle = True
        #elif opt == '-T':
            #timePenalty = int(arg)
        #elif opt == '-D':
            #dropPenalty = int(arg)
        #elif opt == '-c':
            #observationCmd = arg
        #elif opt == '-v':
            #verbose = int(arg)
        #elif opt == '-l':
            #logPath = arg
        #elif opt == '-s':
            #location = arg


    # copy stdout to log file
    log = os.path.expanduser(logPath + os.path.sep +"observePulsars."+ str(datetime.datetime.now()) +".log")
    safeMakedirs(logPath, 0755)
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    tee = subprocess.Popen(["tee", log], stdin=subprocess.PIPE)
    os.dup2(tee.stdin.fileno(), sys.stdout.fileno())
    os.dup2(tee.stdin.fileno(), sys.stderr.fileno())

    if verbose > 0:
        print "================="
        print "observePulsars.py"
        print "================="

    if verbose > 0:
        print 'Reading desired observations from', inputList,"...",
    with open(inputList) as f:
        lines = f.readlines()
        for line in lines:
            if not line.startswith('#'):
                observationList.append(line.strip().split())
    if verbose > 0:
        print "done."

    if inputPath != None:
        schedule = []
        if verbose > 0:
            print 'Reading schedule from', inputPath,"...",
        with open(inputPath) as f:
            lines = f.readlines()
            for line in lines:
                if not line.startswith('#'):
                    (pulsar, start, stop, optimalUTC, priority) = line.strip().split("\t")
                    schedule.append((pulsar, dateutil.parser.parse(start), dateutil.parser.parse(stop), dateutil.parser.parse(optimalUTC), int(priority)))
        if verbose > 0:
            print "done."

    if len(observationList) > 0:
        if verbose>0:
            print "Creating schedule..."
        site = sites.get(location)
        schedule = makeSchedule(observationList,site, begin, end,
                                deadline,timePenalty,idlePenalty,dropPenalty,initialRetries)

    # Determine dropped observations
    dropObservationList = list(observationList)
    for (pulsar, start, stop, optimalUTC, priority) in schedule:
        dur = (stop-start).seconds / 60
        for line in dropObservationList:
            (pulsarL, durL, priorityL) = line
            if pulsarL == pulsar and str(dur) == durL and priority == priorityL:
                dropObservationList.remove(line)
                break

    # print intermediate schedule
    if verbose > 1:
        printSchedule(schedule, dropObservationList, timePenalty, dropPenalty,
                      "This is the best schedule (with idle times):")

    if verbose > 1 and not keepIdle:
        plotschedule(begin, end, deadline, schedule, "Best Schedule (with idle"
                     " times)", True, True )

    if not keepIdle:
        if verbose > 0:
            print "Extending observations to fill up idle time..."
        schedule = fillIdleTimes(begin, end, deadline, schedule)

    # print final schedule
    if verbose > 0:
        printSchedule(schedule, dropObservationList, timePenalty, dropPenalty, "This is the final schedule:")
        plotschedule(begin, end, deadline, schedule, "Final Schedule", True,
                     True )

    # write schedule to file
    with open(outputPath, 'w') as f:
        if verbose > 0:
            print "Writing schedule to", outputPath
        f.write("# TADAM Schedule created by observePulsars.py\n")
        f.write("# Pulsar \t Duration \t Start UTC \t Stop UTC \t Optimal UTC \t Priority\t Start LST \t Stop LST\n")
        for (pulsar, start, stop, optimalUTC, priority) in schedule:
            #3 lines inserted by STEFAN
            start_date = matplotlib.dates.date2num(start)
            stop_date = matplotlib.dates.date2num(stop)
            duration = stop_date - start_date
            # '"\t"+str(duration)+' as well as LST inserted by STEFAN
            line = pulsar+"\t"+str(duration)+"\t"+str(start)+"\t"+str(stop)+"\t"+str(optimalUTC)+"\t"+str(priority)+"\t"+site.localSiderialTime(start, returntype="string")+"\t"+site.localSiderialTime(stop, returntype="string")
            f.write(line+"\n")

    # start observation
    for i in range(3):
        print "Observe that schedule now? (y,N)"
        sys.stdout.flush()
        input = raw_input().strip()
        if input == '' or input == 'n' or input == 'N':
            if verbose > 0:
                print "You can load and observe your schedule later with option '-i",outputPath+"'"
            break
        if input == 'y' or input == 'Y':
            if verbose > 0:
                print "Start observing..."
            observe(schedule, os.path.expanduser(observationCmd))


if __name__ == '__main__':
    #main(sys.argv[1:])
    main()

