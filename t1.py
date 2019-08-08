import urllib2
import httplib
import re

services = ['http://hgdstrave015.mdsol.com/','http://hgsbxrave001.mdsol.com']
services2 = ["hgsbxrave001.mdsol.com","hgdstrave015.mdsol.com","hgperfrave039.mdsol.com"]

def check_health(services2):
    for s in services:
        html_content = urllib2.urlopen(str(s)).read()

        matches = re.findall('maintenance', html_content);

        u_name = re.findall('User Name', html_content);

        if len(matches) == 0 and len(u_name) != 0: 
           print s,':this site is fine'
        else:
           print s,':the site is in maintenance'

check_health(services)


def get_status_code(host, path="/"):
    """ This function retreives the status code of a website by requesting
        HEAD data from the host. This means that it only requests the headers.
        If the host cannot be reached or something else goes wrong, it returns
        None instead.
    """
    try:
        conn = httplib.HTTPConnection(host)
        conn.request("HEAD", path)
        return conn.getresponse().status
    except StandardError:
        return None


#print get_status_code("stackoverflow.com") # prints 200
#print get_status_code("hgsbxrave001.mdsol.com")
#print get_status_code("hgdstrave015.mdsol.com")
#print get_status_code("paidtimeoff.com") # prints 404


for s in services2:
    print get_status_code(str(s))




    
