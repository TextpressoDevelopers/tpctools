#!/usr/bin/env bash

function usage {
    echo "this script inverts images for all papers in the CAS1 directory."
    echo
    echo "usage: $(basename $0) [-cPh]"
    echo "  -c --cas1-dir     directory where generated cas1 files will be stored"
    echo "  -P --num-proc     maximum number of parallel processes"
    echo "  -h --help         display help"
    rm ${LOCKFILE}
    exit 1
}

CAS1_DIR="/data/textpresso/tpcas-1"
N_PROC=8
LOCKFILE="/data/textpresso/tmp/11invertimages.lock"
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
	    -P|--num-proc)
		shift
		N_PROC=$1
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
    
    cd ${CAS1_DIR}
    jobcount=0
    for folder in *
    do
	for i in "${folder}"/*
	do
            cmykinverter "$i/images" &
	    jobcount=$((jobcount+1))
	    if [[ $(($jobcount % ${N_PROC})) == 0 ]]
	    then
		wait
	    fi
	done
    done
    rm ${LOCKFILE}
fi
