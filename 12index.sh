#!/usr/bin/env bash

function usage {
    echo "this script indexes all papers in the CAS2_DIR."
    echo
    echo "usage: $(basename $0) [-Cih]"
    echo "  -C --cas2-dir     directory where cas2 files are stored"
    echo "  -i --index-dir    directory for the lucene index"
    echo "  -h --help         display help"
    rm ${LOCKFILE}
    exit 1
}

CAS2_DIR="/data/textpresso/tpcas-2"
INDEX_DIR="/data/textpresso/luceneindex"
PAPERS_PER_SUBINDEX=1000000
LOCKFILE="/data/textpresso/tmp/12index.lock"
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
	    -C|--cas2-dir)
		shift
		CAS2_DIR="$1"
		shift
		;;
	    -i|--index-dir)
		shift
		INDEX_DIR="$1"
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
    
    #################################################################################
    #####                     6. INDEX PAPERS                                   #####
    #################################################################################
    
    echo "Updating index ..."
    export INDEX_PATH=${INDEX_DIR}
    INDEX_DIR_CUR="${INDEX_DIR}"
    if [[ -d ${INDEX_DIR} && $(ls ${INDEX_DIR} | grep -v "subindex_0" | wc -l) != "0" ]]
    then
	INDEX_DIR_CUR="${INDEX_DIR}_new"
    fi
    mkdir -p "${INDEX_DIR_CUR}/db"
    create_single_index.sh -m 10000 ${CAS2_DIR} ${INDEX_DIR_CUR}
    cd "${INDEX_DIR_CUR}"
    num_subidx_step=$(echo "${PAPERS_PER_SUBINDEX}/10000" | bc)
    first_idx_in_master=0
    final_counter=0
    last_idx_in_master=${num_subidx_step}
    num_subidx=$(ls | grep "subindex_" | wc -l)
    found="0"
    while [[ ${found} == "0" ]]
    do
	if [[ ${last_idx_in_master} -ge ${num_subidx} ]]
	then
            last_idx_in_master=${num_subidx}
            found="1"
	fi
	for ((i=$((first_idx_in_master + 1)); i<=$((last_idx_in_master-1)); i++))
	do
            indexmerger subindex_${first_idx_in_master} subindex_${i} no
            rm -rf subindex_${i}
	done
	if [[ "subindex_${first_idx_in_master}" != "subindex_${final_counter}" ]]
	then
            mv subindex_${first_idx_in_master} subindex_${final_counter}
	fi
	first_idx_in_master=$((first_idx_in_master + num_subidx_step))
	last_idx_in_master=$((last_idx_in_master + num_subidx_step))
	final_counter=$((final_counter + 1))
    done
    saveidstodb -i ${INDEX_DIR_CUR}
    chmod -R 777 "${INDEX_DIR_CUR}/db"
    rm -rf /data/textpresso/db.bk
    mv /data/textpresso/db /data/textpresso/db.bk
    mv "${INDEX_DIR_CUR}/db" /data/textpresso/db
    ln -s /data/textpresso/db "${INDEX_DIR_CUR}/db"
    if [[ -d "${INDEX_DIR}_new" ]]
    then
	rm -rf "${INDEX_DIR}.bk"
	mv "${INDEX_DIR}" "${INDEX_DIR}.bk"
	mv ${INDEX_DIR_CUR} ${INDEX_DIR}
    fi
    rm ${LOCKFILE}
fi
