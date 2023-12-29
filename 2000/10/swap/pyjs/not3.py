#!/usr/local/bin/python
"""
$Id: not3.py,v 1.12 2007-07-17 02:21:15 timbl Exp $

HAND EDITED FOR CONVERSION TO JAVASCRIPT

This module implements a Nptation3 parser, and the final
part of a notation3 serializer.

See also:

Notation 3
http://www.w3.org/DesignIssues/Notation3

Closed World Machine - and RDF Processor
http://www.w3.org/2000/10/swap/cwm

To DO: See also "@@" in comments

- Clean up interfaces
______________________________________________

Module originally by Dan Connolly, includeing notation3
parser and RDF generator. TimBL added RDF stream model
and N3 generation, replaced stream model with use
of common store/formula API.  Yosi Scharf developped
the module, including tests and test harness.

"""


# Python standard libraries
import types, sys
import string
import codecs # python 2-ism; for writing utf-8 in RDF/xml output
import urllib
import re

# SWAP http://www.w3.org/2000/10/swap
from diag import verbosity, setVerbosity, progress
from uripath import refTo, join
import uripath
import RDFSink
from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
from RDFSink import  LITERAL, LITERAL_DT, LITERAL_LANG, ANONYMOUS, SYMBOL
from RDFSink import Logic_NS
import diag

from why import BecauseOfData, becauseSubexpression


# Magic resources we know about


from RDFSink import RDF_type_URI, RDF_NS_URI, DAML_sameAs_URI, parsesTo_URI
from RDFSink import RDF_spec, List_NS, uniqueURI
from local_decimal import Decimal

ADDED_HASH = "#"  # Stop where we use this in case we want to remove it!
# This is the hash on namespace URIs


from RDFSink import N3_first, N3_rest, N3_nil, N3_li, N3_List, N3_Empty

LOG_implies_URI = "http://www.w3.org/2000/10/swap/log#implies"

INTEGER_DATATYPE = "http://www.w3.org/2001/XMLSchema#integer"
FLOAT_DATATYPE = "http://www.w3.org/2001/XMLSchema#double"
DECIMAL_DATATYPE = "http://www.w3.org/2001/XMLSchema#decimal"
BOOLEAN_DATATYPE = "http://www.w3.org/2001/XMLSchema#boolean"

option_noregen = 0   # If set, do not regenerate genids on output

# @@ I18n - the notname chars need extending for well known unicode non-text
# characters. The XML spec switched to assuming unknown things were name
# characaters.
# _namechars = string.lowercase + string.uppercase + string.digits + '_-'
_notQNameChars = "\t\r\n !\"#$%&'()*.,+/;<=>?@[\\]^`{|}~" # else valid qname :-/
_notNameChars = _notQNameChars + ":"  # Assume anything else valid name :-/
_rdfns = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'


N3CommentCharacter = "#"     # For unix script #! compatabilty

########################################## Parse string to sink
#
# Regular expressions:   In pythn, match() is anchored, serarch() not. In js, just exec()
eol = re.compile(r'^[ \t]*(#[^\n]*)?\r?\n')     # end  of line, poss. w/comment
eof = re.compile(r'^[ \t]*(#[^\n]*)?$')         # end  of file, poss. w/comment
ws = re.compile(r'^[ \t]*')                     # Whitespace not including NL
signed_integer = re.compile(r'^[-+]?[0-9]+')    # integer
number_syntax = re.compile(r'^(?P<integer>[-+]?[0-9]+)(?P<decimal>\.[0-9]+)?(?P<exponent>e[-+]?[0-9]+)?')
digitstring = re.compile(r'^[0-9]+')            # Unsigned integer      
interesting = re.compile(r'[\\\r\n\"]')   # Things to be quoted @@ pyjs: Anchar all OTHER regexps to ^
langcode = re.compile(r'^[a-zA-Z0-9]+(-[a-zA-Z0-9]+)?')
#"




class SinkParser:
    def __init__(self, store, openFormula=None, thisDoc="", baseURI=None,
                 genPrefix = "", metaURI=None, flags="",
                 why=None):
        """ note: namespace names should *not* end in #;
        the # will get added during qname processing """

        self._bindings = {}
        self._flags = flags
        if thisDoc != "":
            assertFudge( ':' in thisDoc, "Document URI not absolute: " + thisDoc)
            self._bindings[""] = thisDoc + "#"  # default

        self._store = store
        if genPrefix: store.setGenPrefix(genPrefix) # pass it on
        
        self._thisDoc = thisDoc
        self.source = store.sym(thisDoc)
        self.lines = 0              # for error handling
        self.statementCount = 0     # for stats only
        self.startOfLine = 0        # For calculating character number
        self.previousLine = 0       # For calculating character number
        self._genPrefix = genPrefix
        self.keywords = ['a', 'this', 'bind', 'has', 'is', 'of', 'true', 'false' ]
        self.keywordsSet = 0    # Then only can others be considerd qnames
        self._anonymousNodes = {} # Dict of anon nodes already declared ln: Term
        self._variables  = {}
        self._parentVariables = {}
        self._reason = why      # Why the parser was asked to parse this

        self._reason2 = None    # Why these triples
        if diag.tracking: self._reason2 = BecauseOfData(
                        store.newSymbol(thisDoc), self._reason) 

        if baseURI: self._baseURI = baseURI
        else:
            if thisDoc:
                self._baseURI = thisDoc
            else:
                self._baseURI = None

        assertFudge( not self._baseURI or ':' in self._baseURI)

        if not self._genPrefix:
            if self._thisDoc: self._genPrefix = self._thisDoc + "#_g"
            else: self._genPrefix = uniqueURI()

        if openFormula ==None:
            if self._thisDoc:
                self._formula = store.newFormula(thisDoc + "#_formula")
            else:
                self._formula = store.newFormula()
        else:
            self._formula = openFormula
        

        self._context = self._formula
        self._parentContext = None
        
        # META INFROMATION NOT THE PARSER'S JOB (PYJS)
        
    def here(self, i):

        return self._genPrefix + '_L' + self.lines +'C' +(
                                            i - self.startOfLine + 1) # "%s_L%iC%i"
        
    def formula(self):
        return self._formula
    
    def loadStream(self, stream):
        return self.loadBuf(stream.read())   # Not ideal

    def loadBuf(self, buf):
        """Parses a buffer and returns its top level formula"""
        self.startDoc()
        self.feed(buf)
        return self.endDoc()    # self._formula


    def feed(self, octets):
        """Feed an octet stream tothe parser
        
        if BadSyntax is raised, the string
        passed in the exception object is the
        remainder after any statements have been parsed.
        So if there is more data to feed to the
        parser, it should be straightforward to recover."""
        str = octets.decode('utf-8')
        i = 0
        while i >= 0:
            j = self.skipSpace(str, i)
            if j<0: return

            i = self.directiveOrStatement(str,j)
            if i<0:
                raise BadSyntax(self._thisDoc, self.lines, str, j,
                                    "expected directive or statement")

    def directiveOrStatement(self, str,h):
    
            i = self.skipSpace(str, h)
            if i<0: return i   # EOF

            j = self.directive(str, i)
            if j>=0: return  self.checkDot(str,j)
            
            j = self.statement(str, i)
            if j>=0: return self.checkDot(str,j)
            
            return j


    #@@I18N
 #   global _notNameChars
    #_namechars = string.lowercase + string.uppercase + string.digits + '_-'
        
    def tok(self, tok, str, i):
        """Check for keyword.  Space must have been stripped on entry and
        we must not be at end of file."""
        
        # assertFudge( tok[0] not in _notNameChars) # not for punctuation pyjs
        # was: string.whitespace which is '\t\n\x0b\x0c\r \xa0' -- not ascii
        whitespace = '\t\n\x0b\x0c\r ' 
        if str[i:i+1] == "@":
            i = i+1
        else:
            if tok not in self.keywords:
                return -1   # No, this has neither keywords declaration nor "@"

        k = i + len(tok)
        if (str[i:k] == tok
            and (str[k] in  _notQNameChars )): 
            return k
        else:
            return -1

    def directive(self, str, i):
        j = self.skipSpace(str, i)
	if j<0: return j # eof
	res = []
	
	j = self.tok('bind', str, i)        # implied "#". Obsolete.
	if j>0: raise BadSyntax(self._thisDoc, self.lines, str, i,
				"keyword bind is obsolete: use @prefix")

	j = self.tok('keywords', str, i)
	if j>0:
	    i = self.commaSeparatedList(str, j, res, false)
	    if i < 0:
		raise  BadSyntax(self._thisDoc, self.lines, str, i,
		    "'@keywords' needs comma separated list of words")
	    self.setKeywords(res[:])
	    if diag.chatty_flag > 80: progress("Keywords ", self.keywords)
	    return i


	j = self.tok('forAll', str, i)
	if j > 0:
	    i = self.commaSeparatedList(str, j, res, true)
	    if i <0: raise BadSyntax(self._thisDoc, self.lines, str, i,
			"Bad variable list after @forAll")
	    for x in res:
		#self._context.declareUniversal(x)
                if x not in self._variables or x in self._parentVariables:
                    self._variables[x] =  self._context.newUniversal(x)
            return i

        j = self.tok('forSome', str, i)
        if j > 0:
            i = self. commaSeparatedList(str, j, res, self.uri_ref2)
            if i <0: raise BadSyntax(self._thisDoc, self.lines, str, i,
                    "Bad variable list after @forSome")
            for x in res:
                self._context.declareExistential(x)
            return i

	j=self.tok('prefix', str, i)   # no implied "#"
	if j >= 0:
            t = []
            i = self.qname(str, j, t)
            if i<0: raise BadSyntax(self._thisDoc, self.lines, str, j,
                                "expected qname after @prefix")
            j = self.uri_ref2(str, i, t)
            if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i,
                                "expected <uriref> after @prefix _qname_")
            ns = t[1].uri # pyjs was uriref()
            if self._baseURI:
                ns = join(self._baseURI, ns)
            else:
                assertFudge( ":" in ns, "With no base URI, cannot handle relative URI for NS")
            assertFudge( ':' in ns) # must be absolute
            self._bindings[t[0][0]] = ns;
            self.bind(t[0][0], hexify(ns))
            return j

	j=self.tok('base', str, i)      # Added 2007/7/7
	if j >= 0:
            t = []
            i = self.uri_ref2(str, j, t)
            if i<0: raise BadSyntax(self._thisDoc, self.lines, str, j,
                                "expected <uri> after @base ")
            ns = t[0].uri # pyjs was uriref()

            if self._baseURI:
                ns = join(self._baseURI, ns)
            else:
                raise BadSyntax(self._thisDoc, self.lines, str, j,
                    "With no previous base URI, cannot use relative URI in @base  <"+ns+">")
            assertFudge( ':' in ns) # must be absolute
            self._baseURI = ns
            return i

        return -1  # Not a directive, could be something else.


    def bind(self, qn, uri):
#       assertFudge( isinstance(uri,     # pyjs
#                   types.StringType), "Any unicode must be %x-encoded already")
        
        if qn == "":
#            self._store.setDefaultNamespace(uri)
            pass # pyjs
        else:
            self._store.setPrefixForURI(qn, uri)

    def setKeywords(self, k):
        "Takes a list of strings"
        if k == None:
            self.keywordsSet = 0
        else:
            self.keywords = k
            self.keywordsSet = 1


    def startDoc(self):
        pass
        #self._store.startDoc()

    def endDoc(self):
        """Signal end of document and stop parsing. returns formula"""
        # self._store.endDoc(self._formula)  # don't canonicalize yet
        return self._formula

    def makeStatement(self, quad):
        #$$$$$$$$$$$$$$$$$$$$$
#        alert( "Parser output SPO: " + [quad[2], quad[1], quad[3]] )
#        self._store.makeStatement(quad, why=self._reason2)
        quad[0].add(quad[2], quad[1], quad[3], self.source)
        self.statementCount += 1



    def statement(self, str, i):
        r = []

        i = self.object(str, i, r)  #  Allow literal for subject - extends RDF 
        if i<0: return i

        j = self.property_list(str, i, r[0])

        if j<0: raise BadSyntax(self._thisDoc, self.lines,
                                    str, i, "expected propertylist")
        return j

    def subject(self, str, i, res):
        return self.item(str, i, res)

    def verb(self, str, i, res):
        """ has _prop_
        is _prop_ of
        a
        =
        _prop_
        >- prop ->
        <- prop -<
        _operator_"""

        j = self.skipSpace(str, i)
        if j<0:return j # eof
        
        r = []

        j = self.tok('has', str, i)
        if j>=0:
            i = self.prop(str, j, r)
            if i < 0: raise BadSyntax(self._thisDoc, self.lines,
                                str, j, "expected property after 'has'")
            res.append(('->', r[0]))
            return i

        j = self.tok('is', str, i)
        if j>=0:
            i = self.prop(str, j, r)
            if i < 0: raise BadSyntax(self._thisDoc, self.lines, str, j,
                                "expected <property> after 'is'")
            j = self.skipSpace(str, i)
            if j<0:
                raise BadSyntax(self._thisDoc, self.lines, str, i,
                            "End of file found, expected property after 'is'")
                return j # eof
            i=j
            j = self.tok('of', str, i)
            if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i,
                                "expected 'of' after 'is' <prop>")
            res.append(('<-', r[0]))
            return j

        j = self.tok('a', str, i)
        if j>=0:
            res.append(('->', self._store.newSymbol(RDF_type_URI)))
            return j

            
        if str[i:i+2] == "<=":
            res.append(('<-', self._store.newSymbol(Logic_NS+"implies")))
            return i+2

        if str[i:i+1] == "=":
            if str[i+1:i+2] == ">":
                res.append(('->', self._store.newSymbol(Logic_NS+"implies")))
                return i+2
            res.append(('->', self._store.newSymbol(DAML_sameAs_URI)))
            return i+1

        if str[i:i+2] == ":=":
            # patch file relates two formulae, uses this    @@ really?
            res.append(('->', Logic_NS+"becomes")) 
            return i+2

        j = self.prop(str, i, r)
        if j >= 0:
            res.append(('->', r[0]))
            return j

        if str[i:i+2] == ">-" or str[i:i+2] == "<-":
            raise BadSyntax(self._thisDoc, self.lines, str, j,
                                        ">- ... -> syntax is obsolete.")

        return -1

    def prop(self, str, i, res):
        return self.item(str, i, res)

    def item(self, str, i, res):
        return self.path(str, i, res)

    def blankNode(self, uri):
#       if "B" not in self._flags:
            return self._context.bnode(uri, self._reason2)
#       return self._context.blankNode();  # pyjs
        
#       x = self._context.newSymbol(uri)
#       self._context.declareExistential(x)
#       return x
        
    def path(self, str, i, res):
        """Parse the path production.
        """
        j = self.nodeOrLiteral(str, i, res)
        if j<0: return j  # nope

        while str[j:j+1] in "!^.":  # no spaces, must follow exactly (?)
            ch = str[j:j+1]     # @@ Allow "." followed IMMEDIATELY by a node.
            if ch == ".":
                ahead = str[j+1:j+2]
                if not ahead or (ahead in _notNameChars
                            and ahead not in ":?<[{("): break
            subj = res.pop()
            obj = self.blankNode(self.here(j))
            j = self.node(str, j+1, res)
            if j<0: raise BadSyntax(self._thisDoc, self.lines, str, j,
                            "EOF found in middle of path syntax")
            pred = res.pop()
            if ch == "^": # Reverse traverse
                self.makeStatement((self._context, pred, obj, subj)) 
            else:
                self.makeStatement((self._context, pred, subj, obj)) 
            res.append(obj)
        return j

    def anonymousNode(self, ln):
        """Remember or generate a term for one of these _: anonymous nodes"""
        term = self._anonymousNodes[ln]  # pyjs
        if term: return term   # pyjs
        term = self._store.newBlankNode(self._context, self._reason2)
        self._anonymousNodes[ln] = term
        return term

    def node(self, str, i, res, subjectAlready=None):
        """Parse the <node> production.
        Space is now skipped once at the beginning
        instead of in multipe calls to self.skipSpace().
        """
        subj = subjectAlready

        j = self.skipSpace(str,i)
        if j<0: return j #eof
        i=j
        ch = str[i:i+1]  # Quick 1-character checks first:

        if ch == "[":
            bnodeID = self.here(i)
            j=self.skipSpace(str,i+1)
            if j<0: raise BadSyntax(self._thisDoc,
                                    self.lines, str, i, "EOF after '['")
            if str[j:j+1] == "=":     # Hack for "is"  binding name to anon node
                i = j+1
                objs = []
                j = self.objectList(str, i, objs);
                if j>=0:
                    subj = objs[0]
                    if len(objs)>1:
                        for obj in objs:
                            self.makeStatement((self._context,
                                                self._store.newSymbol(DAML_sameAs_URI),
                                                subj, obj))
                    j = self.skipSpace(str, j)
                    if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i,
                        "EOF when objectList expected after [ = ")
                    if str[j:j+1] == ";":
                        j=j+1
                else:
                    raise BadSyntax(self._thisDoc, self.lines, str, i,
                                        "objectList expected after [= ")

            if subj is None:
                subj=self.blankNode(bnodeID)

            i = self.property_list(str, j, subj)
            if i<0: raise BadSyntax(self._thisDoc, self.lines, str, j,
                                "property_list expected")

            j = self.skipSpace(str, i)
            if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i,
                "EOF when ']' expected after [ <propertyList>")
            if str[j:j+1] != "]":
                raise BadSyntax(self._thisDoc,
                                    self.lines, str, j, "']' expected")
            res.append(subj)
            return j+1

        if ch == "{":
            ch2 = str[i+1:i+2]
            if ch2 == '$':
                i += 1
                j = i + 1
                mylist = []
                first_run = True
                while 1:
                    i = self.skipSpace(str, j)
                    if i<0: raise BadSyntax(self._thisDoc, self.lines, str, i,
                                                    "needed '$}', found end.")                    
                    if str[i:i+2] == '$}':
                        j = i+2
                        break

                    if not first_run:
                        if str[i:i+1] == ',':
                            i+=1
                        else:
                            raise BadSyntax(self._thisDoc, self.lines,
                                                str, i, "expected: ','")
                    else: first_run = False
                    
                    item = []
                    j = self.item(str,i, item) #@@@@@ should be path, was object
                    if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i,
                                            "expected item in set or '$}'")
                    mylist.append(item[0])
                res.append(self._store.newSet(mylist, self._context))
                return j
            else:
                j=i+1
                oldParentContext = self._parentContext
                self._parentContext = self._context
                parentAnonymousNodes = self._anonymousNodes
                grandParentVariables = self._parentVariables
                self._parentVariables = self._variables
                self._anonymousNodes = {}
                self._variables = self._variables.copy()
                reason2 = self._reason2
                self._reason2 = becauseSubexpression
                if subj is None: subj = self._store.newFormula()
                self._context = subj
                
                while 1:
                    i = self.skipSpace(str, j)
                    if i<0: raise BadSyntax(self._thisDoc, self.lines,
                                    str, i, "needed '}', found end.")
                    
                    if str[i:i+1] == "}":
                        j = i+1
                        break
                    
                    j = self.directiveOrStatement(str,i)
                    if j<0: raise BadSyntax(self._thisDoc, self.lines,
                                    str, i, "expected statement or '}'")

                self._anonymousNodes = parentAnonymousNodes
                self._variables = self._parentVariables
                self._parentVariables = grandParentVariables
                self._context = self._parentContext
                self._reason2 = reason2
                self._parentContext = oldParentContext
                res.append(subj.close())   #  No use until closed
                return j

        if ch == "(":
            thing_type = self._store.newList
            ch2 = str[i+1:i+2]
            if ch2 == '$':
                thing_type = self._store.newSet
                i += 1
            j=i+1

            mylist = []
            while 1:
                i = self.skipSpace(str, j)
                if i<0: raise BadSyntax(self._thisDoc, self.lines,
                                    str, i, "needed ')', found end.")                    
                if str[i:i+1] == ')':
                    j = i+1
                    break

                item = []
                j = self.item(str,i, item) #@@@@@ should be path, was object
                if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i,
                                        "expected item in list or ')'")
                mylist.append(item[0])
            res.append(thing_type(mylist, self._context))
            return j

        j = self.tok('this', str, i)   # This context
        if j>=0:
            raise BadSyntax(self._thisDoc, self.lines, str, i,
                "Keyword 'this' was ancient N3. Now use @forSome and @forAll keywords.")
            res.append(self._context)
            return j

        #booleans
        j = self.tok('true', str, i)
        if j>=0:
            res.append(True)
            return j
        j = self.tok('false', str, i)
        if j>=0:
            res.append(False)
            return j

        if subj is None:   # If this can be a named node, then check for a name.
            j = self.uri_ref2(str, i, res)
            if j >= 0:
                return j

        return -1
        
    def property_list(self, str, i, subj):
        """Parse property list
        Leaves the terminating punctuation in the buffer
        """
        while 1:
            j = self.skipSpace(str, i)
            if j<0:
                raise BadSyntax(self._thisDoc, self.lines, str, i,
                            "EOF found when expected verb in property list")
                return j #eof

            if str[j:j+2] ==":-":
                i = j + 2
                res = []
                j = self.node(str, i, res, subj)
                if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i,
                                        "bad {} or () or [] node after :- ")
                i=j
                continue
            i=j
            v = []
            j = self.verb(str, i, v)
            if j<=0:
                return i # void but valid

            objs = []
            i = self.objectList(str, j, objs)
            if i<0: raise BadSyntax(self._thisDoc, self.lines, str, j,
                                                        "objectList expected")
            for obj in objs:
                pairFudge = v[0]
                dir = pairFudge[0]
                sym = pairFudge[1] 
                if dir == '->':
                    self.makeStatement((self._context, sym, subj, obj))
                else:
                    self.makeStatement((self._context, sym, obj, subj))

            j = self.skipSpace(str, i)
            if j<0:
                raise BadSyntax(self._thisDoc, self.lines, str, j,
                                                "EOF found in list of objects")
                return j #eof
            if str[i:i+1] != ";":
                return i
            i = i+1 # skip semicolon and continue

    def commaSeparatedList(self, str, j, res, ofUris):
	"""return value: -1 bad syntax; >1 new position in str
	res has things found appended
	
	Used to use a final value of the function to be called, e.g. this.bareWord
	but passing the function didn't work fo js converion pyjs
	"""
	i = self.skipSpace(str, j)
	if i<0:
	    raise BadSyntax(self._thisDoc, self.lines, str, i,
				    "EOF found expecting comma sep list")
	    return i
	if str[i] == ".": return j  # empty list is OK
	if ofUris:
	    i = this.uri_ref2(str, i, res)
	else:
	    i = self.bareWord(str, i, res)
	if i<0: return -1
	
	while 1:
	    j = self.skipSpace(str, i)
	    if j<0: return j # eof
	    ch = str[j:j+1]  
	    if ch != ",":
		if ch != ".":
		    return -1
		return j    # Found  but not swallowed "."
	    if ofUris:
		i = this.uri_ref2(str, j+1, res)
	    else:
		i = self.bareWord(str, j+1, res)
	    if i<0:
		raise BadSyntax(self._thisDoc, self.lines, str, i,
						"bad list content")
		return i

    def objectList(self, str, i, res):
        i = self.object(str, i, res)
        if i<0: return -1
        while 1:
            j = self.skipSpace(str, i)
            if j<0:
                raise BadSyntax(self._thisDoc, self.lines, str, j,
                                    "EOF found after object")
                return j #eof
            if str[j:j+1] != ",":
                return j    # Found something else!
            i = self.object(str, j+1, res)
            if i<0: return i

    def checkDot(self, str, i):
            j = self.skipSpace(str, i)
            if j<0: return j #eof
            if str[j:j+1] == ".":
                return j+1  # skip
            if str[j:j+1] == "}":
                return j     # don't skip it
            if str[j:j+1] == "]":
                return j
            raise BadSyntax(self._thisDoc, self.lines,
                    str, j, "expected '.' or '}' or ']' at end of statement")
            return i


    def uri_ref2(self, str, i, res):
        """Generate uri from n3 representation.

        Note that the RDF convention of directly concatenating
        NS and local name is now used though I prefer inserting a '#'
        to make the namesapces look more like what XML folks expect.
        """
        qn = []
        j = self.qname(str, i, qn)
        if j>=0:
            pairFudge = qn[0]
            pfx = pairFudge[0]
            ln = pairFudge[1] 
            if pfx is None:
                assertFudge( 0, "not used?")
                ns = self._baseURI + ADDED_HASH
            else:
                ns = self._bindings[pfx]
                if not ns:  # @@ pyjs should test undefined
                    if pfx == "_":  # Magic prefix 2001/05/30, can be overridden
                        res.append(self.anonymousNode(ln))
                        return j
                    raise BadSyntax(self._thisDoc, self.lines, str, i,
                                'Prefix '+pfx+' not bound.')
            symb = self._store.newSymbol(ns + ln)
            if symb in self._variables:
                res.append(self._variables[symb])
            else:
                res.append(symb) # @@@ "#" CONVENTION
            return j

        
        i = self.skipSpace(str, i)
        if i<0: return -1

        if str[i] == "?":
            v = []
            j = self.variable(str,i,v)
            if j>0:              #Forget varibles as a class, only in context.
                res.append(v[0])
                return j
            return -1

        elif str[i]=="<":
            i = i + 1
            st = i
            while i < len(str):
                if str[i] == ">":
                    uref = str[st:i] # the join should dealt with "":
                    if self._baseURI:
                        uref = uripath.join(self._baseURI, uref)
                    else:
                        assertFudge( ":" in uref, \
                            "With no base URI, cannot deal with relative URIs")
                    if str[i-1:i]=="#" and not uref[-1:]=="#":
                        uref = uref + "#" # She meant it! Weirdness in urlparse?
                    symb = self._store.newSymbol(uref)
                    if symb in self._variables:
                        res.append(self._variables[symb])
                    else:
                        res.append(symb)
                    return i+1
                i = i + 1
            raise BadSyntax(self._thisDoc, self.lines, str, j,
                            "unterminated URI reference")

        elif self.keywordsSet:
            v = []
            j = self.bareWord(str,i,v)
            if j<0: return -1      #Forget varibles as a class, only in context.
            if v[0] in self.keywords:
                raise BadSyntax(self._thisDoc, self.lines, str, i,
                    'Keyword "'+v[0]+'" not allowed here.')
            res.append(self._store.newSymbol(self._bindings[""]+v[0]))
            return j
        else:
            return -1

    def skipSpace(self, str, i):
        """Skip white space, newlines and comments.
        return -1 if EOF, else position of first non-ws character"""
        while 1:
            eol.lastIndex = 0
            m = eol.execFudge(str.slice(i))
	    if (m == None): break
	    self.lines = self.lines + 1
	    i += eol.lastIndex   # Point to first character unmatched
	    self.previousLine = self.startOfLine
	    self.startOfLine = i
	    tabulator.log.debug('N3 line '+self.lines+ ' ' +
		str.slice(self.previousLine, self.startOfLine))  # pyjs
	ws.lastIndex = 0
	m = ws.execFudge(str.slice(i))
	if m != None and m[0] != "":
	    i += ws.lastIndex
	if i ==len(str): return -1
#	m = eof.execFudge(str.slice(i))
#	if m != None: return -1
	return i

    def variable(self, str, i, res):
        """     ?abc -> variable(:abc)
        """

        j = self.skipSpace(str, i)
        if j<0: return -1

        if str[j:j+1] != "?": return -1
        j=j+1
        i = j
        if str[j] in "0123456789-":
            raise BadSyntax(self._thisDoc, self.lines, str, j,
                            "Varible name can't start with '"+str[j]+"s'")
            return -1
        while i <len(str) and str[i] not in _notNameChars:
            i = i+1
        if self._parentContext == None:
            raise BadSyntax(self._thisDoc, self.lines, str, j,
                "Can't use ?xxx syntax for variable in outermost level: "
                + str[j-1:i])
        
        res.append(self._store.variable(str[j:i]))  # @@ pyjs

#        varURI = self._store.newSymbol(self._baseURI + "#" +str[j:i])
#        if varURI not in self._parentVariables:
#            self._parentVariables[varURI] = self._parentContext.newUniversal(varURI
#                            , self._reason2) 
#        res.append(self._parentVariables[varURI])
        return i

    def bareWord(self, str, i, res):
	"""	abc -> :abc
  	"""
	j = self.skipSpace(str, i)
	if j<0: return -1
	
	ch = str[j]  #pyjs
	if ch in "0123456789-": return -1   # pyjs
	if ch in _notNameChars: return -1
        i = j
        while i <len(str) and str[i] not in _notNameChars:
            i = i+1
        res.append(str[j:i])
        return i

    def qname(self, str, i, res):
        """
        xyz:def -> ('xyz', 'def')
        If not in keywords and keywordsSet: def -> ('', 'def')
        :def -> ('', 'def')    
        """

        i = self.skipSpace(str, i)
        if i<0: return -1

        c = str[i]
        if c in "0123456789-+": return -1
        if c not in _notNameChars:
            ln = c
            i = i + 1
            while i < len(str):
                c = str[i]
                if c not in _notNameChars:
                    ln = ln + c
                    i = i + 1
                else: break
        else: # First character is non-alpha
            ln = ''   # Was:  None - TBL (why? useful?)

        if i<len(str) and str[i] == ':':
            pfx = ln
            i = i + 1
            ln = ''
            while i < len(str):
                c = str[i]
                if c not in _notNameChars:
                    ln = ln + c
                    i = i + 1
                else: break

            res.append((pfx, ln))
            return i

        else:  # delimiter was not ":"
            if ln and self.keywordsSet and ln not in self.keywords:
                res.append(('', ln))
                return i
            return -1
            
    def object(self, str, i, res):
        j = self.subject(str, i, res)
        if j>= 0:
            return j
        else:
            j = self.skipSpace(str, i)
            if j<0: return -1
            else: i=j

            if str[i]=='"':
                if str[i:i+3] == '"""': delim = '"""'
                else: delim = '"'
                i = i + len(delim)

                pairFudge = self.strconst(str, i, delim)
                j = pairFudge[0]
                s = pairFudge[1]

                res.append(self._store.literal(s))
                progress("New string const ", s, j)
                return j
            else:
                return -1

    def nodeOrLiteral(self, str, i, res):
	j = self.node(str, i, res)
	if j>= 0:
	    return j
	else:
	    j = self.skipSpace(str, i)
	    if j<0: return -1
	    else: i=j

	    ch = str[i]
	    if ch in "-+0987654321":
		number_syntax.lastIndex = 0
		m = number_syntax.execFudge(str.slice(i))
		if m == None:
		    raise BadSyntax(self._thisDoc, self.lines, str, i,
				"Bad number syntax")
		j = i + number_syntax.lastIndex
                val = str[i:j]
                if 'e' in val:  # canonicalization is useful
                    res.append(self._store.literal(parseFloat(val),
                        undefined, kb.sym(FLOAT_DATATYPE)))
                elif '.' in str[i:j]:
                    res.append(self._store.literal(parseFloat(val),
                        undefined, kb.sym(DECIMAL_DATATYPE)))
                else:
                    res.append(self._store.literal(parseInt(val),
                        undefined, kb.sym(INTEGER_DATATYPE)))

#                
#		if m.group('exponent') != None: # includes decimal exponent
##@@ pyjs	    res.append(float(str[i:j]))  # pyjs 'float' reseves word in js
#		    res.append(str[i:j]-0)  # See "JS the definitive Guide" p164
##		    res.append(self._store.newLiteral(str[i:j],
#			self._store.newSymbol(FLOAT_DATATYPE)))
#                elif m.group('decimal') != None:
#                    res.append(Decimal(str[i:j]))
#		else:
# @@ pyjs	    res.append(long(str[i:j]))    # long is reserved word in js
#		    res.append(str[i:j]-0)
#		    res.append(self._store.newLiteral(str[i:j],
#			self._store.newSymbol(INTEGER_DATATYPE)))
		return j

	    if str[i]=='"':
		if str[i:i+3] == '"""': delim = '"""'
		else: delim = '"'
                i = i + len(delim)

                dt = None
                pairFudge = self.strconst(str, i, delim)
                j = pairFudge[0]
                s = pairFudge[1]
                lang = None
                if str[j:j+1] == "@":  # Language?
                    langcode.lastIndex = 0;
                    m = langcode.execFudge(str.slice(j+1))
                    if m == None:
                        raise BadSyntax(self._thisDoc, startline, str, i,
                        "Bad language code syntax on string literal, after @")
                    i = langcode.lastIndex + j + 1;
                    lang = str[j+1:i]
                    j = i
                if str[j:j+2] == "^^":
                    res2 = []
                    j = self.uri_ref2(str, j+2, res2) # Read datatype URI
                    dt = res2[0]
                res.append(self._store.literal(s, lang, dt))
                return j
            else:
                return -1

    def strconst(self, str, i, delim):
        """parse an N3 string constant delimited by delim.
        return index, val
        """


        j = i
#        ustr = u""   # Empty unicode string
        ustr = ""   # Empty unicode string  fudge
        startline = self.lines # Remember where for error messages
        while j<len(str):
            i = j + len(delim)
            if str[j:i] == delim: # done.
                return i, ustr

            if str[j] == '"':
                ustr = ustr + '"'
                j = j + 1
                continue
            interesting.lastIndex = 0
            m = interesting.execFudge(str.slice(j))  # was str[j:].
            # Note for pos param to work, MUST be compiled  ... re bug?
            if not m:
                raise BadSyntax(self._thisDoc, startline, str, j,
                        "Closing quote missing in string at ^ in "+str[j-20:j]+"^"+str[j:j+20]) # we at least have to find a quote
            i = j + interesting.lastIndex - 1 # The start of this match  [sic - why?]
            
#           try:
            ustr = ustr + str[j:i]
#           except UnicodeError:
#               err = ""
#               for c in str[j:i]:
#                   err = err + (" %02x" % ord(c))
#               streason = sys.exc_info()[1].__str__()
#               raise BadSyntax(self._thisDoc, startline, str, j,
#               "Unicode error appending characters %s to string, because\n\t%s"
#                               % (err, streason))
                
#           print "@@@ i = ",i, " j=",j, "m.end=", m.end()

            ch = str[i]
            if ch == '"':
                j = i
                continue
            elif ch == "\r":   # Strip carriage returns
                j = i+1
                continue
            elif ch == "\n":
                if delim == '"':
                    raise BadSyntax(self._thisDoc, startline, str, i,
                                    "newline found in string literal")
                self.lines = self.lines + 1
                ustr = ustr + ch
                j = i + 1
                self.previousLine = self.startOfLine
                self.startOfLine = j

            elif ch == "\\":
                j = i + 1
                ch = str[j:j+1]  # Will be empty if string ends
                if not ch:
                    raise BadSyntax(self._thisDoc, startline, str, i,
                                    "unterminated string literal (2)")
                k = string.find('abfrtvn\\"', ch)
                if k >= 0:
                    uch = '\a\b\f\r\t\v\n\\"'[k]
                    ustr = ustr + uch
                    j = j + 1
                elif ch == "u":
                    pairFudge = self.uEscape(str, j+1, startline)
                    j = pairFudge[0]
                    ch = pairFudge[1]
                    ustr = ustr + ch
                elif ch == "U":
                    pairFudge = self.UEscape(str, j+1, startline)
                    j = pairFudge[0]
                    ch = pairFudge[1]
                    ustr = ustr + ch
                else:
                    raise BadSyntax(self._thisDoc, self.lines, str, i,
                                    "bad escape")

        raise BadSyntax(self._thisDoc, self.lines, str, i,
                        "unterminated string literal")


    def uEscape(self, str, i, startline):
        j = i
        count = 0
        value = 0
        while count < 4:  # Get 4 more characters
            chFudge = str[j:j+1]
            ch = chFudge.lower() 
                # sbp http://ilrt.org/discovery/chatlogs/rdfig/2002-07-05
            j = j + 1
            if ch == "":
                raise BadSyntax(self._thisDoc, startline, str, i,
                                "unterminated string literal(3)")
            k = string.find("0123456789abcdef", ch)
            if k < 0:
                raise BadSyntax(self._thisDoc, startline, str, i,
                                "bad string literal hex escape")
            value = value * 16 + k
            count = count + 1
        uch = unichr(value)
        return j, uch

    def UEscape(self, str, i, startline):
        j = i
        count = 0
        value = '\\U'
        while count < 8:  # Get 8 more characters
            chFudge = str[j:j+1]
            ch = chFudge.lower() 
            # sbp http://ilrt.org/discovery/chatlogs/rdfig/2002-07-05
            j = j + 1
            if ch == "":
                raise BadSyntax(self._thisDoc, startline, str, i,
                                "unterminated string literal(3)")
            k = string.find("0123456789abcdef", ch)
            if k < 0:
                raise BadSyntax(self._thisDoc, startline, str, i,
                                "bad string literal hex escape")
            value = value + ch
            count = count + 1
            
        # uch = value.decode('unicode-escape')   # @@ pyjs
        uch = stringFromCharCode(('0x'+value[2:10])-0)
        return j, uch


# If we are going to do operators then they should generate
#  [  is  operator:plus  of (  \1  \2 ) ]


class OLD_BadSyntax():   # was subclass ofSyntaxError @@ pyjs
    def __init__(self, uri, lines, str, i, why):
        self._str = str.encode('utf-8') # Better go back to strings for errors
        self._str = str # @@ pyjs
        self._i = i
        self._why = why
        self.lines = lines
        self._uri = uri 

    def __str__(self):
        str = self._str
        i = self._i
        st = 0
        if i>60:
            pre="..."
            st = i - 60
        else: pre=""
        if len(str)-i > 60: post="..."
        else: post=""
        return 'Line %i of <%s>: Bad syntax (%s) at ^ in:\n"%s%s^%s%s"' \
               % (self.lines +1, self._uri, self._why, pre,
                                    str[st:i], str[i:i+60], post)

def BadSyntax(uri, lines, str, i, why):
        return 'Line '+(lines +1)+' of <'+uri+'>: Bad syntax: '+why+'\nat: "'+str[i:i+30]+'"'




def stripCR(str):
    res = ""
    for ch in str:
        if ch != "\r":
            res = res + ch
    return res

def dummyWrite(x):
    pass
    
    
    

################################################################################
#ends

