#!/usr/bin/env bash

MODEL_NAME="/data/textpresso/classifiers/nn/celegans.word"
CAS1_DIR="/data/textpresso/classifiers/nn/tpcas-1/C. elegans"
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
    rm /usr/local/textpresso/uti/excluded.tokens
    ln -s /usr/local/textpresso/etc/celegans_excluded.tokens /usr/local/textpresso/uti/excluded.tokens  
    echo "Compute word model..."

    CASLIST=$(mktemp)
    TKNLIST=$(mktemp)
    find -L "${CAS1_DIR}" -name "*tpcas.gz" >${CASLIST}
    while IFS='' read -r line || [[ -n "$line" ]]
    do
	if [ "$line" -nt "$line.all.tkn" ]
	then
	    printf '%s\n' "$line"
	fi
    done < ${CASLIST} > ${TKNLIST} 
    mldataconverter -a -f ${TKNLIST} -o /
    ALLTXT=$(mktemp); rm ${ALLTXT}
    IFS=$'\n'
    find ${CAS1_DIR} -name "*txt" | xargs -I {} cat {} >>${ALLTXT}
    fasttext skipgram -input ${ALLTXT} -output ${MODEL_NAME} -dim 200
    rm ${MODEL_NAME}.bin
    rm ${CASLIST} ${TKNLIST} ${ALLTXT}
    rm ${LOCKFILE}
fi

