Improvements over the previous parseBBSJonesPSRCHIVE.sh:
- Speed: for long observations (few hours) this script will be faster by a factor of few tens. For shorter observations the difference will be smaller. This was achieved by replacing the most time consuming part of the script with a simple sort and running multiple instances of antennaJones.py simultaneously.
- Portability: No need to modify anything in the script, just setup the MSCORPOL_PYPATH variable.
- Parallelism: You can now run multiple instances of this script. Previously this would have been problematic.
- Robustness: The script will perform some basic checks before commencing processing.
- No parset required.

Drawbacks:
- Needs a seprate add_freq.awk script. This is because it would have been very complex to incorporate the same functionality directly in the script. If you know how to do this then let me (Stefan Oslowski) know!
- Relies on GNU parallel which is often not part of default installation. Many distribution provide packages though and compilation from source is quite easy as well.

Prerequisities:
I   mscorpol
II  psrchive
III psrcat 
IV  GNU parallel
V   You need to know the sub-band width and band filter. For HBA observations these are 195.3125 and HBA_110_190, respectively.

To use the new calibration script:
0. Copy parseBBSJonesPSRCHIVE.sh somewhere in your PATH (optional, you can always specify full path to the script when running it
1. Set the (environment) variable MSCORPOL_PYPATH to point to your mscorpol installation. This is where pypath pointed to in the original parseBBSJonesPSRCHIVE.sh script.
2. Copy add_freq.awk to MSCORPOL_PYPATH
3. Run parseBBSJonesPSRCHIVE.sh ! To get a usage example run "./parseBBSJonesPSRCHIVE.sh" or "./parseBBSJonesPSRCHIVE.sh -h"
4. Copy the antennaJones.py to MSCORPOL_PYPATH. This version should only differ slightly. The version I provide work well for sources with negative declination

The script was verified to produce the same result as the original for a single station observation.
The inversion functionality was not tested at all.

Changelog:
30.06.2015: Updated the example usage (Thanks to Aris N. for spotting the out-of-date example!)
11.07.2015: Will now work correctly for sources with negative declination. Need to use the modified antennaJones.py
Next changelogs via git hist
