<?xml version='1.0'?><!-- -*- mode: indented-text;-*- -->
<xsl:transform
    xmlns:xsl  ="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:r    ="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:s="http://www.w3.org/2000/01/rdf-schema#"
    xmlns:xs   ="http://www.w3.org/2001/XMLSchema"
    >

<div xmlns="http://www.w3.org/1999/xhtml">
<p>grokSchema -- convert schema component specification to RDF/S</p>

<address>Dan Connolly <br class=""/>
$Id: grokSchema.xsl,v 1.2 2002-07-09 21:12:44 connolly Exp $</address>

<p>see log at end</p>

<p>Share and Enjoy.
  Copyright (c) 2001 W3C (MIT, INRIA, Keio)
   <a href="http://www.w3.org/Consortium/Legal/copyright-software-19980720">Open Source license</a>
</p>

</div>

<xsl:output method="xml" indent="yes"/>

<xsl:template match="/">
  <r:RDF>
    <xsl:apply-templates/>
  </r:RDF>
</xsl:template>


<xsl:template match="compdef">
  <xsl:message>@@found component defintion: <xsl:value-of select='@name'/></xsl:message>

  <xsl:variable name="componentID" select='@ref'/>

  <xsl:if test='not($componentID = "intro-terminology")'>
    <s:Class r:ID='{$componentID}'>
      <s:label><xsl:value-of select='@name'/></s:label>
    </s:Class>

    <xsl:for-each select='proplist/propdef'>
      <xsl:call-template name='eachProp'>
        <xsl:with-param name="domain" select='$componentID'/>
      </xsl:call-template>
    </xsl:for-each>
  </xsl:if>

</xsl:template>

<xsl:template name="eachProp">
  <xsl:param name="domain"/>

  <xsl:message>@@found property defintion: <xsl:value-of select='@name'/></xsl:message>

  <r:Property r:ID='{@id}'>
    <s:label><xsl:value-of select='normalize-space(@name)'/></s:label>
    <s:comment><xsl:value-of select='normalize-space(.)'/></s:comment> <!-- @@copy nested XML markup? -->
    <s:domain r:resource='{concat("#", $domain)}'/>
  </r:Property>

</xsl:template>

<!-- don't pass text thru -->
<xsl:template match="text()|@*">
</xsl:template>


<!--
$Log: grokSchema.xsl,v $
Revision 1.2  2002-07-09 21:12:44  connolly
checkpoint: XML Schema diagram sorta works

Revision 1.1  2002/07/09 17:38:50  connolly
starting to work

-->

</xsl:transform>
