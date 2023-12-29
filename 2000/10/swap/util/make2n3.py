#!/usr/bin/python
#
import sys
import string
import os
import re

version = "$Id: make2n3.py,v 1.7 2007-06-26 02:36:17 syosi Exp $"[1:-1]

from swap import notation3  # from http://www.w3.org/2000/10/swap/notation3.py

global verbose
global recursive

def ss(str):
    """Format string for output"""
    return notation3.stringToN3(str)

def macroSubstitute(line, dict):
    return line  #@@@@@@

def convert(path):
    """Convert Makefile format to n3"""
    global nochange
    global verbose
    dict = {}

    print "# http://www.w3.org/DesignIssues/Notation3"
    print "# Generated from", path
    print "# Generated by  ", version
    print
    print "@prefix make: <http://www.w3.org/2000/10/swap/util/make#>."
    print "@prefix ext:  <http://www.w3.org/2000/10/swap/util/make-ext#>."
    print

    input = open(path, "r")
    buf = input.read()  # Read the file
    input.close()
    i = 0
    comment = re.compile(r'^(.*?)#.*$')
    macro = re.compile(r'([-_a-zA-Z0-9\.]+)=(.*)')
    macro1 = re.compile(r'^(.*?)\$([a-zA-Z0-9\$@])(.*)$')
    macron = re.compile(r'^(.*?)\$\(([a-zA-Z0-9\$@]+)\)(.*)$')
    include = re.compile(r'include *([-_a-zA-Z0-9\./,]+)')
    target = re.compile(r'^(.*?)\$@(.*)$')
    dependency = re.compile( r'^([-_a-zA-Z0-9,][-_a-zA-Z0-9\.,]*) *:(.*)$' )
    rule = re.compile(r'^\.([-_a-zA-Z0-9,]*)\.([-_a-zA-Z0-9,]*)')
    recipe = re.compile( r'^\t.*')
    filename = re.compile( r'[-_a-zA-Z0-9\./,]+')
    blank = re.compile(r"^ *$")
    recipeList = []
    subj = None
    lines = []

    while 1:
        lines.append(i)
        j = buf.find("\n", i)
        if j <0: break
        if buf[j-1:j] == "\\":
            buf = buf[:j-1] + " " + buf[j+1:]  # Chop out escaped newline
            continue
        e = j
        if e>i and buf[e-1]=='\r':
            e = e-1
        line = buf[i:e]
        if verbose:  sys.stderr.write("# ... "+line+"\n")
        last = 0
        i = j+1

        k = line.find("#") # Chop comments
        if k >= 0:
            comment = line[k:]
            line = line[:k]
        else:
            comment = ""

        here = 0
        while 1:
            m = macron.match(line, here)
            if not m:
                m = macro1.match(line, here)
                if not m: break
            var = m.group(2)
            if len(var)==1 and var in "$@<>":  # move on
                here = m.start(3)  # skip $$ and don't use the second $
                continue
            res = dict.get(var, None)
            if res == None:
                raise RuntimeError("No macro value for "+var+ (" around line %i:\n"%len(lines))+buf[lines[-2]:i])
            line =  m.group(1) + res + m.group(3) #1
#line[:here] +
        if verbose:  sys.stderr.write("# >>> "+line+"\n")
        m = include.match(line)
        if m:
            path2 = m.group(1)  # @@@@@@@@@@@@ Relative addressing in nested makefiles: @@ won't work
            if verbose: sys.stderr.write("make2n3: including " + path2 + "\n")
            print "# start include", path2
            input2 = open(path2, "r")
            buf2 = input2.read()  # Read the file
            input2.close()
            buf = buf[:i] + buf2 + "# end include"+ path2 +"\n" + buf[i:]
            continue

        m = recipe.search(line)
        if m:
            rec = line[1:]
            if subj[0] == "<":  # If an file not a rule
                while 1:
                    m = target.match(rec)
                    if not m: break
                    rec = m.group(1) + subj[1:-1] + m.group(2)
            recipeList.append(rec)
            continue


        # Not a recipe - if list, dump it now.,
        if len(recipeList) > 0:
            print "%s make:recipeList (" % subj
            for r in recipeList:
                print '    %s' % ss(r)
            print "    )."
            recipeList = []
            subj = None

        m = rule.match(line)
        if m:
            subj = """[make:fromExt "%s"; make:toExt "%s"]""" %(
                        m.group(1), m.group(2))
            if comment != "": print comment
            continue

        m = dependency.search(line)
        if m:
            subj = "<"+m.group(1)+">"
            objl = filename.findall(m.group(2))
            if len(objl) > 0:
                print "%s make:dependsOn <%s>" %(subj, objl[0]),
                for obj in objl[1:]:
                    print ", <%s>" % obj,
                print ".",
            print comment
            continue

        m = macro.match(line)
        if m:
            dict[m.group(1)]=m.group(2)
#           print "# macro %s = %s" %(m.group(1), m.group(2))  #cut
            continue

        m = blank.match(line)
        if m:
            print comment
            continue
        print "#@@", line, comment

def do(path):
    if verbose: sys.stderr.write("# make2n3: converting " + path + "\n")
    return convert(path)
        
######################################## Main program

recursive = 0
nochange = 1
verbose = 0
doall = 0
files = []

for arg in sys.argv[1:]:
    if arg[0:1] == "-":
        if arg == "-?" or arg == "--help":
            print """Convert Makfile format of make(1) to n3 format.

Syntax:    make2n3  <file>

    where <file> can be omitted and if so defaults to Makefile.
    This program was http://www.w3.org/2000/10/swap/util/make2p3.py
    $Id: make2n3.py,v 1.7 2007-06-26 02:36:17 syosi Exp $
    
    -v  verbose
"""
        elif arg == "-v": verbose = 1
        else:
            print """Bad option argument."""
            sys.exit(-1)
    else:
        files.append(arg)

if files == []: files = [ "Makefile" ] # Default to Makefile

for path in files:
    do(path)
