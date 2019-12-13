#!/usr/bin/env bash

apt-get -y install poppler-utils
#

BODY="/data/textpresso/raw_files/pdf/C. elegans"
SUPP="/data/textpresso/raw_files/pdf/C. elegans Supplementals"
COMB="/data/textpresso/raw_files/pdf/C. elegans Combined"
#IFS=$(echo -en '\b\n')
IFS=$'\n'
#

mkdir -p $COMB
rsync -av $BODY/ $COMB/
#

for i in $(ls $BODY)
do j=$(ls $SUPP/$i*/*.pdf)
   pdfunite $BODY/$i/$i.pdf $j $COMB/$i/$i.pdf
   touch -r $BODY/$i/$i.pdf $COMB/$i/$i.pdf
done
#
