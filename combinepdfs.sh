#!/usr/bin/env bash

apt-get -y install poppler-utils
#

BODY="/data/textpresso/raw_files/pdf/C. elegans"
SUPP="/data/textpresso/raw_files/pdf/C. elegans Supplementals"
COMB="/data/textpresso/raw_files/pdf/C. elegans Combined"

SUPPCOVER="/data/textpresso/tpctools/SupplMatCoverSheet.pdf"
#IFS=$(echo -en '\b\n')
IFS=$'\n'
#

mkdir -p $COMB
rsync -av $BODY/ $COMB/
#

for i in $(ls $BODY)
do
    j=$(ls $SUPP/$i*/*.pdf 2>/dev/null)
    if [[ "$j" != "" ]]
    then
	pdfunite $BODY/$i/$i.pdf $SUPPCOVER $j $COMB/$i/$i.pdf
	touch -r $BODY/$i/$i.pdf $COMB/$i/$i.pdf
    fi
done
#
