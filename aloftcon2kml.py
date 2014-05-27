#!/sw/bin/python
# Hacked for MacOSX to get the fink build of python with the pyexiv2 library

#!/usr/bin/env python
__author__    = 'Kurt Schwehr'
__version__   = '$Revision: 4799 $'.split()[1]
__revision__  = __version__ # For pylint
__date__ = '$Date: 2006-09-25 11:09:02 -0400 (Mon, 25 Sep 2006) $'.split()[1]
__copyright__ = '2009'

__doc__ ='''
Convert the Healy aloftcon images into a KML file and try to produce a GeoRSS feed.  Meant to be run as a cron job

@requires: U{Python<http://python.org/>} >= 2.6
@requires: U{epydoc<http://epydoc.sourceforge.net/>} >= 3.0.1

@undocumented: __doc__
@since: 2009-Apr-18
@status: under development

@todo: Also generate a ship track
@see: U{Aloftcon images<http://mgds.ldeo.columbia.edu/healy/reports/aloftcon/2009/>} - Source of images.
'''

import sys
import datetime
#import urllib2
import urllib2 as urllib
import Image
import pyexiv2


 #iso8601_timeformat= '%04d-%02d-%02dT%02d:%02d:%02dZ' # % (y,mo,d,h,mi,s)
iso8601_timeformat = '%Y-%m-%dT%H:%M:%SZ'
'''ISO time format for NetworkLinkControl strftime
@see: U{KML Tutorial<http://code.google.com/apis/kml/documentation/kml_21tutorial.html#updates>}
'''

baseurl = 'http://mgds.ldeo.columbia.edu/healy/reports/aloftcon/' + str(datetime.datetime.utcnow().year)

style='''	<StyleMap id="healy">
		<Pair>
			<key>normal</key>
			<styleUrl>#healy_normal</styleUrl>
		</Pair>
		<Pair>
			<key>highlight</key>
			<styleUrl>#s_ylw-pushpin_hl</styleUrl>
		</Pair>
	</StyleMap>
	<Style id="healy_normal">
	  <BalloonStyle>
            <text>
              <![CDATA[$[name]<p>$[description]<br/><img src="http://vislab-ccom.unh.edu/~schwehr/healy/uscg-small"/>]]><br/>
NSF,USCG,LDEO,CCOM/JHC
            </text>
          </BalloonStyle>
		<IconStyle>
			<scale>1.5</scale>
			<Icon>
				<href>http://vislab-ccom.unh.edu/~schwehr/healy/healy64x64.png</href>
			</Icon>
			<hotSpot x="0.5" y="0.5" xunits="fraction" yunits="fraction"/>
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
	<Style id="s_ylw-pushpin_hl">
	  <BalloonStyle>
            <text>
              <![CDATA[$[name]<p>$[description]<br/><img src="http://vislab-ccom.unh.edu/~schwehr/healy/uscg-small"/>]]>
<br/>
NSF,USCG,LDEO,CCOM/JHC
            </text>
          </BalloonStyle>
		<IconStyle>
			<scale>2</scale>
			<Icon>
				<href>http://vislab-ccom.unh.edu/~schwehr/healy/healy64x64.png</href>
			</Icon>
			<hotSpot x="0.5" y="0.5" xunits="fraction" yunits="fraction"/>
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
'''

#def xml_start(outfile):
#    outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')

#def kml_start(outfile,name="Healy Aloftcon Camera"):
#    outfile.write('''<kml xmlns="http://earth.google.com/kml/2.0">
#<Document>
#  <name>{name}</name>
#'''.format(name=name))


def build_small_filename(filename):
    return filename.split('.')[0]+'-small.jpg'


def kml_author(outfile):
    outfile.write('''
    <atom:author>      
      <atom:name>USCG, NSF, LDGO, CCOM, Kurt Schwehr</atom:name>    
    </atom:author>    
    <atom:link href="http://vislab-ccom.unh.edu/~schwehr/healy/healy-aloftcon-latest.kml"/> 
''')


def kml_end(file):
    file.write('''</Document>
</kml>
''')

def rational2deg(r):
    ''' convert a pyexiv2 rational gps lat or lon to decimal degrees'''

    deg = r[0].numerator / float(r[0].denominator)
    min = r[1].numerator / float(r[1].denominator)
    sec = r[2].numerator / float(r[2].denominator)

    return deg + min / 60 + sec / 3600


def kml_placemark(x, y, z=10, description='No description', name='unknown',indent='\t\t'):
    ''' Try to handle writing kml placemarks
    '''
    out = []
    out.append(indent+'<Placemark>')
    out.append(indent+'\t<name>'+str(name)+'</name>')
    out.append('<styleUrl>#healy</styleUrl>')
    out.append(indent+'\t<snippet></snippet>') # Keep it blank
    out.append(indent+'\t<description>'+str(description)+'</description>')
    out.append(indent+'\t<Point>')
    out.append(indent+'\t\t<coordinates>'+str(x)+','+str(y)+','+str(z)+'</coordinates>')
    out.append(indent+'\t</Point>')
    out.append(indent+'</Placemark>')
    return '\n'.join(out)

def kml_line(outfile,positions,name="Healy ship track"):
    o = outfile
    o.write('''
\t\t\t<Placemark> <name>{name}</name> 
\t\t\t\t<snippet></snippet>
\t\t\t\t<description>
\t\t\t\t  Vessel: <a href="http://www.uscg.mil/pacarea/cgcHealy/">USCGC HEALY (WAGB-20)</a><br/>
\t\t\t\t  Track over the last 10 hours</description>
\t\t\t\t<styleUrl>#healy</styleUrl> 
\t\t\t\t<LineString><coordinates>
'''.format(name=name))

    for point in positions:
        print point
        o.write ('''\t\t\t\t{point[0]},{point[1]},0\n'''.format(point=point))
    o.write('\t\t\t</coordinates></LineString></Placemark>')



def image_position(filename):
    image = pyexiv2.Image(filename)
    image.readMetadata()
    lon =  rational2deg(image['Exif.GPSInfo.GPSLongitude'])
    if 'W' ==  image['Exif.GPSInfo.GPSLongitudeRef']:
        lon = -lon
    lat =  rational2deg(image['Exif.GPSInfo.GPSLatitude'])
    if 'S' ==  image['Exif.GPSInfo.GPSLatitudeRef']:
        lat = -lat

    return lon,lat

def process_image(filename,url,timestamp,small_url):
    '''FIX: pil 1.1.6 is unable to read these exif tags'''

    lon,lat = image_position(filename)

    description = '''<![CDATA[
\t\t\t<a href="http://www.uscg.mil/pacarea/cgcHealy/">USCGC HEALY (WAGB-20)</a><br/>
UTC time: {timestamp}<br/>
\t\t\t<a href="http://maps.google.com/?ll={lat},{lon}&z=10">Longitude: {lon_pretty}   Latitude: {lat_pretty}<br/></a> [Google Map location]<br/>'''.format(
        filename = filename,
        lon_pretty ='%+3.3f' % lon,
        lat_pretty ='%+2.3f' % lat,
        lon ='%f' % lon,
        lat ='%f' % lat,
        url = url,
        timestamp=str(timestamp),
        small_url = small_url)
   
    if (lon > -122.4 and lon < -122.3 
        and lat > 47.5 and lat < 47.7
        ):
        description += '''\t\t\t<br/>Images not available while Healy is stationed in Seattle<br/><br/>\n'''
    else:
        description += '''\t\t\t<a href="{url}">Full size image</a><br/>
\t\t\t<a href="{url}"><img src="{small_url}"/></a>&nbsp;
'''.format(
        url = url,
        small_url = small_url,
        )
    description += ']]>\n'
# \t\t\t<img width="300" height="225" src="{url}"/>


    name = timestamp.strftime('%d %b %H:%M')

    placemark = kml_placemark(lon, lat, name=name, description=description)
    return placemark

def georss(filename,positions,times):
    '''WARNING: points on y x!!  lat lon
    '''

    o = file(filename,'w')

    # Removed: <language>en</language>   where did I get this requirement?

    o.write('''<?xml version="1.0" encoding="UTF-8"?> 
<feed xmlns:dc="http://purl.org/dc/elements/1.1/" 
  xmlns:georss="http://www.georss.org/georss" 
  xmlns:sy="http://purl.org/rss/1.0/modules/syndication/"
  xmlns="http://www.w3.org/2005/Atom">

  <sy:updatePeriod>hourly</sy:updatePeriod>
  <sy:updateFrequency>1</sy:updateFrequency>

  <title>USCGC Healy Aloftcon Camera {time}</title>   
  <link href="http://vislab-ccom.unh.edu/~schwehr/healy/healy-aloftcon-latest.georss" rel="self"/>
  <id>http://vislab-ccom.unh.edu/~schwehr/healy/healy-aloftcon-latest.kml</id>   
  <updated>{time}</updated>
  <generator uri="http://schwehr.org/">Kurt Schwehr</generator>
'''.format(time=times[0].strftime('%Y-%m-%dT%H:%M:00Z') ) )

# >2007-03-09T09:14:02Z

    for i,pos in enumerate(positions):
        t = times[i]
        ldgo_timestamp = t.strftime('%Y%m%d-%H%M')
        filename = ldgo_timestamp+'.jpeg'
        url = baseurl+'/'+filename
        small_name = build_small_filename(filename)
        small_url = 'http://vislab-ccom.unh.edu/~schwehr/healy/small/'+small_name

        o.write('''
  <entry>
    <title>Aloftcon Image {timestamp}</title>
    <author>       
      <name>USCGC Healy</name>
    </author> 
    <georss:point>{lat} {lon}</georss:point>
    <link href="http://www.uscg.mil/pacarea/cgchealy/aws09/"/>
    <published>{time}</published>     
    <content type="html"><![CDATA[<a href="http://www.uscg.mil/pacarea/cgcHealy/">USCGC HEALY (WAGB-20)</a><br/>
UTC time: {timestamp}<br/>
\t\t\t<a href="http://maps.google.com/?ll={lat},{lon}&z=10">Longitude: {lon} Latitude: {lat}</a> [Google Map location]<br/>
'''.format(
                time=t.strftime('%Y-%m-%dT%H:%M:00Z'),
                lon=pos[0], lat=pos[1],
                timestamp=ldgo_timestamp,
                url=url,
                small_url = small_url
                ))

        if (pos[0] > -122.4 and pos[0] < -122.3 
            and pos[1] > 47.5 and pos[1] < 47.7
            ):
            o.write('''\t\t\tImages not available while Healy is stationed in Seattle<br/>\n''')
        else:
            o.write('''\t\t\t<a href="{url}">Link to full size image</a><br/>
\t\t\t<a href="{url}"><img src="{small_url}"/></a><br/>'''.format(
                url=url,
                small_url = small_url
                ))

        o.write('''
Feed credits: USCG, NSF, LDEO, CCOM/JHC
]]></content>
  </entry>
''' )

# \t\t\t<img width="300" height="225" src="{url}"/> ]]></content>

    o.write('''</feed>
''')


def do_update(now=None,outfile=None):

    if not outfile:
        outfile=file('healy-aloftcon-latest.kml','w')
    o = outfile

    if not now:
        now = datetime.datetime.utcnow()
    print str(now)

    start_time = datetime.datetime(now.year,now.month,now.day,now.hour,minute=1)

    #xml_start(o)
    #kml_start(o)

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
    <name>Healy Aloftcon Camera {time}</name>
'''.format(
            time = cur_time_str,
            reload_time = reload_time.strftime(iso8601_timeformat)
            )
)

    o.write(style)
    o.write('\t<Folder><name>Healy - Lastest images</name>\n')

    
    small_names=[]
    positions = []
    times = []
    for hour_offset in range(10):
        td = datetime.timedelta(hours=hour_offset)
        cur_time = start_time - td

        timestamp = cur_time.strftime('%Y%m%d-%H%M')
        filename = timestamp+'.jpeg'
        url = baseurl+'/'+filename

        try:
            print url
            f = urllib.urlopen(url)
        except:
            sys.stderr.write('Image %s not yet available\n' % (filename,))
            continue

        img = file(filename,'w')
        img.write(f.read())
        img.close()

        #p = 
        try:
            positions.append(image_position(filename))# {'x':p[0],'y':p[1]})
        except:
            sys.stderr.write('Unable to get GPS info from image: %s\n'% (url,))
            continue

        small_name = build_small_filename(filename)
        img_sml = Image.open(filename)
        img_sml.thumbnail((300,225))
        img_sml.save(small_name,'JPEG')

        small_names.append(small_name)

        times.append(cur_time)

        o.write(process_image(filename, url, cur_time, small_url='http://vislab-ccom.unh.edu/~schwehr/healy/small/'+small_name))

    kml_line(o,positions)
    o.write('\t</Folder>\n')

    kml_end(o)

    georss('healy-aloftcon-latest.georss',positions,times)

    print small_names

    o = file('HEADER.html','w')
    o.write(file('HEADER.html.tmpl').read().format(
            time=str(now),
            latest_img = 'small/'+small_names[0]
            ))
    o.close()


if __name__=='__main__':
    do_update()

