#!/usr/bin/perl

use diagnostics;
use strict;
use DBI;

my $infile = "$ARGV[0]/Paper.dump";
my $infile2 = "$ARGV[0]/LongText.dump";
my $outpath = "$ARGV[0]/";

my $countentries = 0;
my $dateShort;
my @directories = qw (
		      accession
		      author
		      abstract
		      title
		      journal
		      citation
		      year
		      type
		      );

# back up old and make new directories.

&getDate();

foreach (@directories){
    print "Making $outpath/$_ directory ..... ";
    if (-d "$outpath/$_"){
#	my @args = ("tar", "zcf", "$outpath/$_.$dateShort.tgz", "$outpath/$_"); 
#	system(@args) == 0 or die "system @args failed: $?";
	my @temp = <$outpath/$_/*>;
	for (@temp){
	    unlink "$_" or warn "Cannot delete $_: $!";
	}
    } else {
	mkdir "$outpath/$_";
    }
    print "done.\n";
}

# extracts Title, Author, Citation, Year, Type, Journal from Paper.dump

open (FILE, "<$infile") || die "Cannot open $infile : $!";
print "loading $infile ....";
undef $/;
my $wholefile = <FILE>;
$/ = "\n";
close (FILE) or die "Cannot close $infile : $!";
print "done.\n";
my @sections = split (/\n\n/, $wholefile);
my $count = scalar(@sections);

# extracts abstracts from LongText.dump

my $filename2 = "";
open (FILE2, "<$infile2") || die "Cannot open $infile2 : $!";
print "loading $infile2 ....";
undef $/;
my $wholefile2 = <FILE2>;
$/ = "\n";
close (FILE2) or die "Cannot close $infile2 : $!";
print "done.\n";

(my @array2) = split(/\*\*\*LongTextEnd\*\*\*\n/, $wholefile2);
my $count2 = scalar(@array2);
my %abstracttexts = ();
foreach my $entry (@array2) {
    (my $id) = $entry =~ /Longtext[ \t]\:[ \t]\"(.+?)\"/;
    (my $text) = $entry =~ /\"$id\"\n\n(.+?)\n\n/;
    $abstracttexts{$id} = $text;
}



#my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb;host=131.215.52.76", "acedb", "") or die "Cannot connect to database!\n"; 
my $dbh = DBI->connect ( "dbi:Pg:dbname=muellerdb;host=131.215.76.23", "mueller", "goldturtle") or die "Cannot connect to database!\n"; 
my $result = $dbh->prepare( "SELECT * FROM pap_curation_flags WHERE pap_curation_flags = 'non_nematode'");
$result->execute() or die "Cannot prepare statement: $DBI::errstr\n"; 
my %non_nematode = ();
while (my @row = $result->fetchrow) {
    if ($row[0]) { 
	my $jk = shift (@row);
	$non_nematode{"WBPaper$jk"} = 1;
    } 
}
$dbh->disconnect;

foreach my $s (@sections){

#
    next if (($s !~ /(^|\n)Paper/) || ($s !~ /\n(Author|Editor)/) || ($s !~ /\nTitle/));
#

    (my $filename) = $s =~ /Paper \:[ \t]+\"(WBPaper\d{8})\"/;
#
    next if ($non_nematode{$filename});
#
    (my @other_names) = $s =~ /\nName[ \t]+\"(.+?)\"/g;
    (my $pmid_name) = $s =~ /\nDatabase[ \t]+\"MEDLINE\"[ \t]+\"PMID\"[ \t]+\"(\d+)\"/;
    my @editors = $s =~ /\nEditor[ \t]+\"(.+?)\"/g;
    my @authors = $s =~ /\nAuthor[ \t]+\"(.+?)\"/g;
    push (@authors,@editors);
    (my $aux) = $s =~ /\nVolume[ \t]+(.+)\n/;
    my @volumes = $aux =~ /\"(.+?)\"/g;
    ($aux) = $s =~ /\nPage[ \t]+(.+)\n/;
    my @pages = $aux =~ /\"(.+?)\"/g;
    my $journal = '';
    ($aux) = $s =~ /\nJournal[ \t]+\"(.+?)\"/;
    $journal .= $aux;
    ($aux) = $s =~ /\nTitle[ \t]+(\".+?\n)/;
    (my $title) = $aux =~ /^\"(.+)\"/;
    (my $type) = $s =~ /\nType[ \t]+\"(.+?)\"/;
    (my $year) = $s =~ /\nPublication_date[ \t]+\"([\-\d]+)\"/;
    (my $absid) = $s =~ /\nAbstract[ \t]+\"(.+?)\"/;

    $countentries++;

    my $acc = '';
    $acc .= "Other:" . "@other_names" . "\n" if (@other_names);
    $acc =~ s/(doi|DOI|Doi)/$1:/g;
    $acc .= "PMID:$pmid_name\n" if ($pmid_name ne '');

# need to remove if-loop and add empty line
# so an empty accession file can be written.
# this is necessary so pdf without any accession 
# can be downloaded

    $acc .= "\n" if ($acc eq '');
#    if ($acc ne '') {
	open (OUT, ">$outpath/accession/$filename") or die "Cannot open $outpath/Accession/$filename : $!";
	print OUT "$acc";
	close (OUT) or die "Cannot close $outpath/Accession/$filename : $!";
#    }
#
    if (@authors) {
	# take care of new format in author section (repetition of author lines) 
	my %seen = ();
	my @aux = ();
	foreach (@authors) {
	    if (!$seen{$_}) {
		$seen{$_} = 1;
		push @aux, $_;
	    }
	}
	open (OUT, ">$outpath/author/$filename") or die "Cannot open $outpath/Author/$filename : $!";	    
	print OUT join(" ; \n", @aux);
	close (OUT) or die "Cannot close $outpath/Author/$filename: $!";
    }
#    
    if ((@volumes) || (@pages)) {
	open (OUT, ">$outpath/citation/$filename") or die "Cannot open $outpath/Citation/$filename : $!";
	print OUT "V: ", join(" ", @volumes), "\n" if (@volumes);
	print OUT "P: ", join(" ", @pages), "\n" if (@pages);
	close (OUT) or die "Cannot close $outpath/Citation/$filename : $!";
    }
#
    if ($journal ne '') {
	open (OUT, ">$outpath/journal/$filename") or die "Cannot open $\outpath/Journal/$filename : $!";
	print OUT "$journal\n";
	close (OUT) or die "Cannot close $outpath/Journal/$filename : $\!";
    }
#
    if ($title ne '') {
	open (OUT, ">$outpath/title/$filename") or die "Cannot open $outpath/Title/$filename : $!";
	print OUT "$title\n";
	close (OUT) or die "Cannot close $outpath/Title/$filename : $!";
    }
#
    if ($type ne '') {
	open (OUT, ">$outpath/type/$filename") or die "Cannot open $outpath/Type/$filename : $!";
	print OUT "$type\n";
	close (OUT) or die "Cannot close $outpath/Type/$filename : $!";
    }
#
    if ($year ne '') {
	open (OUT, ">$outpath/year/$filename") or die "Cannot open $outpath/Year/$filename : $!";
	print OUT "$year\n";
	close (OUT) or die "Cannot close $outpath/year/$filename : $!";
    }
#
    if ($abstracttexts{$absid}) {
	open (OUT, ">$outpath/abstract/$filename") or die "Cannot open $outpath/$filename : $!";
	print OUT "$abstracttexts{$absid}";
	close (OUT) or die "Cannot close $outpath/$filename : $!";
    }
#
}

print "\n\n#########################################";
print "\nThere are $count citations total and\n";
print "$countentries were complete enough to be usable.\n";
print "$count2 abstracts were extracted.\n";
print "\n\n";
for (@directories){
    my @cnt = <$outpath/$_/*>; 
    my $cnt = scalar(@cnt); 
    print "$_ has $cnt files\n";
}

print "\n\n##########################################\n";

sub getDate{
    my $time_zone = 0;
    my $time = time() + ($time_zone * 3600);
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($time);
    $year += ($year < 90) ? 2000 : 1900;
    $dateShort = sprintf("%04d%02d%02d",$year,$mon+1,$mday);
    return $dateShort;
}
