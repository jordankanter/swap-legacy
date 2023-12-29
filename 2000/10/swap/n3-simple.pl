#!/usr/bin/perl
# $Id: n3-simple.pl,v 1.2 2001-05-30 22:34:14 connolly Exp $
# see changelog at end

use strict;

while(<>){
  my($S, $P, $O, $st, $pt, $ot);

  next unless /\S/; # skip blank lines
  s/^\s*//; # trim leading space
  s/\s*\.\s*$//; # trim trailing space and .
  
  ($S, $P, $O) = split(/ +/, $_, 3);
  if($st = term($S, 0)){
    # OK
  }
  else{
    die "bogus subject: $S";
  }

  if($pt = term($P, 0)){
    # OK
  }
  else{
    die "bogus predicate: $P";
  }

  if($ot = term($O, 1)){
    statement($st, $pt, $ot);
  }
  else{
    die "bogus object: $O";
  }
}

sub statement{
  my($s, $p, $o) = @_;

  print "triple($s, $p, $o)\n";

}

sub term{
  my($t, $litOK) = @_;
  
  if($t =~ s/^<//){
    if($t =~ s/>$//){
      return "r($t)";
    }
    else{
      return undef
    }
  }
  elsif($litOK && $t =~ s/^\"//){
    if($t =~ s/\"$//){
      #@@string unquoting
      return "l(\"$t\")";
    }
    else{
      return undef;
    }
  }
  elsif($t =~ s/^_://){
    if($t =~ /^[a-zA-Z0-9]+$/){
      return "a($t)";
    }
    else{
      return undef;
    }
  }
  else{
    return undef;
  }
}
    

# $Log: n3-simple.pl,v $
# Revision 1.2  2001-05-30 22:34:14  connolly
# allow some whitespace
#
