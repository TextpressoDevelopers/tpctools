#!/usr/bin/env bash

##### simple script to change suffix .ppm to .jpg in compressed cas files and delete original .ppm images #####

function fixcas() {
    root_dir=$1
    find "${root_dir}" -name *.tpcas.gz | xargs -n 1 -P $2 -I {} sudo bash -c "zcat '{}' | sed 's/\.ppm/.jpg/g' | gzip > '{}'.tmp; mv '{}'.tmp '{}'"
}

function remppm() {
    root_dir=$1
    find "${root_dir}" -name *.ppm | xargs -I {} sudo bash -c "rm '{}'"
}

function usage {
    echo "usage: $(basename $0) [-fdh] <dir>"
    echo "  -f --fix-cas      fix cas files in <dir> recursively by changing substituting .ppm by .jpg suffix"
    echo "  -d --delete-ppm   delete .ppm images in <dir> recursively"
    echo "  -p --num-proc     maximum number of parallel processes"
    echo "  -h --help         display help"
    exit 1
}

if [[ "${#}" < 2 ]]
then
    usage
fi

FIX_CAS=false
REM_PPM=false
ROOT_DIR=""
N_PROC=1

while [[ $# -gt 0 ]]
do
key=$1

case $key in
    -f|--fix-cas)
    FIX_CAS=true
    shift # past argument
    ;;
    -d|--delete-ppm)
    REM_PPM=true
    shift # past argument
    ;;
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

if [ ${FIX_CAS} = true ]
then
    fixcas "${ROOT_DIR}" ${N_PROC}
fi
if [ ${REM_PPM} = true ]
then
    remppm "${ROOT_DIR}"
fi

exit 0