#!/usr/bin/env bash

function usage {
    echo "this script converts xmls into cas files."
    echo
    echo "usage: $(basename $0) [-xcPh]"
    echo "  -x --xml-dir      directory where raw xml files are"
    echo "  -c --cas1-dir     directory where generated cas1 files will be stored"
    echo "  -h --help         display help"
    rm ${LOCKFILE}
    exit 1
}

XML_DIR="/data/textpresso/raw_files/xml"
CAS1_DIR="/data/textpresso/tpcas-1"
LOCKFILE="/data/textpresso/tmp/05addimages2cas1.lock"
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
    
    echo "Add images CAS1 directories ..."
    
    # add images to tpcas directory
    cd ${CAS1_DIR}/PMCOA
    for i in *
    do
	if [[ -d "${XML_DIR}/$i/images" ]]
	then
	    if [[ "$(ls -A ${XML_DIR}/$i/images)" ]]
	    then
		ln -s "${XML_DIR}/$i/images"/* "${CAS1_DIR}/PMCOA/$i/images/." 2>/dev/null
	    fi
	fi
    done
    rm ${LOCKFILE}
fi
