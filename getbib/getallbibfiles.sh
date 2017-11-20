#!/usr/bin/env bash

function usage {
    echo "usage: $(basename $0) [p] <tpcas_dir>"
    echo "  -p --num-proc     maximum number of parallel processes"
    echo "  -h --help         display help"
    exit 1
}

if [[ "${#}" < 1 ]]
then
    usage
fi

ROOT_DIR=""
N_PROC=1

while [[ $# -gt 0 ]]
do
key=$1

case $key in
    -p|--num-proc)
    shift
    N_PROC=$1
    shift
    ;;
    -h|--help)
    usage
    ;;
    *)
    if [[ -d $key ]]
    then
        ROOT_DIR="$key"
        shift
    else
        usage
    fi
    ;;
esac
done

# check for the required argument ROOT_DIR
if [[ ${ROOT_DIR} == "" ]]
then
    usage
fi

for corpus in ${ROOT_DIR}/*
do
    corpus_name=$(echo ${corpus} | awk -F"/" '{print $NF}')
    if [[ "${corpus_name}" == "C. elegans" || "${corpus_name}" == "C. elegans Supplementals" ]]
    then
        getbib "${ROOT_DIR}/${corpus_name}"
    else
        getbib4nxml "${ROOT_DIR}/${corpus_name}"
    fi
done