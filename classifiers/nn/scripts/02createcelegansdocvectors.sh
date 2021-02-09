#!/usr/bin/env bash

WORD_MODEL_NAME="/data/textpresso/classifiers/nn/celegans.word.vec"
DOC_MODEL_NAME="/data/textpresso/classifiers/nn/celegans.doc"
CAS1_DIR="/data/textpresso/classifiers/nn/tpcas-1"

function usage {
    echo "This script creates document vectors."
    echo
    echo "usage: $(basename $0) [-mdch]"
    echo "  -m --model-name      filename of word model (input) [$WORD_MODEL_NAME]."
    echo "  -d --doc-model-name  filename of doc model (output) [$DOC_MODEL_NAME]."
    echo "  -c --cas1-dir        directory where cas1 files are stored [$CAS1_DIR]."
    echo "  -h --help            display help."
    rm ${LOCKFILE}
    exit 1
}

LOCKFILE="/data/textpresso/tmp/02createcelegansdocvectors.lock"
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
		WORD_MODEL_NAME="$1"
		shift
		;;
	    -d|--doc-model-name)
		shift
		DOC_WORD_MODEL_NAME="$1"
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
    ln -s /usr/local/textpresso/etc/celegans_excluded.tokens /usr/local/textpresso/uti/excluded.tokens
    echo "Creating C. elegans document vectors..."
    
    CASLIST=$(mktemp)
    TKNLIST=$(mktemp)
    find -L "${CAS1_DIR}" -name "*tpcas.gz" >${CASLIST}
    while IFS='' read -r line || [[ -n "$line" ]]
    do
	if [ "$line" -nt "$line.tkn" ]
	then
	    printf '%s\n' "$line"
	fi
    done < ${CASLIST} > ${TKNLIST} 
    mldataconverter -f ${TKNLIST} -o / -t
    rm ${CASLIST}
    rm ${TKNLIST}
    echo "{" > /data/textpresso/classifiers/nn/createcelegansdocvecs.json
    echo "   \"task\" : \"create document vectors\"," >> /data/textpresso/classifiers/nn/createcelegansdocvecs.json
    echo "   \"document directory\" : \"${CAS1_DIR}\"," >> /data/textpresso/classifiers/nn/createcelegansdocvecs.json
    echo "   \"word model\" : \"${WORD_MODEL_NAME}\"," >> /data/textpresso/classifiers/nn/createcelegansdocvecs.json
    echo "   \"document model\" : \"${DOC_MODEL_NAME}\"," >> /data/textpresso/classifiers/nn/createcelegansdocvecs.json
    echo "   \"normalize vectors\" : \"yes\"" >> /data/textpresso/classifiers/nn/createcelegansdocvecs.json
    echo "}" >> /data/textpresso/classifiers/nn/createcelegansdocvecs.json
    we -j /data/textpresso/classifiers/nn/createcelegansdocvecs.json
    rm /data/textpresso/classifiers/nn/createcelegansdocvecs.json
    rm ${LOCKFILE}
fi
