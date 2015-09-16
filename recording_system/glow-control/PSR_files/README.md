## Examples
The files 2015-09-15_DE601.list.example and 2015-09-15_DE601.list.sched.example show the format of input file and the schedule create with CreateSched.py.
The command used was:
```
python CreateSched.py 2015-09-15_DE601.list -S -R C1 C2 C2 -v -P "ssh glowSID ssh LSTATIONc" -p
```
Naturally, the file would have to be renamed (strip .example) for the exact command to work.
