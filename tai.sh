#!/usr/bin/env bash

BODY="/data/textpresso/raw_files/pdf/"
IFS=$'\n'
#

BODYLIST=$(mktemp)
TARGETLIST=$(mktemp)
find -L "${BODY}" -name "*.pdf" >${BODYLIST}
while IFS='' read -r line || [[ -n "$line" ]]
do
    if [ "$line" -nt "${line%.pdf}.00001.txt" ]
    then
	printf '%s\n' "$line"
    fi
done < ${BODYLIST} > ${TARGETLIST}
rm ${BODYLIST}

##
for i in $(cat ${TARGETLIST})
do
    timeout 5m pdf2txtimg $i &
    while (( $(jobs| wc -l) > 20 ))
    do
        sleep 1
    done
done
#
rm ${TARGETLIST}
