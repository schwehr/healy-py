#!/usr/bin/env python
__author__    = 'Kurt Schwehr'
__version__   = '$Revision: 4799 $'.split()[1]
__revision__  = __version__ # For pylint
__date__ = '$Date: 2006-09-25 11:09:02 -0400 (Mon, 25 Sep 2006) $'.split()[1]
__copyright__ = '2009'

__doc__ ='''
Parse data strings in the Healy science reports.  Try to do most of the
work with regular expressions.  Note that some of these strings are
not valid nmea (specifically "DERIV")

Note that these regular expressions (regex) might not match the NMEA standard.  They will
hopefully be good enough to parse everything that Healy generates.




@requires: U{Python<http://python.org/>} >= 2.5
@requires: U{sqlite3<>}

@undocumented: __doc__
@since: 2009-May-14
@status: under development
@organization: U{CCOM<http://ccom.unh.edu/>}

@see: http://walrus.wr.usgs.gov/infobank/h/h208ar/meta/HLY0806_Sensors.pdf
@see: http://gpsd.berlios.de/NMEA.txt

@todo: GPVTG
@todo: Call-Sign
@todo: PSATC
@todo: HEROT
@todo: IBS-WayPoints
@todo: ISUSV3-SERIAL
@todo: PSXTA
@todo: GPGSV
@todo: PRDID
@todo: GPRMC
@todo: PTNLDG
@todo: GPMSS
@todo: NVWPL
@todo: HEXDR
@todo: NVXDR
@todo: GPGSA
@todo: handle "NO DATA"
@todo: http://yachtelectronics.blogspot.com/2011/02/srt-proprietary-ais-commands.html
@todo: John Helly reported this from the Melville EM122 1298419231.321 $SDDBT,17960.21,f,5474.27,M,2993.37,F*3E

'''

import re
import os
import sys
import sqlite3

import os, sys
import mailbox
#from dateutil.parser import parse
#import dateutil.parser
#from dateutil.relativedelta import relativedelta
import datetime
import commands # Execute shell commands via os.popen() and return status, output.
import time


regex_dict = {}
'''
regular expressions to match against the Healy Support emails
'''

##############################
# FSR - AIS Frame Summary Report

# Talker likely AR
fsr_nmea_regex_str = r'''[$](?P<talker>[A-Z][A-Z])(?P<sentence>FSR),
(?P<station>[a-zA-Z0-9_-]*),
(?P<uscg_date>(?P<year>\d\d\d\d)(?P<month>\d\d)(?P<day>\d\d))?
(?P<time_utc>(?P<hours>\d\d)(?P<minutes>\d\d)(?P<seconds>\d\d)(?P<decimal_sec>\.\d\d)?),
(?P<channel>[ABXY]),
(?P<slots_rx_last_frame>\d+),
(?P<slots_tx_last_frame>\d+),
(?P<crc_errors_last_frame>\d+)?,
(?P<ext_slots_res_cur_frame>\d+)?,
(?P<local_slots_res_cur_frame>\d+)?,
(?P<avg_noise_dbm>-?\d+)?,
(?P<rx_10dbm_over_avg_noise>\d+)?
\*(?P<checksum>[0-9A-F][0-9A-F])'''
'''
USCG violates the time standard by including yyyymmdd and droping the .ss
XY for channel is not valid, but used by the USCG NAIS system.
'''
regex_dict['fsr'] = re.compile(fsr_nmea_regex_str, re.VERBOSE)
##############################
# DBT - Echosounder depth

dbt_nmea_regex_str = r'''[$](?P<talker>SD)(?P<sentence>DBT),
(?P<depth_ft>\d+\.\d+),f,
(?P<depth_m>\d+\.\d+),M,
(?P<depth_fath>\d+\.\d+),F
\*(?P<checksum>[0-9A-F][0-9A-F])'''
'''
depth in feet
depth in meters
depth in fathoms
'''

regex_dict['dbt'] = re.compile(dbt_nmea_regex_str, re.VERBOSE)

##############################
# PAT - Ashtech Attitude

# FIX: is time really GMT or is it UTC?
ashtech_attitude_nmea_regex_str = r'''
[$](?P<talker>GP)(?P<sentence>PAT),
(?P<time_gmt>(?P<hours>\d\d)(?P<minutes>\d\d)(?P<seconds>\d\d\.\d\d)),
(?P<lat>(?P<lat_deg>\d\d)(?P<lat_min>\d\d\.\d{5})),
(?P<lat_hemi>[NS]),
(?P<lon>(?P<lon_deg>\d{3})(?P<lon_min>\d\d\.\d{5})),
(?P<lon_hemi>[EW]),
(?P<altitude_m>\d{5}\.\d\d),
(?P<heading>\d*\.\d*)?,
(?P<pitch>[+-]?\d*\.\d\d)?,
(?P<roll>[+-]?\d*\.\d\d)?,
(?P<attitude_phase_rms_m>\d+\.\d{4})?,
(?P<attitude_baseline_rms_m>\d+\.\d{4})?,
(?P<attitude_reset_flag>)[01]?
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''1 SCS logged Date 04/15/2007 mm/dd/year
2 SCS logged Time GMT 00:00:05.490 hh:mm:ss.sss
3 NMEA header $GPPAT ASCII text
4 GPS time at position GMT 000005.00 hhmmss.ss
5 Latitude 5830.44859 ddmm.mmmmm
6 North (N) or South(S) N ASCII character
7 Longitude 17012.63099 dddmm.mmmmm
8 East (E) or West (W) W ASCII character
9 Altitude 00030.23 Meters
10 Heading 344.3431 Degrees
11 Pitch 000.22 Degrees
12 Roll -000.07 degrees
13 Attitude phase measurement rms error, MRMS 0.0014 meters
14 Attitude baseline length rms error, BRMS 0.0077 meters
15 Attitude reset flag (0:good attitude, 1:rough estimate or bad attitude) 0 ASCII integer
16 Check sum *41 ASCII text'''

regex_dict['pat'] = re.compile(ashtech_attitude_nmea_regex_str, re.VERBOSE)



########################################
# GGA - GPS

# FIX: what is the range of gps_quality?

gga_nmea_regex_str = r'''[$](?P<talker>[A-Z][A-Z])(?P<sentence>GGA),
(?P<time_utc>(?P<hour>\d\d)(?P<minute>\d\d)(?P<second>\d\d\.\d*))?,
(?P<lat>(?P<lat_deg>\d\d)(?P<lat_min>\d\d\.\d*))?,
(?P<lat_hemi>[NS])?,
(?P<lon>(?P<lon_deg>\d{3})(?P<lon_min>\d\d\.\d*))?,
(?P<lon_hemi>[EW])?,
(?P<gps_quality>\d+)?,
(?P<satellites>\d+)?,
(?P<hdop>\d+\.\d+)?,
(?P<antenna_height>[+-]?\d+\.\d+)?,
(?P<antenna_height_units>M)?,
(?P<geoidal_height>[+-]?\d+\.\d+)?,
(?P<geoidal_height_units>M)?,
(?P<differential_ref_station>[A-Z0-9.]*),
(?P<differential_age_sec>\d+)?
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''1 SCS logged Date 04/15/2007 mm/dd/year
2 SCS logged Time GMT 00:00:04.333 hh:mm:ss.sss
3 NMEA header $GPGGA ASCII text
4 GPS time at position GMT 000004.00 hhmmss.ss  NOTE: this is Not GMT, but UTC! -kurt 5/2009
5 Latitude 5830.44527 ddmm.mmmmm
6 North (N) or South(S) N ASCII character
7 Longitude 17012.62914 dddmm.mmmmm
8 East (E) or West (W) W ASCII character
9 GPS Quality: 1 = GPS 2=DGPS 1 ASCII integer
10 Number of GPS Satellites Used 13
11 HDOP (horizontal dilution of precision) 0.7
12 Antenna height 20.76 meters
13 M for Meters M ASCII character
14 Geoidal Height 9.47 meters
15 M for Meters M ASCII character
16 Differential reference station ID (no data in sample string)
17 Checksum *75 ASCCII text'''

regex_dict['gga'] = re.compile(gga_nmea_regex_str, re.VERBOSE)

########################################
# GLL Geographic Position - Latitude/Longitude

gll_nmea_regex_str = r'''[$!](?P<talker>[A-Z][A-Z])(?P<sentence>GLL),
(?P<lat>(?P<lat_deg>\d\d)(?P<lat_min>\d\d\.\d*))?,
(?P<lat_hemi>[NS])?,
(?P<lon>(?P<lon_deg>\d{3})(?P<lon_min>\d\d\.\d*))?,
(?P<lon_hemi>[EW])?,
(?P<time_utc>(?P<hour>\d\d)(?P<minute>\d\d)(?P<second>\d\d\.\d*))?,
(?P<valid_flag>[AV])?
(,(?P<mode>[ADE]))?
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''1 SCS logged Date 04/15/2007 mm/dd/year
2 SCS logged Time GMT 00:00:05.255 hh:mm:ss.sss
3 NMEA header $GPGLL ASCI text
4 Latitude 5830.44859 ddmm.mmmmm
5 North or South N ASCII character
6 Longitude 17012.63099 dddmm.mmmmm
7 East or West W ASCII character
8 GMT of Position 000005.00 hhmmss.ss
9 Status of data (A=valid) A ASCII character, V for invalid
10 ??? A   A=Autonomous, D=DGPS, E=DR (Only present in NMEA version 3.00)
11 Checksum *74 ASCII text'''

regex_dict['gll'] = re.compile(gll_nmea_regex_str, re.VERBOSE)


########################################
# HDT - Heading

hdt_nmea_regex_str = r'''[$!](?P<talker>(GP|HE|IN))(?P<sentence>HDT),
(?P<heading_deg>\d*\.\d*)?,
(?P<mode>[TM])?
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''1 SCS logged Date 04/15/2007 mm/dd/year
2 SCS logged Time GMT 00:00:05.505 hh:mm:ss.sss
3 NMEA header $GPHDT ASCII text
4 Heading 344.343 Degrees
5 True(T) or Magnetic(M) T ASCII character
6 Checksum *32 ASCII text'''

regex_dict['hdt'] = re.compile(hdt_nmea_regex_str, re.VERBOSE)

########################################
# Flourometer

fla_nmea_regex_str = r'''[$!](?P<talker>PS)(?P<sentence>FLA),
(?P<flurometer>\d*\.\d*),
(?P<flurometer_raw>\d*\.\d*),
(?P<turbidity>\d*\.\d*)?,
(?P<turbitity_raw>\d*\.\d*)?
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''3 NMEA header $PSFLA ASCII text
4 Flurometer 0.330 Ug/l
5 Flrometer, RAW 0.033 volts
6 Turbidity 0.000 NTU
7 Turbidity, RAW 0.010 volts
8 Check sum *49 ASCII text'''

regex_dict['fla'] = re.compile(fla_nmea_regex_str, re.VERBOSE)

########################################
# GST - pseudorange error stats

gst_nmea_regex_str = r'''[$!](?P<talker>[A-Z]{2})(?P<sentence>GST),
(?P<time_utc>(?P<hours>\d\d)(?P<minutes>\d\d)(?P<seconds>\d\d\.\d*)),
(?P<stddev_ranges>\d*\.\d*)?,
(?P<stddev_m_major_axis>\d*\.\d*),
(?P<stddev_m_minor_axis>\d*\.\d*),
(?P<orientation_major_axis>\d*\.\d*),
(?P<stddev_m_lat_error>\d*\.\d*),
(?P<stddev_m_lon_error>\d*\.\d*),
(?P<stddev_m_alt_error>\d*\.\d*)
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''NMEA header $INGST ASCII text
4 GPS time at position UTC??? 000004.737 hhmmss.sss
5
6 Smjr.smjr 0.6 meters
7 Smnr.smnr 0.4 meters
8 000.0 22.3
9 l.l 0.4 meters
10 y.y 0.6 meters
11 Standard deviation of altitude (a.a) 0.8 meters
12 Checksum *65 ACII text'''
regex_dict['gst'] = re.compile(gst_nmea_regex_str, re.VERBOSE)

########################################

rot_nmea_regex_str = r'''[$!](?P<talker>IN)(?P<sentence>ROT),
(?P<rate_of_turn>[+-]?\d*),
(?P<valid>[AV])
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''$--ROT,x.x,A*hh<CR><LF>
| |
| +----------------------Status: A = Data valid
+-------------------------Rate of turn, degrees/minute, "-" = bow turns to port'''

regex_dict['rot'] = re.compile(rot_nmea_regex_str, re.VERBOSE)


########################################

zda_nmea_regex_str = r'''[$!](?P<talker>[A-Z][A-Z])(?P<sentence>ZDA),
(?P<time_utc>(?P<hours>\d\d)(?P<minutes>\d\d)(?P<seconds>\d\d\.\d\d*))?,
(?P<day>\d\d)?,
(?P<month>\d\d)?,
(?P<year>\d{4})?,
(?P<zone_hrs>[+-]?(\d\d))?,
(?P<zone_min>(\d\d))?,?
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''
$--ZDA,hhmmss.ss,xx,xx,xxxx,xx,xx*hh<CR><LF>
| | | | | |
| | | | | +--Local zone minutes description, same sign as local hours
| | | | +-----Local zone description [1], 00 to +-13 hrs
| | | +---------Year
| | +-------------Month, 01 to 12
| +----------------Day , 01 to 31
+------------------------UTC'''

regex_dict['zda'] = re.compile(zda_nmea_regex_str, re.VERBOSE)

########################################
# CTR - Multibeam Center Beam Depth


ctr_nmea_regex_str = r'''[$!](?P<talker>[A-Z][A-Z])(?P<sentence>CTR),
(?P<year>\d{4}),
(?P<month>\d{1,2}),
(?P<day>\d{1,2}),
(?P<time>(?P<hour>\d{1,2}):(?P<min>\d{1,2}):(?P<sec>\d{1,2}\.\d*)),
(?P<lat>[+-]?\d{1,2}\.\d*),
(?P<lon>[+-]?\d{1,3}\d\.\d*),
(?P<depth_m>\d*\.\d*),
(?P<num_beams>\d+)
\*(?P<checksum>[0-9A-F][0-9A-F])'''
'''NMEA header $SBCTR ASCII text
4 Seabeam Date 2007, Year
5 Seabeam Date 4 month
6 Seabeam Date 14 day
7 Seabeam Time 18:24:38.734 hh:mm:ss.sss
8 Latitude 58.119193 Degrees
9 Longitude -169.839452 Degrees
10 Depth 70.92 meters
11 Number of Beams 60
12 Check sum *00 ASCII text'''

regex_dict['ctr'] = re.compile(ctr_nmea_regex_str, re.VERBOSE)

########################################
# MEA - Meteorological Sensors

me_nmea_regex_str = r'''[$](?P<talker>[A-Z][A-Z])(?P<sentence>ME[AB]),
(?P<air_temp_c>[+-]?\d*\.\d*),
(?P<rel_humid>\d{0,3}\.\d*),
(?P<barometric_pressure_mb>\d*.\d*),
(?P<precip_mm>\d*\.\d*)?
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''NMEA header $PSMEA ASCII text
4 Air Temperature -6.29 Celsius
5 Relative Humidity 83.89 %
6 Barometric Pressure 1018.45 milibars
7 Precipitation, total accumulation 14.17 milimeters
8 Check sum *5C ASCII text'''

regex_dict['me'] = re.compile(me_nmea_regex_str, re.VERBOSE)

########################################
# STA - Sea Surface Temp2

sta_nmea_regex_str = r'''
[!$](?P<talker>[A-Z][A-Z])(?P<sentence>STA),
(?P<sea_temp_c>[+-]?[0-9]*\.[0-9]*),
(?P<sea_temp_raw_voltage>[0-9]*\.[0-9]*)
\*(?P<checksum>[0-9A-F][0-9A-F])'''
'''
1 SCS logged Date 03/13/2008 mm/dd/year
2 SCS logged Time GMT 05:46:40.402 hh:mm:ss.sss
3 NMEA header $PSSTA ASCII text
4 Surface temperature (Sea Chest) 2.039 Celsius
5 Temperature, RAW 2945.900 volts
6 Check sum *7E ASCII text
'''
regex_dict['sta'] = re.compile(sta_nmea_regex_str, re.VERBOSE)

########################################
# Flow Meter

fm_nmea_regex_str = r'''
[!$](?P<talker>[A-Z][A-Z])(?P<sentence>FM[AB]),
(?P<flow_liters_per_minute>[+-]?[0-9]*\.[0-9]*),
(?P<flow_raw_freq>[0-9]*\.[0-9]*)
\*(?P<checksum>[0-9A-F][0-9A-F])'''
'''
Flow Meter

NMEA header $PSFMA ASCII text
4 Flow meter 2.51 Liters/minute
5 Flow meter, RAW 38.000 frequency
6 Check sum *44 ASCII text
'''
regex_dict['fm'] = re.compile(fm_nmea_regex_str, re.VERBOSE)

########################################
# OXA - Oxygen

oxa_nmea_regex_str = r'''[$!](?P<talker>[A-Z][A-Z])(?P<sentence>OXA),
(?P<oxygen>\d*\.\d*)?,
(?P<oxygen_raw>\d*\.\d*)?,
(?P<oxygen_temp_c>[+-]?\d*.\d*)?,
(?P<oxygen_temp_raw>[+-]?\d*\.\d*)?
\*(?P<checksum>[0-9A-F][0-9A-F])'''
'''
NMEA header $PSOXA ASCII text
4 Oxygen 7.265 ml/l
5 Oxygen, RAW 2.922
6 Oxygen Temperature 2.576 Celsius
7 Oxygen Temperature, Raw 2.576 volts
8 Check sum *58 ASCII text
'''
regex_dict['oxa'] = re.compile(oxa_nmea_regex_str, re.VERBOSE)

########################################
# VTG - Course made good and speed over gound

vtg_nmea_regex_str = r'''[$!](?P<talker>[A-Z]{2})(?P<sentence>VTG),
(?P<track_deg_true>\d*\.\d*),
(?P<true>T),
(?P<track_deg_mag>\d*\.\d*)?,
(?P<mag>M),
(?P<speed_knots>\d*\.\d*),
(?P<knots>N),
(?P<speed_kph>\d*\.\d*),
(?P<kph>K)
\*(?P<checksum>[0-9A-F][0-9A-F])'''
'''
         1  2  3  4  5	6  7  8 9   10
         |  |  |  |  |	|  |  | |   |
 $--VTG,x.x,T,x.x,M,x.x,N,x.x,K,m,*hh<CR><LF>

 Field Number:
  1) Track Degrees
  2) T = True
  3) Track Degrees
  4) M = Magnetic
  5) Speed Knots
  6) N = Knots
  7) Speed Kilometers Per Hour
  8) K = Kilometers Per Hour
  9) FAA mode indicator (NMEA 2.3 and later)
  10) Checksum

Note: in some older versions of NMEA 0183, the sentence looks like this:

         1  2  3   4  5
         |  |  |   |  |
 $--VTG,x.x,x,x.x,x.x,*hh<CR><LF>

 Field Number:
  1) True course over ground (degrees) 000 to 359
  2) Magnetic course over ground 000 to 359
  3) Speed over ground (knots) 00.0 to 99.9
  4) Speed over ground (kilometers) 00.0 to 99.9
  5) Checksum'''

regex_dict['vtg'] = re.compile(vtg_nmea_regex_str, re.VERBOSE)

########################################
# SHR - pitch and roll

shr_nmea_regex_str = r'''[$!](?P<talker>[A-Z][A-Z])(?P<sentence>SHR),
(?P<time_utc>(?P<hours>\d\d)(?P<minutes>\d\d)(?P<seconds>\d\d\.\d*)),
(?P<heading_deg>\d*.\d*),
(?P<heading_type>T),
(?P<roll_deg>[+-]?\d*\.\d*),
(?P<pitch_deg>[+-]?\d*\.\d*),
(?P<heave_deg>[+-]?\d*\.\d*),
(?P<roll_accuracy_deg>[+-]?\d*\.\d*),
(?P<pitch_accuracy_deg>[+-]?\d*\.\d*),
(?P<heave_accuracy_deg>[+-]?\d*\.\d*),
(?P<heading_accuracy>[0-2]),
(?P<imu_status>[01])
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''NMEA header $PASHR ASCII text
4 Time GMT 000004.737 hhmmss.sss
5 Heading 344.20 heading
6 True T ASCII character
7 Roll -0.24 Degrees
8 Pitch 0.10 Degrees
9 Heave -0.02 Degrees
10 Accuracy roll 0.017 Degrees
11 Accuracy pitch 0.017 Degrees
12 Accuracy heading 0.011 Degrees  # heave? -kurt 5/2009
13 Accuracy of heading 0-no aiding, 1-GPS
2= GPS & GAMS 2 ASCII integer
14 IMU 0= out 1= satisfactory 1 ASCII character
15 Check Sum *10 ASCI text'''

regex_dict['shr'] = re.compile(shr_nmea_regex_str, re.VERBOSE)

########################################
# Transducer measurement

xdr_nmea_regex_str_broken = r'''[$!](?P<talker>[A-Z]{2})(?P<sentence>XDR),
(?P<transducer_type>[A-Z]),
(?P<measurement_data>\d*(\.\d*)?),
(?P<units>[A-Z]+)?,
(?P<transducer_id>[A-Z]+)
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''

        1 2   3 4			    n
        | |   | |            |
 $--XDR,a,x.x,a,c--c, ..... *hh<CR><LF>

 Field Number:
  1) Transducer Type
  2) Measurement Data
  3) Units of measurement
  4) Name of transducer
  x) More of the same
  n) Checksum
'''

# FIX: what to do about xdr???
#regex_dict['xdr'] = re.compile(xdr_nmea_regex_str, re.VERBOSE)

########################################
# TSA - Thermosalinograph / Fluorometer

tsa_nmea_regex_str = r'''[$!](?P<talker>[A-Z]{2})(?P<sentence>TSA),
(?P<temp_c>[+-]?\d*\.\d*)?,
(?P<conductivity>\d*\.\d*)?,
(?P<salinity_psu>\d*\.\d*)?,
(?P<sound_vel_mps>\d*\.\d*)?
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''NMEA header $PSTSA ASCII text
4 Temperature 2.565 Celsius
5 Conductivity 28.4522 millisiemens/cm
6 Salinity 31.526 PSU
7 Sound Velocity 1456.01 Meters per Second (m/s)
8 Check sum *7E ASCII text'''

regex_dict['tsa'] = re.compile(tsa_nmea_regex_str, re.VERBOSE)


########################################
# WD[A-C] - Wind

wd_nmea_regex_str = r'''[$!](?P<talker>[A-Z]{2})(?P<sentence>WD[A-C]),
(?P<wind_dir_rel_deg>\d*\.\d*),
(?P<wind_speed_rel_mps>\d*\.\d*),
(?P<wind_dir_true_deg>\d*\.\d*),
(?P<wind_speed_true_mps>\d*\.\d*)
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''NMEA header $PSWDA ASCII text
4 Relative Wind Direction 52.45 degrees
5 Relative Wind Speed 13.92 m/s
6 True Wind Direction 341.17 degrees
7 True Wind Speed 14.81 m/s
8 Check sum *62 ASCII text'''

regex_dict['wd'] = re.compile(wd_nmea_regex_str, re.VERBOSE)


########################################
# Wind-T

deriv_wind_side_regex_str = r'''(?P<wind_side>(?P<side>Stbd|Port)Wind-T):::
(?P<date>(?P<month>\d\d)/(?P<day>\d\d)/(?P<year>\d{4})),
(?P<time>(?P<hour>\d\d):(?P<min>\d\d):(?P<sec>\d\d\.\d*)),
\$DERIV,
(?P<wind_speed_kts>\d*(\.\d*)?),
(?P<wind_dir_deg>\d+(\.\d*)?),
(?P<wind_dir_rel_deg>\d+(\.\d*)?),
(?P<wind_speed_rel_kts>\d*(\.\d*)?),
(?P<sog_kts>\d*(\.\d*)?),
(?P<cog_deg>\d*(\.\d*)?),
(?P<heading>\d*(\.\d*)?),'''

'''1 SCS logged Date 04/15/2007 mm/dd/year
2 SCS logged Time GMT 00:00:07.396 hh:mm:ss.sss
3 NMEA header $DERIV ASCII text
4 Wind Speed derived 19.99 knots
5 Wind Directions derived 13.31 degrees
6 Wind Speed relative 31.4 knots
7 Wind Direction relative 18 direction
8 Speed over ground (pos mv) 12.4 knots
9 Course over ground (pos mv) 344.1 Degrees
10 Heading (pos mv) 344.2 degrees'''

regex_dict['wind'] = re.compile(deriv_wind_side_regex_str, re.VERBOSE)

########################################
deriv_temp_regex_str= r'''(?P<sentence>(?P<prefix>[-0-9A-Za-z]*)Air([-])?Temp-F):::
(?P<date>(?P<month>\d\d)/(?P<day>\d\d)/(?P<year>\d{4})),
(?P<time>(?P<hour>\d\d):(?P<min>\d\d):(?P<sec>\d\d\.\d*)),
\$DERIV,
(?P<air_temp_f>[+-]?\d*(\.\d*)?),
(?P<air_temp_c>[+-]?\d*(\.\d*)?),'''

regex_dict['temp'] = re.compile(deriv_temp_regex_str, re.VERBOSE)


########################################
#SAMOS
#
# Shipboard Automated Meteorological and Oceanographic Systems
#   Data formatted to be sent to the U.S. Research Vessel Surface
#   Meteorology Data Assembly Center (DAC).

samos_regex_str = r'''(?P<samos_prefix>(?P<sentence>SAMOS)-(?P<variable>(?P<sensor>[A-Z]{2})(?P<sensor_id>\d+)?)):::
(?P<date>(?P<month>\d\d)/(?P<day>\d\d)/(?P<year>\d{4})),
(?P<time>(?P<hour>\d\d):(?P<min>\d\d):(?P<sec>\d\d\.\d*)),
\$DERIV,
(?P<mean>[+-]?\d*(\.\d*)?),
(?P<last_value>[+-]?\d*(\.\d*)?),
(?P<sum>[+-]?\d*(\.\d*)?(E-\d+)?)?,
((?P<stddev_maybe>[+-]?\d*\.\d*),)?
(?P<n>\d+),
'''
regex_dict['samos'] = re.compile(samos_regex_str, re.VERBOSE)

########################################
# NOAA Barometer - DERV SAMOS style
noaa_baro_regex_str = r'''(?P<sentence>NOAA-Baro):::
(?P<date>(?P<month>\d\d)/(?P<day>\d\d)/(?P<year>\d{4})),
(?P<time>(?P<hour>\d\d):(?P<min>\d\d):(?P<sec>\d\d\.\d*)),
\$DERIV,
(?P<mean>\d*(\.\d*)?),
(?P<last_value>\d*(\.\d*)?),
(?P<sum>[+-]?\d*(\.\d*)?),
(?P<n>\d+),'''

regex_dict['noaa_baro'] = re.compile(noaa_baro_regex_str, re.VERBOSE)

########################################
# NOAA Sea Surface Temp - DERV SAMOS style
noaa_sst_regex_str = r'''(?P<sentence>NOAA-SST):::
(?P<date>(?P<month>\d\d)/(?P<day>\d\d)/(?P<year>\d{4})),
(?P<time>(?P<hour>\d\d):(?P<min>\d\d):(?P<sec>\d\d\.\d*)),
\$DERIV,
(?P<sst_mean>[+-]?\d*(\.\d*)?),
(?P<sst_last_value>[+-]?\d*(\.\d*)?),
(?P<sum>[+-]?\d*(\.\d*)?),
(?P<n>\d+),'''

regex_dict['noaa_sst'] = re.compile(noaa_sst_regex_str, re.VERBOSE)


########################################
# Knudsen echo sounder

ais_regex_str = r'''[!](?P<talker>AI)(?P<sentence>VDM),'''
regex_dict['ais'] = re.compile(ais_regex_str, re.VERBOSE)

########################################
# Knudsen echo sounder

pkel99_regex_str = r'''[$](?P<talker>PKEL)(?P<sentence>99),
([-]+|(?P<record_num>\d+)),
(?P<date>(?P<day>\d\d)(?P<mon>\d\d)(?P<year>\d\d\d\d)),
(?P<time>(?P<hour>\d\d)(?P<min>\d\d)(?P<sec>\d\d\.\d*)),
(?P<unknown1>\d+),
(?P<hf_hdr>HF),
(?P<hf_depth_to_surface>\d*\.\d*),
(?P<hf_draft>\d*(\.\d*)?),
(?P<unknown2>[+-]?\d*\.\d*),
(?P<lf_hdr>LF),
(?P<lf_depth_to_surface>\d*\.\d*),
(?P<lf_depth_valid_flag>[01]),
(?P<unknown3>[+-]?\d*\.\d*),
(?P<sound_speed>\d*(\.\d*)?),\s*
(?P<unknown4>[+-]?\d+(\.\d*)?)\s*,
\s*(?P<unknown5>[+-]?\d+(\.\d*)?)\s*,
(?P<lat>(?P<lat_deg>\d{1,2})\s*(?P<lat_min>\d{1,2}\.\d*)(?P<lat_hemisphere>[NS])),
(?P<lon>(?P<lon_deg>\d{1,3})\s*(?P<lon_min>\d{1,2}\.\d*)(?P<lon_hemisphere>[EW])),
(?P<pos_latency>\d+)
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''NMEA header $PKEL99 ASCII text
4 Record Number??? ------
5 Knudsen Date 14042007 DDMMYYYY
6 Knudsen Time 182527.269 HHMMSS.sss
7 00191
8 HF Header (12 kHz) HF ASCII text
9 HF Depth to Surface 00.00 Meters *
10 HF Draft ,+008.50 Meters
11 LF Header LF ASCII text
12 LF Depth to Surface 73.22 Meters *
13 LF Depth Valid Flag 1 ASCII integer
14 LF Draft +008.50 Meters
15 Sound Speed 1500 Meters Per Second**
18 Latitude 58 07.128948N DD MM.MMMMMM***
19 Longitude 169 50.326409W DDD MM.MMMMMM***
20 Position Latency 1078
21 Checksum *10'''

regex_dict['pkel99'] = re.compile(pkel99_regex_str, re.VERBOSE)

########################################
# Winch

# ignore duplicates Winch-Control-Aft and Winch-Control-Stbd

winch_regex_str = r'''(?P<sentence>winch)_(?P<location>[a-z]+)\s*
(?P<julian_date>(?P<year>\d{4}):(?P<day_of_the_year>\d{1,3})):
(?P<time>(?P<hour>\d{1,2}):(?P<min>\d{1,2}):(?P<sec>\d*\.\d*))\s+
(?P<winch_num>\d+),\s*
(?P<tension_lbs>[+-]?\d+)?,\s*
(?P<wire_out_m>\d+)?,\s*
(?P<wire_speed>[+-]?\d*),\s*
(?P<unknown1>[^,]+)?,
(?P<unknown2>[^,]+)?,
(?P<unknown3>[^,]+)?,
(?P<unknown4>[^,]+)?
'''

'''3 Winch number 01
4 Wire tension 900 Pounds
5 Wire out 35 Meters
7 Wire speed -28 Meters/minute'''
regex_dict['winch'] = re.compile(winch_regex_str, re.VERBOSE)

########################################
# Gravity

bgm_regex_str = r''':::((?P<sentence>bgm)(?P<sensor>\d+))\s*
(?P<julian_date>(?P<year>\d{4}):(?P<day_of_the_year>\d{1,3})):
(?P<time>(?P<hour>\d{1,2}):(?P<min>\d{1,2}):(?P<sec>\d*\.\d*))\s+
(?P<measurement_lenght_qtr_sec>\d+):
(?P<counts>\d+)\s+
(?P<status_flags>\d+)'''
'''measurement period in quarters of a second 04 quarters of a second
4 "counts" proportional to observed gravity 025278 counts
5 status flags 00 0 = OK'''
regex_dict['bgm'] = re.compile(bgm_regex_str, re.VERBOSE)

########################################
# POSMV Attitude

att_regex_str = r''':::(?P<talker>pos)(?P<sentence>att)\s*
(?P<julian_date>(?P<year>\d{4}):(?P<day_of_the_year>\d{1,3})):
(?P<time>(?P<hour>\d{1,2}):(?P<min>\d{1,2}):(?P<sec>\d*\.\d*))\s+:
(?P<unknown1>[+-]?[0-9A-F]{6})\s*
(?P<unknown2>[+-]?[0-9A-F]{5})\s*
(?P<unknown3>[+-]?[0-9A-F]{4})\s*
(?P<unknown4>[+-]?[0-9A-F]{4})'''
regex_dict['att'] = re.compile(att_regex_str, re.VERBOSE)

########################################
# SeaBeam Speed of Sound in Surface Water

sbsv_regex_str = r''':::(?P<talker>sb)(?P<sentence>sv)\s*
(?P<julian_date>(?P<year>\d{4}):(?P<day_of_the_year>\d{1,3})):
(?P<time>(?P<hour>\d{1,2}):(?P<min>\d{1,2}):(?P<sec>\d*\.\d*))\s+
(?P<sound_speed>\d*\.\d*),\s*
(?P<unknown_maybe_temp>[+-]?\d*\.\d*),\s*
(?P<unknown2>\d*\.\d*),\s*
(?P<unknown3>\d*(\.\d*)?)'''
regex_dict['sbsv'] = re.compile(sbsv_regex_str, re.VERBOSE)

########################################
# MWV wind report

mwv_regex_str = r'''[$](?P<talker>[A-Z]{2})(?P<sentence>MWV),
(?P<direction>\d{1,3}),
(?P<relative>R),
(?P<wind_speed_kts>\d{3}\.\d*),
(?P<knots>N),
(?P<valid>[AV])
\*(?P<checksum>[0-9A-F][0-9A-F])'''
'''3 NMEA header $WIMWV ASCII text
4 Wind Direction 033 Degrees
5 R= Relative R ASCII character
6 Wind Speed 028.1 Knots
7 N= Knots N ASCII character
8 A= Valid Data A ASCII character
9 Check sum *36 ASCII text'''
regex_dict['mwv'] = re.compile(mwv_regex_str, re.VERBOSE)

########################################
# Pressure sensor

psa_regex_str = r'''[$](?P<talker>[A-Z]{2})(?P<sentence>PSA),
(?P<pressure_psi>\d*\.\d*),
(?P<pressure_raw>\d*\.\d*)
\*(?P<checksum>[0-9A-F][0-9A-F])'''
'''NMEA header $PSPSA ASCII text
4 Pressure 25.88 PSI
5 Raw Volts 2.588 Volts
6 Check sum *41 ASCII text'''

regex_dict['psa'] = re.compile(psa_regex_str, re.VERBOSE)

##############################
# Sound Velocimeter

sound_vel_regex_str = r'''(?P<sentence>Sound-Velocimeter):::(?P<date>\d\d/\d\d/\d{4}),
(?P<time>\d\d:\d\d:\d\d.\d*),\s*
(?P<sound_velocity>\d*\.\d*)?'''
regex_dict['sound_vel'] = re.compile(sound_vel_regex_str, re.VERBOSE)


########################################
# VBW - Speed over water and ground

vbw_regex_str = r'''[$](?P<talker>[A-Z]{2})(?P<sentence>VBW),
(?P<longitudinal_water_speed_kts>[+-]?\d*\.\d*)?,
(?P<transverse_water_speed_kts>[+-]?\d*\.\d*)?,
(?P<water_status>[AV]),
(?P<longitudinal_ground_speed_kts>[+-]?\d*\.\d*)?,
(?P<transverse_ground_speed_kts>[+-]?\d*\.\d*)?,
(?P<ground_status>[AV])
\*(?P<checksum>[0-9A-F][0-9A-F])'''
regex_dict['vbw'] = re.compile(vbw_regex_str, re.VERBOSE)

########################################
# SRA - Solar Ragiation

sra_regex_str = r'''[$](?P<talker>[A-Z]{2})(?P<sentence>SRA),
(?P<short_wave_rad>[+-]?\d*\.\d*),
(?P<short_wave_rad_raw>[+-]?\d*\.\d*),
(?P<long_wave_rad>[+-]?\d*\.\d*),
(?P<long_wave_rad_raw>[+-]?\d*\.\d*),
(?P<dome_temp_k>\d*\.\d*),
(?P<dome_temp_raw>\d*\.\d*),
(?P<body_temp_k>\d*\.\d*),
(?P<body_temp_raw>\d*\.\d*)
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''NMEA header $PSSRA ASCII text
4 Short Wave Radiation 1.20 W/m*2
5 Short Wave Radiation, RAW 0.010 millivolts
6 Long Wave Radiation (LWR) 338.30 W/m*2
7 LWR, RAW 0.034 millivolts
8 LWR, Dome temperature 276.02 Degrees Kelvin
9 LWR, Some temp, RAW 1.192 volts
10 LWR, Body temperature 275.97 Degrees Kelvin
11 LWR, Body temp, RAW 1.194 volts
12 Check sum *44 ASCII text'''

regex_dict['sra'] = re.compile(sra_regex_str, re.VERBOSE)

########################################
# PAR - Photosynthetic Active Radiation

par_regex_str = r'''[$](?P<talker>[A-Z]{2})(?P<sentence>SPA),
(?P<surface_par>\d*\.\d*),
(?P<surface_par_raw>\d*\.\d*)
\*(?P<checksum>[0-9A-F][0-9A-F])'''

'''NMEA header $PSSPA ASCII text
4 Surface PAR 1749.51 MicroEinstiens sec /m*2
5 Surface PAR 1.056 Volts
6 Check sum *4C ASCII text'''

regex_dict['par'] = re.compile(par_regex_str, re.VERBOSE)


######################################################################

# FIX: add after ::: ?(P<healy_dev2>[A-Za-z0-9]\s*
healy_hdr_regex_str = r'''(?P<healy_device>[-a-zA-Z0-9_]+):::
(?P<healy_datetime>
(?P<healy_date>\d\d/\d\d/\d{4}),
(?P<healy_time>\d\d:\d\d:\d\d.\d*)
)
,'''

healy_hdr_regex = re.compile(healy_hdr_regex_str, re.VERBOSE)

healy_hdr_julian_regex_str = r'''(?P<healy_device>[-a-zA-Z0-9_]+):::
(?P<healy_device_short>[-a-zA-Z0-9_]+)\s*
(?P<healy_julian_datetime>
(?P<healy_julian_date>\d{4}:\d{1,3}):
(?P<healy_time>\d\d:\d\d:\d+.\d*)
)
\s*'''

healy_hdr_julian_regex = re.compile(healy_hdr_julian_regex_str, re.VERBOSE)

######################################################################
def healy_header_dict(line):
    match = healy_hdr_julian_regex.search(line)
    if match is not None:
        #print type(match), match
        #print 'FOUND julian date!!!'
        #print match.groupdict()
        match = match.groupdict()
        r = {}
        r['healy_ts'] = datetime.datetime.strptime(match['healy_julian_datetime'].split('.')[0],'%Y:%j:%H:%M:%S')
        r['healy_device'] = match['healy_device']
        return r

    match = healy_hdr_regex.search(line)
    if match is not None:
        #print type(match), match
        #print 'FOUND julian date!!!'
        #print match.groupdict()
        match = match.groupdict()
        r = {}
        r['healy_ts'] = datetime.datetime.strptime(match['healy_datetime'].split('.')[0],'%m/%d/%Y,%H:%M:%S')
        r['healy_device'] = match['healy_device']
        return r

    sys.stderr.write('ERROR: could not parse healy header:\n  %s\n' % (line,))
    return None


# def uscg_nmea_get_sentence(nmea_str):
#     if nmea_str[0:3] == 'HLY':
#         try:
#             nmea_type = nmea_str.split()[2][3:6]
#             return nmea_type
#         except:
#             return None

#     try:
#         return nmea_str.split(',')[2][-3:]
#     except:
#         return None




def parse_mail_message(text,verbose=False):
    v = verbose
    matches = 0
    misses = 0
    parsed = []
    unparsed = []

    #print text
    for line in text.split('\n'):
        if 'Winch-Control' in line:
            continue # skip dups
        if 'GPVTG' in line: continue # FIX: handle
        if 'Call-Sign' in line: continue # FIX: handle
        if 'PSATC' in line: continue # FIX: handle
        if 'HEROT' in line: continue # FIX: handle
        if 'IBS-WayPoints' in line: continue # FIX: handle
        if 'ISUSV3-SERIAL' in line: continue # FIX: handle
        if 'PSXTA' in line: continue # FIX: handle
        if 'GPGSV' in line: continue # FIX: handle
        if 'PRDID' in line: continue # FIX: handle
        if 'GPRMC' in line: continue # FIX: handle
        if 'PTNLDG' in line: continue # FIX: handle
        if 'GPMSS' in line: continue # FIX: handle
        if 'NVWPL' in line: continue # FIX: handle
        if 'NO DATA' in line: continue # FIX: handle
        if 'HEXDR' in line: continue # FIX: handle
        if 'NVXDR' in line: continue # FIX: handle
        if 'GPGSA' in line: continue # FIX: handle
        if '# ' == line[:2]: continue # FIX: handle
        if line == '': continue
        if line[0] in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', chr(32), ','): continue

        for key in regex_dict:
            match = regex_dict[key].search(line)
            if match is not None:
                break
        if match is None:
            #if v:
            #print 'No_match_for_line: "%s"' % (line.strip(),)
            #print '   line[0]:',line[0], '->', ord(line[0])
            misses += 1
            continue
        match = match.groupdict()

        # Append the healy fields that come before the data.
        healy_hdr = healy_header_dict(line)
        if healy_hdr is not None:
            match.update(healy_hdr)
        else:
            print 'warning... no healy header for',line

        if v:
            print '\n',match
        matches += 1
        parsed.append( (key,match,line) )
    if v:
        print 'matches: %d\nmisses: %d' % (matches,misses)

    #print parsed
    return {'parsed':parsed, 'unparsed':unparsed}


def main_test():
    matches = 0
    misses = 0
    for line in test_str.split('\n'):
        if 'Winch-Control' in line:
            continue # skip dups

        for key in regex_dict:
            match = regex_dict[key].search(line)
            if match is not None:
                break

        if match is None:
            print 'No_match_for_line: "%s"' % (line.strip(),)
            misses += 1
            continue

        match = match.groupdict()
        matches += 1

    print 'matches: %d\nmisses: %d' % (matches,misses)




def get_date(datestr):
    s = datestr
    try:
        return dateutils.parser.parse(datestr)
    except:
        pass

    try:
        return dateutils.parser.parse(datestr.rstrip('GMT'))
    except:
        pass

    try:
        return dateutils.parser.parse(s[:s.find('GMT')-1])
    except:
        pass
        #print 'failed stripping 1 before GMT'

    parse(datestr)

def get_entries_by_type(entry_type,msgs, verbose=False):
    results = []
    for msg in msgs:
        if entry_type == msg[0]:
            results.append(msg[1])
            if verbose:
                print msg[2]

    return results

createdb_str = '''
CREATE TABLE IF NOT EXISTS {table_name} (
  heading REAL, -- ashtech PAT heading in degrees
  lon REAL, -- GGA position
  lat REAL, -- GGA position
  ts TIMESTAMP, -- ZDA
  depth REAL, -- CTR depth_m in meters
  air_temp REAL, -- ME[ABC] Deg C
  humidity REAL, -- ME[ABC]
  pressure REAL, -- ME[ABC] barometric pressure_mb (milli bar)
  precip REAL, -- ME[ABC] milimeters
  sea_temp REAL, -- STA Deg C
  speed REAL -- VTG speed knots

);
'''
possible_fields='''
-- oxa
   -- oxygen_temp_c
-- vtg
   -- track_deg_true
   -- speed_knots
-- shr
   -- roll_deg
   -- pitch_deg
   -- heave_deg
-- wd
   -- wind_dir_true_true_deg
   -- wind_speed_true_mps
-- wind
   -- cog_deg
-- winch  location {aft,stbd}
   -- wire_out_m
-- sound_vel
   -- sound_velocity
-- sra
   -- short_wave_rad
   -- long_wave_rad
'''

def cascade_get_entry_by_type(entry_type, field, msgs, verbose=False):
    lst = get_entries_by_type(entry_type, msgs)
    for item in lst:
        if field in item:
            return item[field]
    return None

def cascade_get_entry_by_type_float(entry_type, field, msgs, verbose=False):
    'return the first entry found as a float or None'
    lst = get_entries_by_type(entry_type, msgs)
    for item in lst:
        if field in item:
            try:
                return float(item[field])
            except:
                pass
    return None

    #get_entries_by_type('zda',parsed)[0]['time_utc']
    #get_entries_by_type('zda',parsed)[0]['year']
    #get_entries_by_type('zda',parsed)[0]['month']
    #get_entries_by_type('zda',parsed)[0]['day']

def decode_gga(msg_dict):
    'take a regex dictionary of a gga and return an interpreted gga with correct python types'

    i = msg_dict # input
    o = {} # output
    o['hour'] = int(i['hour'])
    o['minute'] = int(i['minute'])
    o['second'] = float(i['second'])

    lon = int(i['lon_deg']) + float(i['lon_min']) / 60
    if i['lon_hemi']=='W': lon *= -1

    lat = int(i['lat_deg']) + float(i['lat_min']) / 60
    if i['lat_hemi']=='S': lat *= -1

    o['lon'] = lon
    o['lat'] = lat

    return o


def decode_gll(msg_dict):
    'take a regex dictionary of a gll and return an interpreted gll with correct python types'

    i = msg_dict # input
    o = {} # output
    o['hour'] = int(i['hour'])
    o['minute'] = int(i['minute'])
    o['second'] = float(i['second'])

    lon = int(i['lon_deg']) + float(i['lon_min']) / 60
    if i['lon_hemi']=='W': lon *= -1

    lat = int(i['lat_deg']) + float(i['lat_min']) / 60
    if i['lat_hemi']=='S': lat *= -1

    o['lon'] = lon
    o['lat'] = lat

    return o


def email_payload_to_dict(payload, verbose=False):
    results = parse_mail_message(payload) #,True)
    parsed = results['parsed']

    db_entry = {}

    try:
      db_entry['ts'] = datetime.datetime.strptime(payload.split('\n')[0],'# %a %b %d %H:%M:%S %Z %Y')
    except ValueError:
      print 'Bad timestamp?:', payload.split('\n')[0]
      return None

    lon = None
    lat = None
    for msg in get_entries_by_type('gga',parsed):
        try:
            gga = decode_gga(msg)
        except:
            if verbose:
                sys.stderr.write('WARNING: bad gga\n  %s'% (str(msg),))
            continue
        dt = db_entry['ts'] - msg['healy_ts']
        if abs(dt) > datetime.timedelta(seconds=60*15):
            #sys.stderr.write('WARNING: Report too old: %s vrs %s' % (str(db_entry['ts']),str(msg['healy_ts'])))
            continue
        lon = gga['lon']
        lat = gga['lat']
        break

    # Fall back to GLL if no GGA - happens in port
    if lon == None:
        #del gga # for coding safety
        for msg in get_entries_by_type('gll',parsed):
            #print 'trying:',msg
            try:
                gll = decode_gll(msg)
            except:
                if verbose:
                    sys.stderr.write('WARNING: bad gll\n  %s'% (str(msg),))
                continue
            dt = db_entry['ts'] - msg['healy_ts']
            if abs(dt) > datetime.timedelta(seconds=60*15):
                #sys.stderr.write('WARNING: Report too old: %s vrs %s' % (str(db_entry['ts']),str(msg['healy_ts'])))
                continue
            lon = gll['lon']
            lat = gll['lat']
            break

    if lon == None or lat == None:
        #sys.stderr.write('Skipping message with no valid gga or gll\n')
        return None # skip bad position

    db_entry['lon'] = lon
    db_entry['lat'] = lat

    db_entry['heading'] = cascade_get_entry_by_type_float('pat','heading',parsed)
    db_entry['depth'] = cascade_get_entry_by_type_float('ctr','depth_m',parsed)
    db_entry['air_temp'] = cascade_get_entry_by_type_float('me','air_temp_c',parsed)
    db_entry['humidity'] = cascade_get_entry_by_type_float('me','rel_humid',parsed)
    db_entry['pressure'] = cascade_get_entry_by_type_float('me','barometric_pressure_mb',parsed)
    db_entry['precip'] = cascade_get_entry_by_type('me','precip_mm',parsed)
    db_entry['sea_temp'] = cascade_get_entry_by_type('sta','sea_temp_c',parsed)
    db_entry['speed'] = cascade_get_entry_by_type('vtg','speed_knots',parsed)

    return db_entry

def build_db(email_file, db_name, db_table='healy_summary', verbose=False):
    sqlite3.paramstyle = 'named'
    cx = sqlite3.connect('healy.db3')
    cx.row_factory = sqlite3.Row

    cx.execute(createdb_str.format(table_name = db_table));

    for count,(key,msg) in enumerate( mailbox.mbox(email_file).iteritems() ):
        #print '-----------------------------------------------------------'
        #if count < 10000: continue
        if count % 100 == 0: 
          sys.stderr.write('count: %d\n' % count)
          cx.commit()


        payload = msg.get_payload()
        db_entry = email_payload_to_dict(payload, verbose)
        if db_entry is None:
            #sys.stderr.write('Skipping bad report: "%s"\n' % (payload.split('\n')[0],) )
            continue

        #if verbose: sys.stderr.write('entry_dict: %s\n' % (db_entry,))

        cx.execute('''INSERT INTO healy_summary VALUES (
:heading,
:lon,
:lat,
:ts,
:depth,
:air_temp,
:humidity,
:pressure,
:precip,
:sea_temp,
:speed
);''',db_entry)

    cx.commit()


def main():
    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options]",
                          version="%prog "+__version__+' ('+__date__+')')

    parser.add_option('-d', '--database', dest='db_filename', default='healy.sqlite3',
                      help='Ship track database [default: %default]')

    parser.add_option('-t', '--db-table', dest='db_table', default='healy_summary',
                      help='Database tablename [default: %default]')

    parser.add_option('-e', '--email-file', dest='email_file', default='healy',
                      help='Email reports file in mbox format [default: %default]')

    parser.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true',
                      help='run the tests run in verbose mode')

    (options, args) = parser.parse_args()

    build_db(options.email_file, options.db_filename, options.db_table, verbose=options.verbose)


if __name__ == '__main__':
    main()
