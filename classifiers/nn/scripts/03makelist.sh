#!/usr/bin/env bash

CAS1_DIR="/data/textpresso/classifiers/nn/tpcas-1"
LIST_NAME="/data/textpresso/classifiers/nn/04classify.list.new"
DONE_LIST="/data/textpresso/classifiers/nn/04classify.list.done"
function usage {
    echo "This script creates document vectors."
    echo
    echo "usage: $(basename $0) [-cldh]"
    echo "  -c --cas1-dir        directory where cas1 files are stored [$CAS1_DIR]."
    echo "  -l --list-name       name of file list [$LIST_NAME]."
    echo "  -d --done-list-name   name of done file list [$DONE_NAME]."
    echo "  -h --help            display help."
    rm ${LOCKFILE}
    exit 1
}

LOCKFILE="/data/textpresso/tmp/03makelist.lock"
if [[ -f "${LOCKFILE}" ]]
then
    echo $(basename $0) "is already running."
    exit 1
else
    touch "${LOCKFILE}"
    while [[ $# -gt 0 ]]
    do
	key=$1	
	case $key in
	    -c|--cas1-dir)
		shift
		CAS1_DIR="$1"
		shift
		;;
	    -l|--list-name)
		shift
		LIST_NAME="$1"
		shift
		;;
	    -d|--done-list-name)
		shift
		DONE_LIST="$1"
		shift
		;;
	    -h|--help)
		usage
		;;
	    *)
		echo "wrong argument: $key"
		echo
		usage
	esac
    done    
    echo "Creating list of files to be classified..."
    touch ${DONE_LIST}
    listnew=$(mktemp)
    listold=$(mktemp)
    find -L "${CAS1_DIR}" -name "*tkn" | sort > ${listnew}
    sort ${DONE_LIST} > ${listold}
    comm -23 ${listnew} ${listold} > ${LIST_NAME}
    rm ${listnew} ${listold}
    rm ${LOCKFILE}
fi
