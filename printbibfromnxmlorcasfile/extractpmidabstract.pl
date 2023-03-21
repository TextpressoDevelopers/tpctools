#!/usr/bin/perl

use diagnostics;
use strict;

my $outpath = "$ARGV[0]/";

undef $/;
my $wholefile = <STDIN>;
$wholefile =~ s/\n//g;
(my @pubmedarticles) = $wholefile =~ /<PubmedArticle>(.+?)<\/PubmedArticle>/g;
foreach my $s (@pubmedarticles) {
    my ($pmid) = $s =~ /      <PMID Version=\"1\">(.+?)<\/PMID>/g;
    if (defined($pmid)) {
	unless (-e "$outpath/$pmid.txt") {
	    my ($abtxt) = $s =~ /<AbstractText>(.+?)<\/AbstractText>/g;
	    if (defined($abtxt)) {
		open (OUT, ">$outpath/$pmid.txt") or die "Cannot open $outpath/$pmid.txt : $!";
		print OUT "$abtxt";
		close (OUT) or die "Cannot close $outpath/$pmid.txt : $!";
	    }
	}
    }
}
