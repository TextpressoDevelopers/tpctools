#!/usr/bin/env bash

function usage {
    echo "this script downloads articles from tazendra (C. elegans pdfs)."
    echo
    echo "usage: $(basename $0) [-ph]"
    echo "  -p --pdf-dir      directory where raw pdf files will be stored"
    echo "  -h --help         display help"
    rm ${LOCKFILE}
    exit 1
}

PDF_DIR="/data/textpresso/raw_files/pdf"
LOCKFILE="/data/textpresso/tmp/01downloadpdfs.lock"
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
	    -p|--pdf-dir)
		shift
		PDF_DIR="$1"
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
    
    export PATH=$PATH:/usr/local/bin
    
    # temp files
    logfile=$(mktemp)
    
    echo "Downloading pdf papers ..."
    mkdir -p ${PDF_DIR}
    getpdfs.py -l ${logfile} -L INFO "${PDF_DIR}"
    combinepdfs.sh
    rm ${logfile}
    rm ${LOCKFILE}
fi
