#!/usr/bin/env bash

function usage {
    echo "this script removes cas-1 files that do not have "
    echo "a corresponding raw file. "
    echo
    echo "usage: $(basename $0) [-pxcPh]"
    echo "  -p --pdf-dir      directory where raw pdf files are"
    echo "  -x --xml-dir      directory where raw xml files are"
    echo "  -c --cas1-dir     directory where generated cas1 files will be stored"
    echo "  -P --num-proc     maximum number of parallel processes"
    echo "  -h --help         display help"
    rm ${LOCKFILE}
    exit 1
}

PDF_DIR="/data/textpresso/raw_files/pdf"
XML_DIR="/data/textpresso/raw_files/xml"
CAS1_DIR="/data/textpresso/tpcas-1"
N_PROC=8
LOCKFILE="/data/textpresso/tmp/06removecas1.lock"
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
	    -x|--xml-dir)
		shift
		XML_DIR="$1"
		shift
		;;
	    -c|--cas1-dir)
		shift
		CAS1_DIR="$1"
		shift
		;;
	    -t|--tmp-dir)
		shift
		TMP_DIR="$1"
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
    
    # need to do xml and pdf simultaneously to avoid illegal (cross)deletion
    # remove dirs in ${CAS1_DIR} that do not have corresponding dir in ${PDF_DIR}
    # or ${XML_DIR}.
    cd ${CAS1_DIR}
    for folder in */;
    do
	for i in "${folder}"/*
	do
	    d=${i#"${folder}"/}
	    if [[ ! (-d `find ${PDF_DIR} -name "$d"` || -d `find ${XML_DIR} -name "$d"`) ]]
	    then
		rm -rf "$i"
	    fi
	done
    done
    rm ${LOCKFILE}
fi
