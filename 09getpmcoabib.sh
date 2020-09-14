#!/usr/bin/env bash

function usage {
    echo "this script prepares the PMCOA bibliography."
    echo
    echo "usage: $(basename $0) [-CPh]"
    echo "  -C --cas2-dir     directory where generated cas2 files will be stored"
    echo "  -P --num-proc     maximum number of parallel processes"
    echo "  -h --help         display help"
    rm ${LOCKFILE}
    exit 1
}

CAS2_DIR="/data/textpresso/tpcas-2"
N_PROC=8
LOCKFILE="/data/textpresso/tmp/09getpmcoabib.lock"
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
    export TPCAS_PATH=${CAS2_DIR}
    
    cas_dir_to_process="${CAS2_DIR}/PMCOA"
    if [[ $(ls ${cas_dir_to_process} | wc -l) != "0" ]]
    then
	tempdir=$(mktemp -d)
	num_papers_to_process_together=$(python3 -c "from math import ceil; print(ceil($(ls "${cas_dir_to_process}" | wc -l) / ${N_PROC}))")
	ls "${cas_dir_to_process}" | sed 's/.tpcas.gz//g' | split -l ${num_papers_to_process_together} - ${tempdir}/file_to_process-
	for file_list in $(ls ${tempdir})
	do
            getbib4nxml "${CAS2_DIR}/PMCOA" -f ${tempdir}/${file_list} &
    done
	wait
	rm -rf ${tempdir}
    fi
    rm ${LOCKFILE}
fi
