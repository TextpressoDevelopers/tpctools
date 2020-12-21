#!/usr/bin/env bash

##### create sub-indexes for single index

function usage {
    echo "usage: $(basename $0) [-mph] <cas_input_dir> <indexes_output_dir>"
    echo "  -m --max-num-papers      maximum number of papers per index. Sub-indexes are created with this maximum size, in parallel"
    echo "  -o --offset              offset for document counter"
    echo "  -h --help                display help"
    exit 1
}

if [[ "${#}" < 1 ]]
then
    usage
fi

NUM_PAPERS=50000
OFFSET=0
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
    -o|--offset)
    shift
    OFFSET="$1"
    shift # past argument
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

tempdir=$(mktemp -d)
for dir in ${CAS_ROOT_DIR}/*; do for subdir in "$dir"/*; do echo "$subdir"; done; done | tac | awk -F"/" '!x[$NF]++' | tac | awk 'BEGIN{FS="/"; OFS="/"}{print $(NF-1), $NF}' | split -l ${NUM_PAPERS} - ${tempdir}/file_to_index-
i=0
for file_list in $(ls ${tempdir})
do
    mkdir ${INDEX_OUT_DIR}/tmpindex${i}
    
    counter=$(($i * ${NUM_PAPERS} + ${OFFSET}))
    echo "22 serialization::archive 12 "${counter} > ${INDEX_OUT_DIR}/tmpindex${i}/counter.dat
    (export INDEX_PATH=${INDEX_OUT_DIR}/tmpindex${i}; cas2index -i ${CAS_ROOT_DIR} -o ${INDEX_OUT_DIR}/tmpindex${i} -s ${NUM_PAPERS} -f ${tempdir}/${file_list}) &>/tmp/csi.$i.out &
    let i=$(($i + 1))
    while (( $(jobs| wc -l) > 11 ))
    do
        sleep 10
    done
done
wait
echo "22 serialization::archive 12 "$(cat ${tempdir}/file_to_index-* | wc -l | awk '{print $1}') > ${INDEX_OUT_DIR}/counter.dat
find ${INDEX_OUT_DIR} -type d -name tmpindex* | while read line
do
    tmpnum=$(basename ${line} | sed 's/tmpindex//g')
    cp -r ${line}/subindex_0 ${INDEX_OUT_DIR}/subindex_${tmpnum}
done
rm -rf ${INDEX_OUT_DIR}/tmpindex*
rm -rf ${tempdir}
mkdir "${INDEX_OUT_DIR}/db"
updatecorpuscounter -i ${INDEX_OUT_DIR} -c ${CAS_ROOT_DIR}
exit 0
