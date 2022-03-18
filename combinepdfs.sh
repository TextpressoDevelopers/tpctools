#!/usr/bin/env bash

BODY="/data/textpresso/raw_files/pdf/C. elegans"
SUPP="/data/textpresso/raw_files/pdf/C. elegans Supplementals"
COMB="/data/textpresso/raw_files/pdf/C. elegans and Suppl"
#
SUPPCOVER="/usr/local/etc/SupplMatCoverSheet.pdf"
#IFS=$(echo -en '\b\n')
IFS=$'\n'
#
mkdir -p $COMB
BODYLIST=$(mktemp)
TARGETLIST=$(mktemp)
find -L "${BODY}" -name "*.pdf" >${BODYLIST}
while IFS='' read -r line || [[ -n "$line" ]]
do
    msline="$COMB${line##$BODY}"
    msline="${msline//WB/MSWB}"
    if [ "$line" -nt "$msline" ]
    then
	printf '%s\n' "$line"
    fi
done < ${BODYLIST} > ${TARGETLIST}
rm ${BODYLIST}
for i in $(cat ${TARGETLIST})
do
    rsync -a --delete-after $(dirname ${i}) ${COMB}/.
done
##
for i in $(cat ${TARGETLIST})
do
    d=$(dirname "${i}")
    j=$(ls "$SUPP${d##$BODY}"*/*.pdf 2>/dev/null)
    if [[ "${j}" != "" ]]
    then
	pdfunite "${i}" "$SUPPCOVER" ${j} "$COMB${i##$BODY}"
	touch -r "${i}" "$COMB${i##$BODY}"
    fi
done
#
for i in $(cat ${TARGETLIST})
do
    j="$COMB${i##$BODY}"
    mv $(dirname $j) $(dirname ${j/\/WBPaper/\/MSWBPaper})
    for k in `find $(dirname ${j/\/WBPaper/\/MSWBPaper}) -name "*pdf"`
    do
	mv "$k" "${k/\/WBPaper/\/MSWBPaper}"
    done
done
#
rm ${TARGETLIST}

