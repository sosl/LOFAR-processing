The script CreateSched.py reads an input file as created by observePulsars.py to create a schedule file. The format of the input file is:
PSR TINT TZONE: HH:MM TZONE: YYYY-MM-DD HH:MM TYPE
Where:
 * PSR is the pulsar to be observed
 * TINT is integration time in minutes
 * TZONE is time zone. Currently only LST (first occurence) and UTC (second) are accepted.
 * YYYY-MM-DD is the date in YEAR-MONTH-DAY format
 * HH:MM is the time in the specified timezone in format HOUR:MINUTE
 * TYPE is the type of observation. Currently only NORMAL and HIGHRES are accepted. TODO: implement SINGLE for single pulse modes.

The first time infomation is merely to help manual modification of the schedule input file if necessary, e.g., due to unexpected delays.
The second time specification is used by the observing script as the start time of the observation. If that is in the future, then the observing script will wait for that time which can be useful for tracking sources as soon as they rise. If it is in the past, the observation will be either shortened, if the delay exceeds hard tolerance in ObserveGeneric.py, or the obsever will be notified, if the delay exceeds tolerance and observer's email was provided to ObserveGeneric.py.


