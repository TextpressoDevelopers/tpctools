#!/usr/bin/env bash

MODEL_NAME="/data/textpresso/classifiers/nn/corpus.word"
CAS1_DIR="/data/textpresso/classifiers/nn/tpcas-1"
N_PROC=8
DIM=200

function usage {
    echo "This script computes word models with the help of fasttext."
    echo
    echo "usage: $(basename $0) [-mcPh]"
    echo "  -m --model-name   filename of model (output) [$MODEL_NAME]."
    echo "  -c --cas1-dir     directory where cas1 are stored [$CAS1_DIR]."
    echo "  -P --num-proc     maximum number of parallel processes [$N_PROC]."
    echo "  -d --dim          dimensionality of word vectors [$DIM]."
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
	    -d|--dim)
		shift
		DIM=$1
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
    echo "cas-dir: " ${CAS1_DIR}
    echo "model name: " ${MODEL_NAME}
    TMP=$(mktemp -d)
    ALLTXT=${TMP}/alltext
    rm -f $ALLTXT
    IFS=$'\n'
    for i in $(find -L "${CAS1_DIR}" -name "*tpcas.gz")
    do
	TARGETFILE=$(echo "$i" | sed 's/\//_/g')
	zgrep sofaString "$i" 2>/dev/null \
	    | sed 's/\(.*\)sofaString="\(.*\)/\2/g' \
	    | cleancas.pl >"${TMP}/${TARGETFILE}.txt" &     
	if (( $(jobs| wc -l) > ${N_PROC} ))
	then
	    wait
	fi
    done
    for i in `find ${TMP} -name "*txt"`; do cat $i; rm $i; done >${ALLTXT}
    fasttext skipgram -input ${ALLTXT} -output ${MODEL_NAME} -dim ${DIM}
    rm ${MODEL_NAME}.bin
    rm -rf ${TMP}
    rm ${LOCKFILE}
fi
