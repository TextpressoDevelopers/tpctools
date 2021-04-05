#!/usr/bin/env bash

function usage {
    echo "this script converts pdfs to txt to cas files."
    echo
    echo "usage: $(basename $0) [-pcPh]"
    echo "  -p --pdf-dir      directory where raw pdf files are"
    echo "  -c --cas1-dir     directory where generated cas1 files will be stored"
    echo "  -P --num-proc     maximum number of parallel processes"
    echo "  -h --help         display help"
    rm ${LOCKFILE}
    exit 1
}

PDF_DIR="/data/textpresso/raw_files/pdf"
CAS1_DIR="/data/textpresso/tpcas-1"
N_PROC=8
LOCKFILE="/data/textpresso/tmp/catch.non-conv.pdfs.4.cas1.lock"
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
    
    echo "Generating CAS1 files for PDFs that defy usual conversion..."
    
    cd ${PDF_DIR}
    # obtain all the folder names in PDF_DIR then create tpcas1 folders for every corpus
    for folder in */ ;
    do
	mkdir -p "${CAS1_DIR}/${folder}"
    done
    
    # check for newer files in each pdf folder, make processing list
    for folder in *;
    do
	echo "${folder}"
	counter=0
	rm -f /tmp/"${folder}".*.nc.list
	rm -rf /tmp/"${folder}".*.nc.dir
	for i in "${folder}"/*
	do
	    if [[ -z $(ls "${CAS1_DIR}/$i/"*.gz 2>/dev/null) ]]
	    then
		d=${i#"${folder}"/}
		bin=$(($counter % $N_PROC))
		echo $d >> "/tmp/${folder}.$bin.nc.list"
		rsync -a "$i" "/tmp/${folder}.$bin.nc.dir"
		counter=$(($counter+1))
	    fi
	done
    done
    find /tmp/*.nc.dir -name "*.pdf" -print0 | xargs -I % -0 -n 1 -P 8 sh -c "pdftotext \"%\"; rm -f \"%\""
    find /tmp/*.nc.dir -name "*.txt" -print0 | xargs -I % -0 -n 1 -P 8 sh -c "sed -i 's/\f/\n/g' \"%\""
    for i in '\x1' '\x2' '\x3' '\x4' '\x5' '\x6' '\x7' '\x8' '\xE' '\xF' \
		   '\x10' '\x11' '\x12' '\x13' '\x14' '\x15' '\x16' '\x18' '\x19' '\x1A' '\x1D' '\x1F'
    do
	find /tmp/*.nc.dir -name "*.txt" -print0 | xargs -I % -0 -n 1 -P 8 sh -c "sed -i 's/$i/ /g' \"%\""  
    done
    # run article2cas, with CAS1_DIR as CWD
    cd ${CAS1_DIR}
    for folder in *
    do
	for ((j=0; j<${N_PROC}; j++))
	do
	    if [[ -f "/tmp/${folder}.$j.nc.list" ]]
	    then
		articles2cas -i "/tmp/${folder}.$j.nc.dir" -l "/tmp/${folder}.$j.nc.list" -t 3 -o "${folder}" -p &
	    fi
	done
	wait
	# gzip all tpcas files
	find "${folder}" -name "*tpcas" -print0 | xargs -0 -n 8 -P 8 pigz 2>/dev/null
	rm -f /tmp/"${folder}".*.nc.list
	rm -rf /tmp/"${folder}".*.nc.dir
    done
    rm ${LOCKFILE}
fi
