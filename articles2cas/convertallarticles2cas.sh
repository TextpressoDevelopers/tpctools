#!/usr/bin/env bash

##### create indexes for all literatures in parallel with a maximum numberof parallel processes

function usage {
    echo "usage: $(basename $0) [-ph] <articles_input_dir> <cas_output_dir>"
    echo "  -p --num-processes       number of parallel processes"
    echo "  -t --file-type           type of input files. 1 for pdf, 2 for xml"
    echo "  -h --help                display help"
    exit 1
}

if [[ "${#}" < 1 ]]
then
    usage
fi

TYPE=1
NUM_PROCESSES=1
ARTICLES_ROOT_DIR=""
CAS_OUT_DIR=""

while [[ $# -gt 1 ]]
do
key="$1"

case $key in
    -t|--file-type)
    shift
    TYPE="$1"
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
        ARTICLES_ROOT_DIR=$key
    else
        usage
    fi
    shift
    if [ -d $1 ]
    then
        CAS_OUT_DIR=$1
    else
        usage
    fi
    shift
    ;;
esac
done

# check for the required argument ROOT_DIR
if [[ ${ARTICLES_ROOT_DIR} == "" || ${CAS_OUT_DIR} == "" ]]
then
    usage
fi

find -L ${ARTICLES_ROOT_DIR} -maxdepth 1 -mindepth 1 -type d | xargs -n 1 -P ${NUM_PROCESSES} -I {} sh -c "basename \"{}\" | xargs -I % articles2cas \"{}\" ${CAS_OUT_DIR}/%"

exit 0