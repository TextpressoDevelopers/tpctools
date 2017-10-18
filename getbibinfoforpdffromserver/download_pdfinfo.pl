#!/usr/bin/perl
# Script downloads the acedumps from postgres and 
# deposits them into local files
#
# USAGE: ./01.pl
#
#
# BEGIN PROGRAM
# 

### modules

use strict;
use HTTP::Request;
use LWP::UserAgent;

### variables

# path to outfile

my $outpath = "$ARGV[0]";

my ($dateShort);
$|=1;  # forces output buffer to flush after every print statement!

# backs up previous data files

&getDate();

print "\n\nBacking up last dumps ....";
my @files = ("$outpath/Paper.dump", "$outpath/LongText.dump");
for (@files){
    if (-e $_){ 
	my @args = ("mv", "$_", "$_.$dateShort");
        system(@args) == 0
	    or die "system @args failed: $?";
    }
}
print "done.\n";

my $outfile1 = "$outpath"."Paper.dump";   
my $outfile2 = "$outpath"."LongText.dump";   

print "Downloading now .......\n";
open (OUT1, ">$outfile1") or die "Cannot create $outfile1 : $!";
open (OUT2, ">$outfile2") or die "Cannot create $outfile2 : $!";

# fetch all Paper objects & abstracts
# This has been changed on 2010-06-28
my $data = getwebpage("http://tazendra.caltech.edu/~postgres/michael/papers.ace");
my @alllines = split /\n/, $data;
my $flag = 0;
foreach my $line (@alllines) {
    if ($line =~ /Longtext \:/) {
	$flag = 1;
    }
    if ($flag) {
        # print longtext object
	print OUT2 $line, "\n";
    } else {
        # print out Paper objects
	print OUT1 $line, "\n";
    }
}

my @aux = $data =~ /Paper \:/g;
print scalar @aux , " paper objects downloaded.\n";
@aux = $data =~ /\*\*\*LongTextEnd\*\*\*/g;
print scalar @aux , " abstracts downloaded.\n";
close (OUT1) or die "Cannot close $outfile1 : $!";
close (OUT2) or die "Cannot close $outfile2 : $!";

print "done.\n\n";

sub getDate {

    my $time_zone = 0;
    my $time = time() + ($time_zone * 3600);
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($time);
    $year += ($year < 90) ? 2000 : 1900;
    $dateShort = sprintf("%04d%02d%02d",$year,$mon+1,$mday);
    return $dateShort;

}



sub getwebpage {

    my $u = shift;
    my $page = "";

    my $ua = LWP::UserAgent->new(timeout => 30); # instantiates a new user agent
    my $request = HTTP::Request->new(GET => $u); # grabs url
    my $response = $ua->request($request);       # checks url, dies if not valid.
    print "Error while getting ", $response->request->uri," -- ", $response->status_line, "\nAborting" unless $response-> is_success;
    $page = $response->content;    #splits by line
    return $page;

}
