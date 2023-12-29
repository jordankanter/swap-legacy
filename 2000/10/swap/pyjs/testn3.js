

// breadcrumbs:
// http://developer.mozilla.org/en/docs/Rhino_documentation
// http://www.mozilla.org/rhino/ScriptingJava.html
// http://www.exampledepot.com/egs/java.io/ReadLinesFromFile.html
// http://developer.mozilla.org/en/docs/Rhino_Shell#arguments

// load("/devel/dig/2005/ajar/ajaw/lib0.js");

load("/devel/dig/2005/ajar/ajaw/js/log.js");
load("/devel/dig/2005/ajar/ajaw/js/uri.js");
load("/devel/dig/2005/ajar/ajaw/js/rdf/term.js");
load("/devel/dig/2005/ajar/ajaw/js/rdf/match.js");
load("/devel/dig/2005/ajar/ajaw/js/rdf/identity.js");
load("/devel/dig/2005/ajar/ajaw/js/rdf/remote.js");
load("/devel/dig/2005/ajar/ajaw/js/rdf/rdfparser.js");
load("n3parser.js");  // @@ Note local copy
load("/devel/dig/2005/ajar/ajaw/js/rdf/serialize.js");
load("/devel/dig/2005/ajar/ajaw/js/rdf/query.js");
load("/devel/dig/2005/ajar/ajaw/js/rdf/sources.js");
load("/devel/dig/2005/ajar/ajaw/js/rdf/sparql.js");

kb = new RDFIndexedFormula();


testn3 = function(uri) {
    var msg = ""
//    msg += '# Parsing '+uri + '\n'
    var localURI = uri;
    if (uri.slice(0,18) == 'http://www.w3.org/') {
        localURI ='http://localhost/' + uri.slice(7)
    }
    var buf = readUrl(localURI);   // @@ offline
//    msg += ('# '+ buf.length+' bytes' + '\n');
    var p = SinkParser(kb, kb, uri, uri, null, null, "", null)

//    p.loadBuf(buf)
    

    try {
	p.loadBuf(buf)

    } catch(e) {
	msg += ("Error trying to parse " + uri
	    + ' as Notation3:\n\t' + e )
//        msg += '\n\tline '+e.lineNumber ;
        if (typeof e != 'string')
           for (i in e) { msg+= '\n\t\t'+i +': '+ e[i]+'; '}
        java.lang.System.err.println(msg)
        
//	print(msg)
        java.lang.System.exit(1)  // Error
    }
  
//    print('kb='+kb);
    sz = Serializer();
//    for (var prefix in kb.namespaces) {
//        sz.setPrefixForURI(prefix, kb.namespaces[prefix]);
//        print(prefix +'->'+kb.namespaces[prefix]);
//    }

    sz.suggestNamespaces(kb.namespaces);
    print('test: sz.prefixes[http://www.w3.org/2000/10/swap/pim/contact#]='+sz.prefixes['http://www.w3.org/2000/10/swap/pim/contact#']);
    sz.setBase(uri);
    var sts = kb.statementsMatching(undefined, undefined, undefined, kb.sym(uri));
//    str = sz.statementsToXML(kb.statements);
    str = sz.statementsToXML(sts);
    
//    str = ''+kb
//    str = str.slice(1,-1)  // remove {}
    print (str)  // .encode('utf-8')
    java.lang.System.exit(0)
    
}

// print("Arguments <"+arguments+">"+arguments.length)

testn3(arguments[0]);
