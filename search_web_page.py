# this python script creates a function 'url_health_check' that iterates through the list of service urls and identifies if they are healthy

import urllib2
import re
services = ['http://yahoo.com/','http://bing.mdsol.com']


def url_health_check(services):
    for s in services:
       # print s
        html_content = urllib2.urlopen(str(s)).read()

        matches = re.findall('maintenance', html_content);

        u_name = re.findall('User Name', html_content);

        if len(matches) == 0 and len(u_name) != 0:
           print s, ': this site is fine'
        else:
           print s, ':the site is in maintenance'

url_health_check(services)
