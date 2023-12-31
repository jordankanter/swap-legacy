#!/usr/bin/python
"""plist2ttl.py -- interpret PList format as RDF

This is or was http://www.w3.org/2000/10/swap/pim/financial/plist2ttl.py

Converts PList format (as in downloaded back statements etc
USAGE:
  python plist2ttl.py --n3 < foo.xml > foo.rdf
  python plist2ttl.py --n3 foo.xml > foo.rdf
  python plist2ttl.py --rename stmt*.xml
  
  The conversion is only syntactic.  The PList modelling is
  pretty weel thought out, so taking it as defining an effecive
  RDF ontolofy seems to make sense. Rules can then be used to
  define mapping into your favorite ontology.
  

DESIGN NOTES
  
 

REFERENCES

 
We try to stick to:
Python Style Guide
  Author: Guido van Rossum
  http://www.python.org/doc/essays/styleguide.html

   
LICENSE OF THIS CODE

Copyright 2002-2003 World Wide Web Consortium, (Massachusetts
Institute of Technology, European Research Consortium for
Informatics and Mathematics, Keio University). All Rights
Reserved. This work is distributed under the W3C(R) Software License
  http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231
in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE.

This is or was http://www.w3.org/2000/10.swap/pim/plist2ttl.py
"""

__version__ = "$Id: plist2ttl.py,v 1.1 2014-07-23 13:23:05 timbl Exp $"
thisSource = "http://www.w3.org/2000/10.swap/pim/plist2ttl.py"

# from swap.myStore import load, Namespace
# from swap.diag import chatty_flag, progress

import sys, re, os

import xml.dom.minidom




def main(argv):
    filenames = []
    for arg in argv[1:]:  # skip script name
        if arg[0] != "-": # Not an option
            filenames.append(arg)
    if filenames == []:
        fyi("Reading PList document")
        doc = sys.stdin.read()
        fyi("Parsing STDIN PList document")
        contentLines(doc, argv)
    else:
        for fn in filenames:
            f = open(fn, "r")
            doc=f.read()
            fyi("Parsing STDIN PList document %s" % fn)
            contentLines(doc, argv, fn)

def fyi(s):
    pass
#    sys.stderr.write(s+"\n")
    
CR = chr(13)
LF = chr(10)
CRLF = CR + LF
SPACE = chr(32)
TAB = chr(9)


# See qfx2n3.sed 
# Date time maps to \1-\2-\3T\4:\5:\6
dt1 = [re.compile(r'([0-9][0-9][0-9][0-9])([0-9][0-9])([0-9][0-9])([0-9][0-9])([0-9][0-9])([0-9][0-9])'),  "%s-%s-%sT%s:%s:%s"]

# Date maps to \1-\2-\3
dt2 = [re.compile(r'([0-9][0-9][0-9][0-9])([0-9][0-9])([0-9][0-9])'), "%s-%s-%s"]

# Date with Timezone  -- maps to \1-\2-\3T\4:\5:\6\70\800
# Like 20100317075059[-7:PDT]
dt3 = [re.compile('([0-9][0-9][0-9][0-9])([0-9][0-9])([0-9][0-9])([0-9][0-9])([0-9][0-9])([0-9][0-9])\[([-+])([0-9]):[A-Z]*\]'), "%s-%s-%sT%s:%s:%s%s0%s00"]

# Like 20100317075059.000[-7:PDT]
#dt4 = [re.compile('([0-9][0-9][0-9][0-9])([0-9][0-9])([0-9][0-9])([0-9][0-9])([0-9][0-9])([0-9][0-9]).[0-9][0-9][0-9]\[([-+])([0-9]):[A-Z]*\]'), "%s-%s-%sT%s:%s:%s%s0%s00"]
dt4 = [re.compile('([0-9][0-9][0-9][0-9])([0-9][0-9])([0-9][0-9])([0-9][0-9])([0-9][0-9])([0-9][0-9]).000\[([-+])([0-9]):[A-Z]*\]'), "%s-%s-%sT%s:%s:%s%s0%s00"]

# Most complex first
dtcases = [dt4, dt3, dt2, dt1]

def sanitize(tag):
    str = ""
    for ch in tag:
        if ch in ".-": str+= "_"
        else: str += ch
    return str
    
def de_escapeXML(st0):
    return st0.replace('&amp;','&').replace('&lt;', '<').replace('&gt;', '>');


def outln(s)
    sys.stdout.write(s+'\n');

def handleTree(dom):
    for child in self.childNodes:
        if child.nodeType == Node.TEXT_NODE:
    if "-v" in argv:
        sys.stderr.write("handletree "+child.nodeName);
        

def contentLines(doc, argv, fn=None):
    "Process the content as a single buffer"

    n3 = "--n3" in argv
    
    version = "$Id: plist2ttl.py,v 1.1 2014-07-23 13:23:05 timbl Exp $"[1:-1]
    if n3:
        outln( """# Generated by %s""" % version);
        outln( """@prefix p: <http://www.w3.org/ns/pim/plist#>.

<> p:headers [
""");

    


    dom = xml.dom.minidom.parseString(doc);

    handleTree(dom);


   

def _test():
    import sys
    from pprint import pprint
    import doctest, fromPList
    doctest.testmod(fromPList)

    lines = contentLines(open(sys.argv[1]))
    #print lines
    c, lines = findComponents(lines)
    assert lines == []
    pprint(c)
    #unittest.main()

if __name__ == '__main__':
    import sys
    if "--help" in sys.argv[1:] or "-help" in sys.argv[1:]:
        print __doc__
    elif sys.argv[1:2] == ['--test']:
        del sys.argv[1]
        _test()
    else:
        main(sys.argv)



