#!/usr/bin/env bash

##### create indexes for all literatures in parallel with a maximum number of parallel processes

function usage {
    echo "usage: $(basename $0) [-mph] <cas_input_dir> <indexes_output_dir>"
    echo "  -m --max-num-papers      maximum number of papers per index. Sub-indexes are created when the threshold is exceeded"
    echo "  -p --num-processes       number of parallel processes"
    echo "  -h --help                display help"
    exit 1
}

if [[ "${#}" < 1 ]]
then
    usage
fi

NUM_PAPERS=50000
NUM_PROCESSES=1
CAS_ROOT_DIR=""
INDEX_OUT_DIR=""

while [[ $# -gt 1 ]]
do
key="$1"

case $key in
    -m|--max-num-papers)
    shift
    NUM_PAPERS="$1"
    shift # past argument
    ;;
    -p|--num-processes)
    shift # past argument
    NUM_PROCESSES="$1"
    shift
    ;;
    -h|--help)
    usage
    ;;
    *)
    if [ -d $key ]
    then
        CAS_ROOT_DIR=$key
    else
        usage
    fi
    shift
    if [ -d $1 ]
    then
        INDEX_OUT_DIR=$1
    else
        usage
    fi
    shift
    ;;
esac
done

# check for the required argument ROOT_DIR
if [[ $CAS_ROOT_DIR == "" || $INDEX_OUT_DIR == "" ]]
then
    usage
fi

find -L ${CAS_ROOT_DIR} -maxdepth 1 -mindepth 1 -type d | xargs -n 1 -P ${NUM_PROCESSES} -I {} sh -c "basename \"{}\" | xargs -I % cas2index \"{}\" $INDEX_OUT_DIR/"

exit 0