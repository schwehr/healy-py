#!/usr/bin/env python
__author__    = 'Kurt Schwehr'
__version__   = '$Revision: 4799 $'.split()[1]
__revision__  = __version__ # For pylint
__date__ = '$Date: 2006-09-25 11:09:02 -0400 (Mon, 25 Sep 2006) $'.split()[1]
__copyright__ = '2009'

__doc__ ='''

@requires: U{Python<http://python.org/>} >= 2.5
@requires: U{sqlite3<>}

@undocumented: __doc__
@since: 2009-May-19
@status: under development

@see: U{healy<>}
'''
import datetime
import sqlite3
import sys
import colorsys

iso8601_timeformat = '%Y-%m-%dT%H:%M:%SZ'

def hex2(val):
    ''' make a 2 character hex string for color'''
    h = hex(val).split('x')[1]
    if len(h)==1:
        h = '0'+h
    return h

def  sqlite2kml(db, outfile, table_name='healy_summary', verbose='False', kml_complete=True, include_style=True, include_style_def=True):
    v = verbose
    cx = db
    cu = cx.cursor()

    if isinstance(outfile,str):
        if v: sys.stderr.write('opening_output_file: %s\n' % (outfile,))
        outfile = file(outfile,'w')
    o = outfile
    
    if kml_complete:
        o.write('''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.0" xmlns:gx="http://www.google.com/kml/ext/2.2">
<Document>
	<name>Healy science data</name>
	<open>1</open>
	<Snippet>NSF,USCG,LDEO,CCOM/JHC,Schwehr</Snippet>
	<description>Derived from hourly data emails from the ship board data systems.

The ship board science systems are run by LDEO and funded by NSF.  The USCGC Healy is
an icebreaker run by USCG.

Visualization was created by <a href="http://schwehr.org/">Kurt Schwehr</a> of the UNH <a href="http://ccom.unh.edu/">CCOM/JHC</a>.
</description> 
''')
        ##############################
        # Attempt to set the time and view ranges - FIX: broken!

        cu.execute('SELECT lon,lat FROM healy_summary ORDER BY ts DESC LIMIT 1;')
        row = cu.fetchone()
        lon = row['lon'] # Focus on the most recent point
        lat = row['lat']

        cu.execute('SELECT MIN(ts) AS ts_min, MAX(ts) as ts_max FROM healy_summary;')
        row = cu.fetchone()
        ts_min = datetime.datetime.strptime(row['ts_min'],'%Y-%m-%d %H:%M:%S')
        ts_max = datetime.datetime.strptime(row['ts_max'],'%Y-%m-%d %H:%M:%S')

        o.write('''<LookAt>
    <gx:TimeSpan>
      <begin>{ts_min}</begin>
      <end>{ts_max}</end>
    </gx:TimeSpan>
    <longitude>{lon}</longitude>
    <latitude>{lat}</latitude>
    <altitude>0</altitude>
    <range>{range}</range>
    <tilt>0</tilt>
    <heading>0</heading>
    <altitudeMode>relativeToGround</altitudeMode>
  </LookAt>

'''.format(lat=lat, lon=lon, range=3000000, ts_min=ts_min.strftime('%Y-%m-%d'), ts_max=ts_max.strftime('%Y-%m-%d')))


    if include_style_def:
        o.write('''
	<!-- For the science report placemarks -->
	<StyleMap id="healy">
		<Pair>
			<key>normal</key>
			<styleUrl>#healy_normal</styleUrl>
		</Pair>
		<Pair>
			<key>highlight</key>
			<styleUrl>#healy_highlight</styleUrl>
		</Pair>
	</StyleMap>
	<Style id="healy_normal">
	  <BalloonStyle>
            <text>
              <![CDATA[$[name]<p>$[description]<br/>]]>
            </text>
          </BalloonStyle>
		<IconStyle>
			<scale>1</scale>
			<Icon>
				<href>http://maps.google.com/mapfiles/kml/paddle/purple-diamond.png</href>
			</Icon>
			<hotSpot x="0.5" y="0." xunits="fraction" yunits="fraction"/> -->
		</IconStyle>
		<LabelStyle>
			<color>ff06249b</color>
		</LabelStyle>
		<ListStyle>
		</ListStyle>
		<LineStyle>
			<color>ff0086ff</color>
			<width>3</width>
		</LineStyle>
	</Style>
	<Style id="healy_highlight">
	  <BalloonStyle>
            <text>
              <![CDATA[$[name]<p>$[description]<br/><br/>
		<i>USCG,NSF,LDEO,CCOM/JHC</i>]]>
            </text>
          </BalloonStyle>
		<IconStyle>
			<scale>1.1</scale>
			<Icon>
				<href>http://maps.google.com/mapfiles/kml/paddle/purple-diamond.png</href>
			</Icon>
			<hotSpot x="0.5" y="0." xunits="fraction" yunits="fraction"/> 
		</IconStyle>
		<LabelStyle>
			<color>ff06249b</color>
		</LabelStyle>
		<ListStyle>
		</ListStyle>
		<LineStyle>
			<color>ff0086ff</color>
			<width>3</width>
		</LineStyle>
	</Style>


''')

        # Create the ship track styles...
        #aabbggrr
        for i in range(11):
            width = 5 - (i / 2.1)
            if width < 1:
                width = 1
            # h,s,v all [0..1]
            a = int( 255 * (0.5 + 0.05 * i) )
            h = 0.6
            s = 0.8 + 0.02 * i
            v = 1 - 0.05 * i
            r, g, b = [ int(255 * band) for band in colorsys.hsv_to_rgb(h,s,v) ]
            print i,':  ',r,g,b,a, width
            o.write('''<Style id="healy_line{i}">
  <LineStyle>
   <color>{a}{b}{g}{r}</color><width>{width}</width>
  </LineStyle>
</Style>
'''.format(i=i, width=width, a = hex(a), r = hex2(r), g = hex2(g), b = hex2(b))
)




    o.write('''	<Folder><name>Ship track</name>\n''')

    prev_point = None
    for point_num,point in enumerate(cx.execute('SELECT ts,lon,lat FROM %s  WHERE ts > "2009-08-05" ORDER by ts;' % table_name)):
        point = dict(point)
        #print prev_point,'->',point
        point['ts'] = datetime.datetime.strptime(point['ts'],'%Y-%m-%d %H:%M:%S')
        #print point['ts']

        # 			<!-- <visibility>1</visibility> -->
        if prev_point is not None:
            o.write('''
		<Placemark>
			<styleUrl>#healy_line{style_num}</styleUrl>
			<name>Track seg</name>
			<snippet>{date}</snippet>
			<description>{ts0} to {ts1}</description>
			<TimeSpan><begin>{ts0}</begin><end>{ts1}</end></TimeSpan>
			<LineString>
				<coordinates>
					{x0},{y0},10
					{x1},{y1},10
				</coordinates>
			</LineString>
		 </Placemark>
'''.format(x0=prev_point['lon'],y0=prev_point['lat'],ts0=prev_point['ts'].strftime(iso8601_timeformat),
            x1=point['lon'],y1=point['lat'],ts1=point['ts'].strftime(iso8601_timeformat),
           date=point['ts'].strftime('%Y-%m-%d'),
           style_num = point_num % 11 )
)
        prev_point = point

    o.write('''	</Folder><!-- Healy ship track -->\n''')


    o.write('''	<Folder><!-- <visibility>0</visibility> --> <name>Science reports</name>\n''')

    for point_num,point in enumerate(cx.execute('SELECT * FROM %s WHERE ts > "2009-08-05";' % table_name)):
        point = dict(point)
        point['ts'] = datetime.datetime.strptime(point['ts'],'%Y-%m-%d %H:%M:%S')

        lon = float(point['lon'])
        hemi = 'E'
        if lon < 0: hemi = 'W'
        point['lon_text'] = '%.3f %s' % (float(lon), hemi)

        lat = float(point['lat'])
        hemi = 'N'
        if lat < 0: hemi = 'S'
        point['lat_text'] = '%.03f %s' % (float(lat), hemi)


            

        o.write('''
		<Placemark>
			<!-- <visibility>0</visibility> -->
			<name>{ts_short}</name>
<styleUrl>#healy</styleUrl>
			<snippet>Science Report</snippet>
			<description><![CDATA[
<a href="http://www.uscg.mil/pacarea/cgcHealy/">USCGC HEALY (WAGB-20)</a><br/>
<a href="http://www.icefloe.net/healy.html">Healy Science Operations</a><br/>
<a href="http://www.icefloe.net/cruisetrack.html">Healy Cruise Track</a><br/>
<a href="http://vislab-ccom.unh.edu/~schwehr/healy/">Healy in Google Earth</a>
<table border="1">
<tr bgcolor="red"><th>Field</th> <th>Value</th> <th>Units</th> </tr>
<tr><th align="left">UTC time</th> <th align="right">{ts}</th> <th>UTC</th> </tr>
<tr><th align="left">Longitude</th> <th align="right">{lon_text}</th> <th>&deg;</th> </tr>
<tr><th align="left">Latitude</th> <th align="right">{lat_text}</th> <th>&deg;</th> </tr>
<tr><th align="left">Heading</th> <th align="right">{heading}</th> <th>&deg; True</th> </tr>
<tr><th align="left">Speed over ground</th> <th align="right">{speed}</th> <th>knots</th> </tr>
<tr><th align="left">Water Depth</th> <th align="right">{depth}</th> <th>m</th></tr>
<tr><th align="left">Sea temp</th> <th align="right">{sea_temp}</th> <th>&deg; C</th></tr>
<tr><th align="left">Air Temp</th> <th align="right">{air_temp}</th> <th>&deg; C</th></tr>
<tr><th align="left">Humidity</th> <th align="right">{humidity}</th> <th>%</th> </tr>
<tr><th align="left">Presure</th> <th align="right">{pressure}</th> <th>millibar</th> </tr>
<tr><th align="left">Precipitation</th> <th align="right">{precip}</th> <th>mm</th> </tr>
</table>
			]]></description>
			<TimeStamp>{ts_google}</TimeStamp>
			<Point>
				<coordinates>{x},{y},10</coordinates>
			</Point>
		</Placemark>
'''.format(x=point['lon'], y=point['lat'],
           ts_google=point['ts'].strftime(iso8601_timeformat),
           ts_short=point['ts'].strftime('%d %b %H:%M'),
           **point))

    o.write('''	</Folder><!-- Science Reports -->\n''')

    if kml_complete:
        o.write('''
</Document>
</kml>
''')


def main():
    '''
    FIX: document main
    '''
    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options]",
                          version="%prog "+__version__+' ('+__date__+')')

    parser.add_option('-d', '--database', dest='db_filename', default='healy.db3',
                      help='Ship track database [default: %default]')

    parser.add_option('-s', '--summary-table', dest='summary_table', default='healy_summary',
                      help='Database tablename [default: %default]')

    parser.add_option('-o', '--outfile', dest='outfile', default='healy-instrument-reports.kml',
                      help='Output KML to write [default: %default]')

    parser.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true',
                      help='run the tests run in verbose mode')

    (options, args) = parser.parse_args()
    v = options.verbose

    if v:
        sys.stderr.write('Opening db\n')
    sqlite3.paramstyle = 'named'
    cx = sqlite3.connect(options.db_filename)
    cx.row_factory = sqlite3.Row
   

    sqlite2kml(cx,options.outfile, table_name=options.summary_table, verbose=v)

if __name__ == '__main__':
    main()
