#!/usr/bin/env bash

BODY="/data/textpresso/raw_files/pdf/C. elegans"
SUPP="/data/textpresso/raw_files/pdf/C. elegans Supplementals"
COMB="/data/textpresso/raw_files/pdf/C. elegans and Suppl"

SUPPCOVER="/data/textpresso/tpctools/SupplMatCoverSheet.pdf"
#IFS=$(echo -en '\b\n')
IFS=$'\n'
#

mkdir -p $COMB
BODYLIST=$(mktemp)
TARGETLIST=$(mktemp)
find -L "${BODY}" -name "*.pdf" >${BODYLIST}
while IFS='' read -r line || [[ -n "$line" ]]
do
    if [ "$line" -nt "$COMB${line##$BODY}" ]
    then
	printf '%s\n' "$line"
    fi
done < ${BODYLIST} > ${TARGETLIST}
rm ${BODYLIST}


for i in $(cat ${TARGETLIST})
do
    rsync -a $(dirname "${i}") $(dirname "$COMB${i##$BODY}")
done

##
for i in $(cat ${TARGETLIST})
do
    d=$(dirname ${i})
    j=$(ls "$SUPP${d##$BODY}"*/*.pdf 2>/dev/null)
    if [[ "${j}" != "" ]]
    then
	pdfunite "${i}" "$SUPPCOVER" "${j}" "$COMB${i##$BODY}"
	touch -r "${i}" "$COMB${i##$BODY}"
    fi
done
#
rm ${TARGETLIST}
