#!/usr/bin/env bash

function usage {
    echo "this script converts xmls into cas files."
    echo
    echo "usage: $(basename $0) [-xcPh]"
    echo "  -x --xml-dir      directory where raw xml files are"
    echo "  -c --cas1-dir     directory where generated cas1 files will be stored"
    echo "  -P --num-proc     maximum number of parallel processes"
    echo "  -h --help         display help"
    rm ${LOCKFILE}
    exit 1
}

XML_DIR="/data/textpresso/raw_files/xml"
CAS1_DIR="/data/textpresso/tpcas-1"
N_PROC=8
LOCKFILE="/data/textpresso/tmp/04xml2cas.lock"
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
    
    echo "Generating CAS1 files ..."
    
    mkdir -p ${CAS1_DIR}/PMCOA
    
    # check for newer files in each xml folder, make processing list
    cd ${XML_DIR}
    counter=0
    t=$(mktemp);
    rm -f $t.*.list
    for i in *
    do
	if [[ $i -nt "${CAS1_DIR}/PMCOA/$i" ]]
	then
	    bin=$(($counter % $N_PROC))
	    echo $i >> "$t.$bin.list"
	    counter=$(($counter+1))
	fi
    done
    # run article2cas, with CAS1_DIR as CWD
    cd ${CAS1_DIR}
    for ((j=0; j<${N_PROC}; j++))
    do
	if [[ -f "$t.$j.list" ]]
	then
	    articles2cas -i "${XML_DIR}" -l "$t.$j.list" -t 2 -o "PMCOA" -p &
	fi
    done
    wait
    # gzip
    find PMCOA -name "*tpcas" -print0 | xargs -0 -n 8 -P 8 pigz 2>/dev/nu\ll
    rm -f $t.*.list
    rm ${LOCKFILE}
fi
