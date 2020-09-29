#!/usr/bin/perl

while (<>) {

    s/&lt;/</g;
    s/&gt;/>/g;
    s/&amp;/&/g;
    s/<_pdf.+?>//g; # remove pdf tags
    s/&[^;]*;/ /g; # remove URL encoded chars
    
    $_=" $_ ";
    tr/A-Z/a-z/;
#    tr/a-z0-9\-\(\)/ /cs;
    tr/a-z0-9\-/ /cs;
    tr/a-z/ /cs;
    s/ [a-z0-9] / /g; # eliminate single characters
    s/ fi //g; # remove fl and fi (artefacts of pdf conversion)
    s/ fl //g;
    chop;
    print $_;
}
