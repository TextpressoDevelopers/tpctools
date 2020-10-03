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

LOCKFILE="/data/textpresso/tmp/04classify.lock"
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
    listnew=$(mktemp)
    listold=$(mktemp)
    sort $WORK_DIR/04classify.list.new > $listnew
    sort $WORK_DIR/04classify.list.done > $listold
    rm $WORK_DIR/pool4predictions
    comm -23 $listnew $listold > $WORK_DIR/pool4predictions
    listcombined=$(mktemp)
    cat $WORK_DIR/04classify.list.new $WORK_DIR/04classify.list.done | sort | uniq > $listcombined
    mv $listcombined $WORK_DIR/04classify.list.done
    rm $listnew $listold
    if [[ -s "$WORK_DIR/pool4predictions" ]]
    then
	tpnn-predict.sh $WORK_DIR
    fi
    rm ${LOCKFILE}
fi
