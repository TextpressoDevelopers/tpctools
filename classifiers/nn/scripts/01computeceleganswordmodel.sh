#!/usr/bin/env bash

MODEL_NAME="/data/textpresso/classifiers/nn/celegans.word"
CAS1_DIR="/data/textpresso/tpcas-1/C. elegans"
N_PROC=1

function usage {
    echo "This script computes word models with the help of fasttext."
    echo
    echo "usage: $(basename $0) [-mcPh]"
    echo "  -m --model-name   filename of model (output) [$MODEL_NAME]."
    echo "  -c --cas1-dir     directory where cas1 are stored [$CAS1_DIR]."
    echo "  -P --num-proc     maximum number of parallel processes [$N_PROC]."  
    echo "  -h --help         display help."
    rm ${LOCKFILE}
    exit 1
}

LOCKFILE="/data/textpresso/tmp/01computewordmodel.lock"
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
	    -m|--model-name)
		shift
		MODEL_NAME="$1"
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
    
    echo "Compute word model..."

    TMP=$(mktemp -d)
    ALLTXT=${TMP}/alltext
    rm -f $ALLTXT
    for i in $(ls "${CAS1_DIR}")
    do
	zgrep sofaString "${CAS1_DIR}/$i/$i.tpcas.gz" 2>/dev/null \
	    | sed 's/\(.*\)sofaString="\(.*\)/\2/g' \
	    | pdfclean.pl >${TMP}/$i.txt &
	if (( $(jobs| wc -l) > ${N_PROC} ))
	then
	    wait
	fi
    done
    cat `find ${TMP} -name "*txt"` >${ALLTXT}
    fasttext skipgram -input ${ALLTXT} -output ${MODEL_NAME}
    rm ${MODEL_NAME}.bin
    rm -rf ${TMP}
    rm ${LOCKFILE}
fi

