#!/usr/bin/env python

# 2009-July-27
# Horrible ugly hackish code.

__author__    = 'Kurt Schwehr'
__version__   = '$Revision: 4799 $'.split()[1]
__revision__  = __version__ # For pylint
__date__ = '$Date: 2006-09-25 11:09:02 -0400 (Mon, 25 Sep 2006) $'.split()[1]
__copyright__ = '2009'

__doc__ ='''
GeoRSS feeds in RSS 1, RSS 2, and atom

@requires: U{Python<http://python.org/>} >= 2.6

@undocumented: __doc__
@since: 2009-Jul-27
@status: under development

@see: U{RSS 1.0<http://web.resource.org/rss/1.0/spec>}
@see: U{RSS 2.0<http://cyber.law.harvard.edu/rss/rss.html>}
@see: U{Atom 1.0<http://www.ietf.org/rfc/rfc4287.txt">}
@see: U{IRI <http://www.ietf.org/rfc/rfc3987.txt">} What???

@todo: what is an IRI?
'''

import georss

import datetime
import calendar
import sqlite3
import sys
import hashlib
import colorsys

def hex2(val):
    ''' make a 2 character hex string for color'''
    h = hex(val).split('x')[1]
    if len(h)==1:
        h = '0'+h
    return h

def datetime2unixtimestamp(a_datetime):
    return calendar.timegm(datetime.datetime.utctimetuple(a_datetime))

cx = sqlite3.connect('healy.db3')
cx.row_factory = sqlite3.Row # Allow access of fields by name

iso8601_timeformat = '%Y-%m-%dT%H:%M:%SZ'
now = datetime.datetime.utcnow()
unix_now = datetime2unixtimestamp(now)
    

domain = 'vislab-ccom.unh.edu'
base_url = 'http://{domain}/%7Eschwehr/healy/'.format(domain=domain)  # %7E
author = 'Kurt Schwehr'
author_url = 'http://schwehr.org'
author_email = 'kurt@ccom.unh.edu'

# FIX: this is supposed to be an IRI... ?  Should it just be the domain name?
base_id = 'tag:{domain},{year}:{last_name}:{key}'.format(domain=domain, 
                                                    year=now.year, 
                                                    last_name=author.split()[-1].lower(), 
                                                    key='healysci'+str(unix_now) )

id = base_id + ':healysci' # +str(unix_now) It looks like the id needs to be constanstant for the feed as a whole.
filename = 'healy-science-gml.atom'

o = file(filename,'w')

o.write('''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:georss="http://www.georss.org/georss"
      xmlns:gml="http://www.opengis.net/gml"
      xmlns:sy="http://purl.org/rss/1.0/modules/syndication/"
>

  <sy:updatePeriod>hourly</sy:updatePeriod>
  <sy:updateFrequency>1</sy:updateFrequency>

  <title>{title}</title>
  <link href="{url_atom}"
        type="application/atom+xml" rel="self"/>
  <link href="{url}"
        type="text/html" rel="alternate"/>

  <updated>{updated}</updated>
  <author>
    <name>{author}</name>
    <uri>{author_uri}</uri>
    <email>{author_email}</email>
  </author>
  <id>{id}</id>
'''.format(title = 'Healy science reports (GML GeoRSS)',
           url_atom = base_url+filename,
           updated = now.strftime(iso8601_timeformat),
           url = base_url,
           author = 'Kurt Schwehr',
           author_uri = author_url,
           author_email = author_email,
           id = id
           )
)

entries = []
for row in cx.execute('SELECT * FROM healy_summary WHERE lon IS NOT NULL AND ts IS NOT NULL ORDER BY ts DESC LIMIT 10;'):
    row = dict(row)

# &#176; is &deg;
    when = datetime.datetime.strptime(row['ts'],'%Y-%m-%d %H:%M:%S')
    row['ts'] = when
    #print when
    entry = {}
    entry['when'] = when
    entry['title'] = 'Healy science report at %s (%.2f %.2f)' % (when.strftime('%Y%m%d %H:%M'), row['lon'], row['lat'])
    entry['link'] = base_url # Doesn't really have a link
    entry['updated'] = when.strftime(iso8601_timeformat)
    entry['summary'] = 'Hourly science report from a USCG Icebreaker'
    entry['georss'] = '''<georss:where>
      <gml:Point>
        <gml:pos>{lat} {lon}</gml:pos> <!-- lat lon -->
      </gml:Point>
    </georss:where>'''.format(**row)
    entry['content'] = '''<table border="1">
<tr bgcolor="red"><th>Field</th> <th>Value</th> <th>Units</th> </tr>
<tr><th align="left">UTC time</th> <th align="right">{ts}</th> <th>UTC</th> </tr>
<tr><th align="left">Longitude</th> <th align="right">{lon}</th> <th>&#176;</th> </tr>
<tr><th align="left">Latitude</th> <th align="right">{lat}</th> <th>&#176;</th> </tr>
<tr><th align="left">Heading</th> <th align="right">{heading}</th> <th>&#176; True</th> </tr>
<tr><th align="left">Speed over ground</th> <th align="right">{speed}</th> <th>knots</th> </tr>
<tr><th align="left">Water Depth</th> <th align="right">{depth}</th> <th>m</th></tr>
<tr><th align="left">Sea temp</th> <th align="right">{sea_temp}</th> <th>&#176; C</th></tr>
<tr><th align="left">Air Temp</th> <th align="right">{air_temp}</th> <th>&#176; C</th></tr>
<tr><th align="left">Humidity</th> <th align="right">{humidity}</th> <th>%</th> </tr>
<tr><th align="left">Presure</th> <th align="right">{pressure}</th> <th>millibar</th> </tr>
<tr><th align="left">Precipitation</th> <th align="right">{precip}</th> <th>mm</th> </tr>
</table>
'''.format(**row)
    
    m = hashlib.md5()
    m.update(entry['content'])
    
    entry['id'] = base_id+':'+m.hexdigest()

    entries.append((row, entry))

    #print entry

# <![CDATA[  ]]>

    o.write('''
  <entry>
    <title>{title}</title>
    <link href="{link}" type="text/html" />
    <id>{id}</id>
    <updated>{updated}</updated>
    <summary>{summary}</summary>
    {georss}
    <content type="xhtml"><div xmlns="http://www.w3.org/1999/xhtml">
{content}
</div>
</content>
    <rights>No claim is made to this data</rights>
  </entry>
'''.format(**entry))

o.write('</feed>\n')


######################################################################
# Simple GeoRSS atom

filename = 'healy-science-simple.atom'

o = file(filename,'w')

o.write('''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:georss="http://www.georss.org/georss"
      xmlns:gml="http://www.opengis.net/gml"
      xmlns:sy="http://purl.org/rss/1.0/modules/syndication/"
>

  <sy:updatePeriod>hourly</sy:updatePeriod>
  <sy:updateFrequency>1</sy:updateFrequency>

  <title>{title}</title>
  <link href="{url_atom}"
        type="application/atom+xml" rel="self"/>
  <link href="{url}"
        type="text/html" rel="alternate"/>

  <updated>{updated}</updated>
  <author>
    <name>{author}</name>
    <uri>{author_uri}</uri>
    <email>{author_email}</email>
  </author>
  <id>{id}</id>
'''.format(title = 'Healy science reports (Simple GeoRSS)',
           url_atom = base_url+filename,
           updated = now.strftime(iso8601_timeformat),
           url = base_url,
           author = 'Kurt Schwehr',
           author_uri = author_url,
           author_email = author_email,
           id = id
           )
)

#print entries

for row,entry in entries:
    entry['georss'] = '<georss:point>{lat} {lon}</georss:point> <!-- lat lon -->'.format(**row)
    entry['id'] += 'simple'

    o.write('''
  <entry>
    <title>{title}</title>
    <link href="{link}" type="text/html" />
    <id>{id}</id>
    <updated>{updated}</updated>
    <summary>{summary}</summary>
    {georss}
    <content type="xhtml"><div xmlns="http://www.w3.org/1999/xhtml">
{content}
</div>
</content>
    <rights>No claim is made to this data</rights>
  </entry>
'''.format(**entry))

o.write('</feed>')


######################################################################
# RSS 2.0 based on Google
# I added the syndication

# WGS84 Geo Positioning: an RDF vocabulary

filename = 'healy-science-google.rss'


# syndication does not validate
#  <!-- <sy:updatePeriod>hourly</sy:updatePeriod>
#  <sy:updateFrequency>1</sy:updateFrequency> -->
#   xmlns:sy="http://purl.org/rss/1.0/modules/syndication/"

# Mon, Jul 27 2009 / 18:30:01 GMT
o = file(filename,'w')
o.write('''<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"
  xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:atom="http://www.w3.org/2005/Atom"
>

  <channel>
    <title>{title}</title>
    <atom:link href="{rss_url}" rel="self" type="application/rss+xml" />
    <link>{link}</link>
    <ttl>60</ttl>  <!-- update every 60 minutes -->
    <copyright>This feed has no copyright</copyright>
    <description>{description}</description>
'''.format(title = 'Healy science reports (Google RSS 2 style)',
           link = base_url,
           rss_url = base_url + filename,
           description = 'Healy hourly science updates',
           ))
           
for row,entry in entries:

    #print entry
    dc_date = row['ts'].strftime('%Y-%m-%dT%H:%M:%S+00:00')
    pub_date = row['ts'].strftime('%a, %d %b %Y %H:%M:%S GMT') # RFC-822 Mon, Jun 8, 2009 / 20:01 PST
    google_maps_link = 'http://maps.google.com/maps?q={base_url}{filename}&ll={lat},{lon}&t=h&z=6'.format(
        base_url = base_url,
        filename = filename,
        **row)

    entry['lat'] = row['lat']
    entry['lon'] = row['lon']
    o.write('''
    <item>
      <title>{title}</title>
      <link>{link}</link>
      <guid isPermaLink="false">{id}</guid>
      <description><![CDATA[
<a href="{google_maps_link}">Google Map View</a></br>
{content}
]]></description>
      <dc:date>{dc_date}</dc:date>
      <pubDate>{pub_date}</pubDate>
      <geo:lat>{lat}</geo:lat>
      <geo:long>{lon}</geo:long>
</item>
'''.format(google_maps_link = google_maps_link,
           dc_date=dc_date, pub_date = pub_date, **entry))


o.write('  </channel>\n</rss>\n')

######################################################################
# KML

filename = 'healy-science-latest.kml'
o = file(filename,'w')

reload_time = reload = now + datetime.timedelta(hours=1,minutes=3)
cur_time_str = datetime.datetime(now.year,now.month,now.day,now.hour,minute=0).strftime('%d %b %H:%M')

o.write('''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.0">
  <NetworkLinkControl>
    <minRefreshPeriod>600</minRefreshPeriod>
    <!-- <message>Testing NetworkLinkControl - should reload {reload_time}</message> -->                           
    <linkName>Healy Aloftcon Camera {time}</linkName>
    <expires>{reload_time}</expires>  
  </NetworkLinkControl>
  <Document>
    <name>Healy science data {time}</name>
    <Snippet>NSF,USCG,LDEO,CCOM/JHC,Schwehr</Snippet>
    <description>Derived from hourly data emails from the ship board data systems.

The ship board science systems are run by LDEO and funded by NSF.  The USCGC Healy is
an icebreaker run by USCG.

Visualization was created by <a href="http://schwehr.org/">Kurt Schwehr</a> of the UNH <a href="http://ccom.unh.edu/">CCOM/JHC</a>.
</description>
'''.format(
            time = cur_time_str,
            reload_time = reload_time.strftime(iso8601_timeformat)
            )
)

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
if False:
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
    for point_num,point in enumerate(cx.execute('SELECT ts,lon,lat FROM healy_summary ORDER by ts DESC LIMIT 10;')):
        point = dict(point)
        point['ts'] = datetime.datetime.strptime(point['ts'],'%Y-%m-%d %H:%M:%S')

        if prev_point is not None:
#			<TimeSpan><begin>{ts0}</begin><end>{ts1}</end></TimeSpan>

            o.write('''
		<Placemark>
			<styleUrl>#healy_line{style_num}</styleUrl>
			<name>Track seg</name>
			<snippet>{date}</snippet>
			<description>{ts0} to {ts1}</description>
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

for point_num,point in enumerate(cx.execute('SELECT * FROM healy_summary ORDER BY ts DESC LIMIT 10;')):
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

#			<TimeStamp>{ts_google}</TimeStamp>
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
			<Point>
				<coordinates>{x},{y},10</coordinates>
			</Point>
		</Placemark>
'''.format(x=point['lon'], y=point['lat'],
           ts_google=point['ts'].strftime(iso8601_timeformat),
           ts_short=point['ts'].strftime('%d %b %H:%M'),
           **point))

o.write('''	</Folder><!-- Science Reports -->
</Document>
</kml>
''')
