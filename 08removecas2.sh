#!/usr/bin/env bash

function usage {
    echo "this script removes cas2 files that don't have a"
    echo "corresponding cas2 file."
    echo
    echo "usage: $(basename $0) [-cCtPh]"
    echo "  -c --cas1-dir     directory where cas1 files are stored"
    echo "  -C --cas2-dir     directory where generated cas2 files will be stored"
    echo "  -h --help         display help"
    rm ${LOCKFILE}
    exit 1
}

CAS1_DIR="/data/textpresso/tpcas-1"
CAS2_DIR="/data/textpresso/tpcas-2"
LOCKFILE="/data/textpresso/tmp/08removecas2.lock"
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
	    -C|--cas2-dir)
		shift
		CAS2_DIR="$1"
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
    
    export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/lib
    export PATH=$PATH:/usr/local/bin

    echo "Removing CAS2 files ..."

    # remove dirs in ${CAS2_DIR} that do not have corresponding dir in ${CAS1_DIR}
    cd ${CAS2_DIR}
    find . -mindepth 1 -maxdepth 1 -type d -print0 | while read -d $'\0' folder
    do
	find "${folder}" -mindepth 1 -maxdepth 1 -type d -print0 | while read -d $'\0' i
	do
	    if [[ ! -d `find ${CAS1_DIR} -name "$i"` ]]
	    then
		rm -rf "${folder}/$i"
	    fi
	done
    done  
    rm ${LOCKFILE}
fi
