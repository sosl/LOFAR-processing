#!/usr/bin/python

from argparse import ArgumentParser
import sqlite3 as sql
import glob
import os
"""
This script populates an sqlite3 database for a LOFAR station.
It accumulates metadata for all the pulsars ever observed with the given
station.
You need to provide one or more stations to handle and a path DBTOPPATH to where the
databases reside. 
The code expects to find pulsar databases in DBTOPPATH/db/STATION/ and it
will produce output in DBTOPPATH/db/station_db/STATION.db
"""

parser = ArgumentParser();
parser.add_argument("-s", "--station", dest="Stations", nargs="+",
        help="Populate databases for station[s]")
parser.add_argument("-v", "--verbose", dest="Verbose", action="store_true",
        help="Turn on verbose output")
parser.add_argument("-P", "--db-top-dir", dest="dbTopPath",
        help="Path to top directory for databases", default="./")

args = parser.parse_args()

dbTopPath = args.dbTopPath

# Here I prepare all the queries to be used later:
# find MJD range:
MJDQuery = 'SELECT MIN(MJD),MAX(MJD) FROM ('\
        +'SELECT mjd_1 as MJD FROM obs UNION '\
        +'SELECT mjd_2 as MJD FROM obs UNION '\
        +'SELECT mjd_3 as MJD FROM obs UNION '\
        +'SELECT mjd_4 as MJD FROM obs) WHERE MJD IS NOT ""'
# find number of observations:
countQuery = 'SELECT COUNT(*) FROM obs'
# find number of days on which the pulsar was observed:
daysQuery = 'SELECT COUNT(*) FROM ('\
        +'SELECT DISTINCT substr(mjd_1,1,5) FROM obs WHERE mjd_1 IS NOT "" '\
        +' UNION '\
        +'SELECT DISTINCT substr(mjd_2,1,5) FROM obs WHERE mjd_2 IS NOT "" '\
        +' UNION '\
        +'SELECT DISTINCT substr(mjd_3,1,5) FROM obs WHERE mjd_3 IS NOT "" '\
        +' UNION '\
        +'SELECT DISTINCT substr(mjd_4,1,5) FROM obs WHERE mjd_4 IS NOT "")'
# find the min, max, and avg integration time
TintQuery = 'SELECT MIN(TINT),MAX(TINT),AVG(TINT) from ( '\
        +'SELECT length_1 as TINT FROM obs UNION '\
        +'SELECT length_2 as TINT FROM obs UNION '\
        +'SELECT length_3 as TINT FROM obs UNION '\
        +'SELECT length_4 as TINT FROM obs) '\
        +'WHERE TINT IS NOT ""'
# find avg bandwidth:
BWQuery = 'SELECT AVG(bw) from ( '\
        +'SELECT bw_1 as bw FROM obs UNION '\
        +'SELECT bw_2 as bw FROM obs UNION '\
        +'SELECT bw_3 as bw FROM obs UNION '\
        +'SELECT bw_4 as bw FROM obs) WHERE bw IS NOT ""'
# find the average relative elevation
elevationQuery = 'SELECT AVG(relative_elevation) from obs'


for station in args.Stations:
    psrDBs = glob.glob(dbTopPath + "/db/"+station+"/*db")
    # list of values for insertion:
    values = []
    for psrDB in psrDBs:
        if args.Verbose:
            print "Trying to connect to psr DB: \n" + psrDB
        psrConnection = sql.connect(psrDB)
        psrCurrent = psrConnection.cursor()
        if args.Verbose:
            print "Connected to the pulsar DB"

        # get PSR name from the psrDB name:
        psr = os.path.basename(os.path.splitext(psrDB)[0])
        if args.Verbose:
            print "This database is for pulsar: " + psr

        # get MJD min / max and round to two digits:
        psrCurrent.execute(MJDQuery)
        MJD_min, MJD_max = (round(MJD, 2) for MJD in psrCurrent.fetchone())

        # get count
        psrCurrent.execute(countQuery)
        count = psrCurrent.fetchone()[0]

        # get days count
        psrCurrent.execute(daysQuery)
        days = psrCurrent.fetchone()[0]

        # we can now calculate time span and cadence
        time_span = (MJD_max - MJD_min) / 365.
        cadence = round(time_span / days, 1)
        time_span = round(time_span, 2)

        # get the min / max / avg integration time in seconds
        psrCurrent.execute(TintQuery)
        Tint_min, Tint_max, Tint_avg = psrCurrent.fetchone()

        # get the average bandwidth
        psrCurrent.execute(BWQuery)
        bw = round(psrCurrent.fetchone()[0], 2)

        # get the average elevation
        psrCurrent.execute(elevationQuery)
        avg_elevation = round(psrCurrent.fetchone()[0], 3)

        if args.Verbose:
            print "Retrieved all needed values"

        values.append((psr, MJD_min, MJD_max, count, days, time_span, cadence, Tint_min, Tint_max, Tint_avg, bw, avg_elevation))
        psrConnection.close()

    station = station.upper()
    dbPath = dbTopPath + "/db/station_db/" + station + ".db"
    if args.Verbose:
        print "Trying to open: " + dbPath
    stationConnection = sql.connect(dbPath)
    stationCurrent = stationConnection.cursor()
    if args.Verbose:
        print "Connected to the station DB"

    stationCurrent.executemany('INSERT INTO psrs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', values)
    stationConnection.commit()
    stationConnection.close()
