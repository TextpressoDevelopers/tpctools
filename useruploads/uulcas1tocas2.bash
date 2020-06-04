#!/bin/bash
# 
# File:   uulcas1tocas2.bash
# Author: mueller
#
# Created on Jun 2, 2020, 1:16:21 AM
#

CAS1_DIR="$1"
CAS2_DIR="$2"
TMP_DIR="$3"
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/lib
export PATH=$PATH:/usr/local/bin
#
rm -rf ${TMP_DIR}/tpcas-1
rm -rf ${TMP_DIR}/tpcas-2
# create dir structure if it does not exist
mkdir -p ${TMP_DIR}/tpcas-1
mkdir -p ${TMP_DIR}/tpcas-2/1
mkdir -p ${TMP_DIR}/tpcas-2/2
    
# prepare files to be processed
find ${CAS1_DIR} -mindepth 1 -maxdepth 1 -print0 -name "*.tpcas" | while read -d $'\0' file
do
    cp "$file" ${TMP_DIR}/tpcas-1/.
done
# perform lexical annotation
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
# prepare tpontology table in postgres
echo "drop table tpontology" | psql www-data
TABLELIST=$(echo "select tablename from pg_tables" | psql www-data | grep tpontology)
FIRSTTABLE=$(echo $TABLELIST | cut -f 1 -d " ");
TABLEARRAY=($TABLELIST)
echo "create table tpontology as (select * from $FIRSTTABLE) with no data" | psql www-data
FIRSTTIME=1
i=0
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
    if (( $FIRSTTIME > 0 ))
        then
            runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi "${TMP_DIR}/tpcas-1/" "${TMP_DIR}/tpcas-2/2"
        else
            runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi "${TMP_DIR}/tpcas-2/1" "${TMP_DIR}/tpcas-2/2"
    fi
    FIRSTTIME=0
    find ${TMP_DIR}/tpcas-2/2 -name "*.tpcas" | xargs -I {} -n 1 mv {} ${TMP_DIR}/tpcas-2/1/.
done
find ${TMP_DIR}/tpcas-2/1 -name "*.tpcas" | xargs -I {} -n 1 mv {} ${TMP_DIR}/tpcas-2/2/.
# COPY TPCAS2 DIRS IN TMPDIR TO TPCAS-2
find ${TMP_DIR}/tpcas-2/2 -name "*.tpcas" | xargs -I {} -n 1 mv {} ${CAS2_DIR}/.

# remove tables in postgres
echo "drop table pcrelations" | psql www-data
echo "drop table tpontology" | psql www-data
	
# remove tmp files
rm -rf ${TMP_DIR}/tpcas-1
rm -rf ${TMP_DIR}/tpcas-2
