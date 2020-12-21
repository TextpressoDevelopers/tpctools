#!/usr/bin/env bash

function usage {
    echo "this script downloads the C. elegans bibliography."
    echo
    echo "usage: $(basename $0) [-Ch]"
    echo "  -C --cas2-dir     directory where generated cas2 files will be stored"
    echo "  -h --help         display help"
    rm ${LOCKFILE}
    exit 1
}

CAS2_DIR="/data/textpresso/tpcas-2"
LOCKFILE="/data/textpresso/tmp/10getcelegansbib.lock"
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
    
    echo "Downloading bib info for pdf files ..."
    # download bib info for pdfs
    mkdir -p /usr/local/textpresso/celegans_bib
    download_pdfinfo.pl /usr/local/textpresso/celegans_bib/
    extract_pdfbibinfo.pl  /usr/local/textpresso/celegans_bib/
    echo "Generating bib files ..."
    export TPCAS_PATH=${CAS2_DIR}
    getbib "${CAS2_DIR}/C. elegans" &
    sleep 120
    getbib "${CAS2_DIR}/C. elegans and Suppl" &
    sleep 120
    getbib "${CAS2_DIR}/C. elegans Supplementals" &
    wait
    rm ${LOCKFILE}
fi
