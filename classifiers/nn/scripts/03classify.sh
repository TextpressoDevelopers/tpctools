#!/usr/bin/env bash

WORK_DIR="/data/textpresso/classifiers/nn"

# models need to be made beforehand and their location can be specified in
# the commandline. Models and document vectors of papers to be classified
# need to be based on the same word model. In case of discrepancies redo
# everything from scratch
#
# Required files or directories in workdir:
#  
#  a) models/
#  b) json/predict_pr_template.json and files specified therein


function usage {
    echo "this script classifies papers."
    echo
    echo "usage: $(basename $0) [-wh]"
    echo "  -w --work-dir    work directory name (input) [$WORK_DIR]."
    echo "  -h --help        display help."
    rm ${LOCKFILE}
    exit 1
}

LOCKFILE="/data/textpresso/tmp/03classify.lock"
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
	    -w|--work-dir)
		shift
		WORK_DIR="$1"
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
    echo "Classifying papers..."
    tpnn-predict.sh $WORK_DIR
    rm ${LOCKFILE}
fi
