#!/usr/bin/env bash

function usage {
    echo "this script lexically annotates cas1 files and stores them as "
    echo "cas2 files."
    echo
    echo "usage: $(basename $0) [-cCtPh]"
    echo "  -c --cas1-dir     directory where cas1 files are stored"
    echo "  -C --cas2-dir     directory where generated cas2 files will be stored"
    echo "  -t --tmp-dir      temp directory"
    echo "  -P --num-proc     maximum number of parallel processes"
    echo "  -h --help         display help"
    rm ${LOCKFILE}
    exit 1
}

CAS1_DIR="/data/textpresso/tpcas-1"
CAS2_DIR="/data/textpresso/tpcas-2"
TMP_DIR="/data/textpresso/tmp"
N_PROC=8
LOCKFILE="/data/textpresso/tmp/07cas1tocas2.lock"
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
	    -c|--cas1-dir)
		shift
		CAS1_DIR="$1"
		shift
		;;
	    -C|--cas2-dir)
		shift
		CAS2_DIR="$1"
		shift
		;;
	    -t|--tmp-dir)
		shift
		TMP_DIR="$1"
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
    echo "Generating CAS2 files ..."
    #
    rm -rf ${TMP_DIR}/tpcas-1
    rm -rf ${TMP_DIR}/tpcas-2
    
    # prepare files to be processed
    cd ${CAS1_DIR}
    echo 0 > /tmp/worktodo
    find . -mindepth 1 -maxdepth 1 -type d -print0 | while read -d $'\0' folder
    do
	echo "${folder}"
	counter=0
	t=$(mktemp);
	rm -f $t.*.list
	find "${folder}" -mindepth 1 -maxdepth 1 -type d -print0 | while read -d $'\0' i
	do
	    if [[ "$i" -nt "${CAS2_DIR}/$i" ]]
	    then
		d=${i#"${folder}"/}
		bin=$(($counter % $N_PROC))
		echo $d >> "$t.$bin.list"
		counter=$(($counter+1))
	    fi
	done
	for ((j=0; j<${N_PROC}; j++))
	do
	    if [[ -f "$t.$j.list" ]]
	    then
		mkdir -p ${TMP_DIR}/tpcas-1/"${folder}.$j"
		for k in $(cat $t.$j.list)
		do
		    f=$(find "${CAS1_DIR}/${folder}/$k" -name "*.tpcas.gz")
		    if [[ -e "$f" ]]
		    then
			ln -s "$f" ${TMP_DIR}/tpcas-1/"${folder}.$j"/$k.tpcas.gz
			echo 1 > /tmp/worktodo
		    fi
		done
	    fi
	done
	rm -f $t.*.list
    done
    worktodo=$(cat /tmp/worktodo)
    # perform lexical annotation
    if (( $worktodo > 0 ))
    then
	#
	# prepare pcrelations table in postgres
	echo "drop table pcrelations" | psql www-data
	TABLELIST=$(echo "select tablename from pg_tables" | psql www-data | grep pcrelations)
	FIRSTTABLE=$(echo $TABLELIST | cut -f 1 -d " ");
	echo "create table pcrelations as (select * from $FIRSTTABLE) with no data" | psql www-data
	for j in $TABLELIST
	do
	    echo Inserting $j
	    echo "insert into pcrelations select * from $j" | psql www-data
	done
	cd ${TMP_DIR}/tpcas-1    
	# prepare tpontology table in postgres
	echo "drop table tpontology" | psql www-data
	TABLELIST=$(echo "select tablename from pg_tables" | psql www-data | grep tpontology)
	FIRSTTABLE=$(echo $TABLELIST | cut -f 1 -d " ");
	TABLEARRAY=($TABLELIST)
	echo "create table tpontology as (select * from $FIRSTTABLE) with no data" | psql www-data
	FIRSTTIME=1
	i=0
	# if we wanted to swap this following while loop with one big folder loop in the interest
	# of saving disk space, we shouldn't do it because we lose parallelization.
	while (( i < ${#TABLEARRAY[@]}))
	do
	    echo "delete from tpontology" | psql www-data
	    while
		if [[ ${TABLEARRAY[$i]} != "" ]]
		then
		    echo Inserting ${TABLEARRAY[$i]}
		    echo "insert into tpontology select * from ${TABLEARRAY[$i]}" | psql www-data
		fi
		i=$((i+1))
		s=$(echo "select count(*) from tpontology" | psql www-data )
		j=$(echo $s | cut -f 3 -d " ")
   		(( j < 2500000)) && (( i < ${#TABLEARRAY[@]}))
	    do true; done
	    # UIMA analysis for all folders
	    fcount=0
	    find . -mindepth 1 -maxdepth 1 -type d -print0 | while read -d $'\0' folder
	    do
		# create dir structure if it does not exist
		mkdir -p ${TMP_DIR}/tpcas-2/"${folder}"
		mkdir -p ${TMP_DIR}/tpcas-2/"1.${folder#./}"
		# decompress all tpcas files in tmp dir before processing them
		find "${folder}" -name "*.tpcas.gz" | xargs -n 8 -P 8 -I "{}" gunzip -f {}
		if (( $FIRSTTIME > 0 ))
		then
		    runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi "${TMP_DIR}/tpcas-1/${folder}" "${TMP_DIR}/tpcas-2/${folder}" &
		else
		    runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi "${TMP_DIR}/tpcas-2/1.${folder#./}" "${TMP_DIR}/tpcas-2/${folder}" &
		fi
		fcount=$((fcount+1))
		if [[ $(($fcount % ${N_PROC})) == 0 ]]
		then
		    wait
		fi
	    done
	    wait
	    find . -name "*.tpcas" | xargs -n 8 -P 8 -I "{}" rm {}
	    FIRSTTIME=0
	    find . -mindepth 1 -maxdepth 1 -type d -print0 | while read -d $'\0' folder
	    do
		find ${TMP_DIR}/tpcas-2/"${folder}" -name "*tpcas" | xargs -I {} -n 1 -P ${N_PROC} mv {} ${TMP_DIR}/tpcas-2/1."${folder#./}"/.
	    done
	done
	find . -mindepth 1 -maxdepth 1 -type d -print0 | while read -d $'\0' folder
	do
	    find ${TMP_DIR}/tpcas-2/1."${folder#./}" -name "*tpcas" | xargs -I {} -n 1 -P ${N_PROC} mv {} ${TMP_DIR}/tpcas-2/"${folder}"/.
	    rm -rf ${TMP_DIR}/tpcas-2/1."${folder#./}"
	done
	echo "drop table pcrelations" | psql www-data
	echo "drop table tpontology" | psql www-data
	
	# COMPRESS THE RESULTS
	find -L ${TMP_DIR}/tpcas-2 -name *.tpcas -print0 | xargs -0 -n 8 -P ${N_PROC} pigz
	# COPY TPCAS2 DIRS IN TMPDIR TO TPCAS-2
	cd ${TMP_DIR}/tpcas-2
	find . -mindepth 1 -maxdepth 1 -type d -print0 | while read -d $'\0' folder
	do
	    find "${folder}" -mindepth 1 -maxdepth 1 -print0 | while read -d $'\0' i
	    do
		dirname=$(basename $(echo "${i#${folder}}" | sed 's/.tpcas.gz//'))
		casfolder=$(echo "${folder}" | sed 's/\.[0-9]\+$//')
		mkdir -p "${CAS2_DIR}/${casfolder}/${dirname}"
		if [[ -d "${CAS1_DIR}/${casfolder}/${dirname}" ]]
		then
		    tpcas_file_name=$(ls "${CAS1_DIR}/${casfolder}/${dirname}"/*.tpcas.gz | head -n1 | awk 'BEGIN{FS="/"}{print $NF}')
		    ln -s -f "${CAS1_DIR}/${casfolder}/${dirname}/images" "${CAS2_DIR}/${casfolder}/${dirname}/."
		    mv "$i" "${CAS2_DIR}/${casfolder}/${dirname}/${tpcas_file_name}"
		fi
	    done
	done
    fi
    # remove tmp files, should be redundant, but once in while there a core files
    rm -rf ${TMP_DIR}/tpcas-1
    rm -rf ${TMP_DIR}/tpcas-2
    rm ${LOCKFILE}
fi
