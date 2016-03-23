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

        cadence_avg =0

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


"""
<html>
<head>
<title> LOFAR single station metadata </title>
    <link rel="stylesheet" type="text/css" href="css/common.css">
    <script type="text/javascript" src="./tablesorter/jquery.tablesorter.js"></script>
    <script>
        $(document).ready(function()
        {
            $("#psrs").tablesorter();
        }
        );
    </script>
</head>
<body bgcolor=black text="#AFAFAF" link="#928A70" vlink="#706850" marginwidth=0 marginheight=0 topmargin=0 leftmargin=0 onload="document.haslo.haslo.focus()">
<?php

ini_set('display_errors',1); 
error_reporting(E_ALL);


$topdir = "/home/soslowski/public_html/LOFARSS/";
$topdir = "";
$station = "DE601";

/*
if (!file_exists($topdir."data/".$station.'/'.$station.'.db'))
{
  echo 'Creating the per-station DB</br></br>';
  $station_db = new PDO('sqlite:/'.$topdir."data/".$station.'.db');
}// */

echo "trying to open ".$topdir.'data/db/station_db/'.$station.'.db'.'</br>';
$station_db = new PDO('sqlite:'.$topdir.'data/db/station_db/'.$station.'.db');

foreach (glob($topdir."data/db/".$station."/*db") as $file)
{
  $psr = basename($file, '.db');
  $pdo = new PDO('sqlite:'.$file);
  echo 'created pdo for '.$psr.'</br></br>';

  $q = 'SELECT MIN(MJD),MAX(MJD) FROM (
    SELECT mjd_1 as MJD FROM obs
    UNION
    SELECT mjd_2 as MJD FROM obs
    UNION
    SELECT mjd_3 as MJD FROM obs
    UNION
    SELECT mjd_4 as MJD FROM obs)
    WHERE MJD IS NOT ""';
  $stmt = $pdo -> query ($q);
  while ($row = $stmt -> fetch())
  {
    $min_mjd=floatval($row[0]);
    $max_mjd=floatval($row[1]);
  }
  echo "</br>";

  $q = 'SELECT COUNT(*) FROM obs';
  $stmt = $pdo -> query ($q);
  while ($row = $stmt -> fetch())
    $obs_count=floatval($row[0]);

  $time_span=$max_mjd - $min_mjd;

  $q = 'SELECT COUNT(*) FROM (
    SELECT DISTINCT substr(mjd_1,1,5) FROM obs WHERE mjd_1 IS NOT ""
    UNION
    SELECT DISTINCT substr(mjd_2,1,5) FROM obs WHERE mjd_2 IS NOT ""
    UNION
    SELECT DISTINCT substr(mjd_3,1,5) FROM obs WHERE mjd_3 IS NOT ""
    UNION
    SELECT DISTINCT substr(mjd_4,1,5) FROM obs WHERE mjd_4 IS NOT "")';
  $stmt = $pdo -> query ($q);
  while ($row = $stmt -> fetch())
    $days_count=floatval($row[0]);

  $cadence_avg = $time_span / $days_count;

  $q = 'SELECT MIN(TINT),MAX(TINT),AVG(TINT) from (
    SELECT length_1 as TINT FROM obs
    UNION
    SELECT length_2 as TINT FROM obs
    UNION
    SELECT length_3 as TINT FROM obs
    UNION
    SELECT length_4 as TINT FROM obs)
    WHERE TINT IS NOT ""';
  $stmt = $pdo -> query ($q);
  while ($row = $stmt -> fetch())
  {
    $min_tint = floatval($row[0]);
    $max_tint = floatval($row[1]);
    $avg_tint = floatval($row[2]);
  }

  $q = 'SELECT AVG(bw) from (
    SELECT bw_1 as bw FROM obs
    UNION
    SELECT bw_2 as bw FROM obs
    UNION
    SELECT bw_3 as bw FROM obs
    UNION
    SELECT bw_4 as bw FROM obs)
    WHERE bw IS NOT ""';
  $stmt = $pdo -> query ($q);
  while ($row = $stmt -> fetch())
    $avg_bw = floatval($row[0]);

  $q = 'SELECT AVG(relative_elevation) from obs';
  $stmt = $pdo -> query ($q);
  while ($row = $stmt -> fetch())
    $avg_elevation= floatval($row[0]);

  /*
  echo $psr." ".$min_mjd." ".$max_mjd." ".$obs_count." ".$days_count." ".$time_span." ".$cadence_avg." ".round($min_tint)
    ." ".round($max_tint)." ".round($avg_tint)." ".round($avg_bw)." ";
  printf("%.2f\n",$avg_elevation); // */

  $inject = 'INSERT INTO psrs VALUES ("'.$psr.'",'.round($min_mjd).",".round($max_mjd).",".$obs_count.",".$days_count.",".round($time_span/365.*100.)/100..",".round($cadence_avg*10./10.).",".round($min_tint).",".round($max_tint).",".round($avg_tint).",".round($avg_bw).",".(round($avg_elevation*1000.)/1000.).')';

  echo 'will attempt inject: '.$inject."</br></br>";
  $station_db ->exec($inject) or die(print_r($station_db->errorInfo(), true));
  //$injected_rows = $station_db -> exec($inject);

  $pdo = NULL;
}

$station_db = NULL;

?>

</body></html>
"""
