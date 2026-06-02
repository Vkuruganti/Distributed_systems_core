import urllib2
import re

html_content = urllib2.urlopen('http://www.google.com/').read()

matches = re.findall('maintenance', html_content);

if len(matches) == 0: 
   print 'I did not find anything'
else:
   print 'My string is in the html'
