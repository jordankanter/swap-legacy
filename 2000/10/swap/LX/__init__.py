""" LX is a package of modules for handling semantic web stuff, with
an emphasis on going beyind RDF and handling more expressive logic
languages (FOL), and various inference engines and syntaxes.

"""
__version__ = "$Revision: 1.13 $"
# $Id: __init__.py,v 1.13 2003-09-17 18:09:28 sandro Exp $

# Needed by test.py, and probably random python utils.
__all__ = [
    "language",
    "engine",
    "kb",
    "expr",
    "logic",
    "rdf",
    "namespace",
    "loader",
    "nodepath",
    "sniff",
    "ladder",
    "describer",
    "reporter",
    ] 

# $Log: __init__.py,v $
# Revision 1.13  2003-09-17 18:09:28  sandro
# added reporter
#
# Revision 1.12  2003/09/17 18:01:30  sandro
# more complete module list
#
# Revision 1.11  2003/09/04 03:14:01  sandro
# remove reference to ns.py
#
# Revision 1.10  2003/08/26 11:15:55  sandro
# rolled defaultns.py into namespace.py
#
# Revision 1.9  2003/02/14 17:21:59  sandro
# Switched to import-as-needed for LX languages and engines
#
# Revision 1.8  2003/02/13 19:54:33  sandro
# cleaned up docs to match moving import-all stuff to all.py
#
# Revision 1.7  2003/02/13 19:47:48  sandro
# reformate a little
#
# Revision 1.6  2003/02/13 19:24:21  sandro
# Stopped importing everything, since doing so meant that any use of
# anything in LX/* meant important everything.  We'll need to use LX.all
# or some such if we want them all into one namespace.
#
# Revision 1.5  2003/02/13 17:20:19  sandro
# moved URI-related stuff over to uri.py
#
# Revision 1.4  2003/01/29 06:09:18  sandro
# Major shift in style of LX towards using expr.py.  Added some access
# to otter, via --check.  Works as described in
# http://lists.w3.org/Archives/Public/www-archive/2003Jan/0024
# I don't like this UI; I imagine something more like --engine=otter
# --think, and --language=otter (instead of --otterDump).
# No tests for any of this.
#
# Revision 1.3  2002/08/29 21:02:13  sandro
# passes many more tests, esp handling of variables
#
# Revision 1.2  2002/08/29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which
# is manifesting in description loops  
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

  
