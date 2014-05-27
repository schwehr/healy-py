#!/usr/bin/env python

__author__    = 'Kurt Schwehr'
__version__   = '$Revision: 4799 $'.split()[1]
__revision__  = __version__ # For pylint
__date__ = '$Date: 2006-09-25 11:09:02 -0400 (Mon, 25 Sep 2006) $'.split()[1]
__copyright__ = '2009'

__doc__ ='''
GeoRSS in RSS 2.0.  dc is doublin core

@requires: U{Python<http://python.org/>} >= 2.6

@undocumented: __doc__
@since: 2009-Jul-23
@status: under development

@see: U{RSS 1.0<http://web.resource.org/rss/1.0/spec>}
@see: U{RSS 2.0<http://cyber.law.harvard.edu/rss/rss.html>}
@see: U{Atom 1.0<http://www.ietf.org/rfc/rfc4287.txt">}
'''

from lxml import etree

feed_fields_optional = (
    'language',
    'copyright',
    'managingEditor',
    'webMaster',
    'pubDate',
    'lastBuildDate',
    'category',
    'generator',
    'docs',
    'cloud',
    'ttl',
    'image',
    'rating',
    'textInput',
    'skipHours',
    'skipDays',
    )

item_fields_optional = (
    'link',
    'author',
    'category',
    'comments',
    'enclosure',
    'guid',
    'pubDate',
    'source',
)

class Feed(object):
    def __init__(self, title, description, link, items=None):
        self.fields = {'title':title, 'link':link, 'description':description}
        if items is None:
            self.items = []
        else:
            self.items = items
        self.flags = set()
        self.title = title
        self.description = description
        self.link = link

    def append(self, item):
        self.items.append(item)
        
    def syndication(period='hourly',frequency=1):
        self.syndication=(period,frequency)

    def __getitem__(self,name):
        if isinstance(name,int):
            return self.items[name]
        return self.__dict__[name]

    def __repr__(self):
        print self.__dict__
        title = self.title
        if len(title) > 30: title = title[:30]
        return 'Feed: %s' % (title,)

    def rss_text(self,indent='  '):
        r = ['<?xml version="1.0" encoding="UTF-8"?>']
        ns = ['<rss version="2.0"'] # open rss tag with namespaces
        if 'has_geo' in self.__dict__['flags']: 
            ns.append('xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#"') # FIX: what is up with the #?
        if 'has_dc' in self.flags: 
            ns.append('xmlns:dc="http://purl.org/dc/elements/1.1/"')
        ns.append('>')
        r.append(' '.join(ns))

        r.append('<title>%s</title>' % (self.title,))
        r.append('<link>%s</link>' % (self.link,))
        r.append('<description>%s</description>' % (self.description,))

        for item in self.items:
            r.append(item.rss_text(indent))
                 
        return ('\n'+indent).join(r)+'</rss>\n'

    def __unicode__(self):
        return self.rss_text()

    def __str__(self):
        return str(self.__unicode__())

class Item(object):
    def __init__(self, title=None, description=None, link=None, fields=None):
        'Must have at least one of title or description'
        if title is None and description is None:
            raise AttributeError('Must specify at least the title or description')
        self.fields = {}
        if title       is not None: self.fields['title']       = title
        if description is not None: self.fields['description'] = title
        if link        is not None: self.fields['link']        = title
        if fields is not None:
            self.fields.update(fields) # No checking

    def __setitem__(self,name,value):
        self.fields[name] = value

    def rss_text(self,indent='  '):
        r = []
        for name,value in self.fields.iteritems():
            r.append('<%s>%s</%s>' % (name,value,name) )
        return ''.join(['<item>\n',indent*2,('\n'+indent*2).join(r),'\n',indent,'<item>\n'])

    def __unicode__(self):
        return self.rss_text()

    def __str__(self):
        return str(self.__unicode__())
    

            
if __name__=='__main__':
    f = Feed('Your Expedition','www.your website.com','The latest news from the expedition')
    item = Item('Expedition Launch','http://findingcoral.blogspot.com','Some text here')
    item['guid'] = ''
    item['dc:date'] = '2009-06-08T10:01:39+00:00'
    item['pubDate'] = 'Monday, June 8, 2009 / 10:01pm PST'
    item['geo:lat'] = 49.307940
    item['geo:long'] = -123.080560

    f.append(item)

    print f.__repr__()
    print str(f)
