#!/usr/bin/env bash

function usage {
    echo "this is the main tpc pipeline script. It downloads articles from tazendra (C. elegans pdf) and PMCOA (xml), "
    echo "and converts them into uima cas files with the addition of semantic annotations and it indexes them into "
    echo "lucene. The script maintains a list of the downloaded files and performs incremental updates. It can be "
    echo "executed periodically to maintain the repository updated"
    echo
    echo "usage: $(basename $0) [-pxcCtfiPeh]"
    echo "  -p --pdf-dir      directory where raw pdf files will be stored"
    echo "  -x --xml-dir      directory where raw xml files will be stored"
    echo "  -c --cas1-dir     directory where generated cas1 files will be stored"
    echo "  -C --cas2-dir     directory where generated cas2 files will be stored"
    echo "  -t --tmp-dir      temp directory"
    echo "  -f --ftp-dir      ftp mount point for pmcoa papers"
    echo "  -i --index-dir    directory for the lucene index"
    echo "  -P --num-proc     maximum number of parallel processes"
    echo "  -e --exclude-step do not execute the steps specified by a comma separated list of step names. Step names "
    echo "                    are: download_pdf,download_xml,cas1,cas2,bib,index,invert_img,remove_invalidated,remove_temp."
    echo "  -h --help         display help"
    exit 1
}

function array_contains {
    length=$(($#-1))
    array=(${@:1:$length})
    element_idx=$((length + 1))
    check=${@:$element_idx:$element_idx}
    found="0"
    for value in "${array[@]}"
    do
        if [[ ${value} == ${check} ]]
        then
            found="1"
        fi
    done
    echo ${found}
}

PDF_DIR="/data/textpresso/raw_files/pdf"
XML_DIR="/data/textpresso/raw_files/xml"
CAS2_DIR="/data/textpresso/tpcas-2"
CAS1_DIR="/data/textpresso/tpcas-1"
TMP_DIR="/data/textpresso/tmp"
FTP_MNTPNT="/mnt/pmc_ftp"
INDEX_DIR="/data/textpresso/luceneindex"
N_PROC=1
EXCLUDE_STEPS=""
PAPERS_PER_SUBINDEX=1000000

while [[ $# -gt 0 ]]
do
key=$1

case $key in
    -p|--pdf-dir)
    shift
    PDF_DIR="$1"
    shift
    ;;
    -x|--xml-dir)
    shift
    XML_DIR="$1"
    shift
    ;;
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
    -f|--ftp-dir)
    shift
    FTP_MNTPNT="$1"
    shift
    ;;
    -i|--index-dir)
    shift
    INDEX_DIR="$1"
    shift
    ;;
    -P|--num-proc)
    shift
    N_PROC=$1
    shift
    ;;
    -e|--exclude-step)
    shift
    EXCLUDE_STEPS=($(echo "$1" | tr ',' '\n'))
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

# temp files
logfile=$(mktemp)
newpdf_list=$(mktemp)
removedpdf_list=$(mktemp)
newxml_list=$(mktemp)
newxml_local_list=$(mktemp)
diffxml_list=$(mktemp)

#################################################################################
#####                      1. DOWNLOAD PAPERS                               #####
#################################################################################

if [[ $(array_contains "${EXCLUDE_STEPS[@]}" "download_xml") == "0" ]]
then
    echo "Downloading xml papers ..."
    # 1.1 XML FROM PMCOA

    # 1.1.1 create directory for unclassified xml files
    mkdir -p ${XML_DIR}
    mkdir -p ${FTP_MNTPNT}
    # 1.1.2 mount pmcoa ftp locally through curl
    curlftpfs ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/ ${FTP_MNTPNT}
    # 1.1.3 retrieve a list of files on pmcoa
    for dir in ${FTP_MNTPNT}/*; do for subdir in ${dir}/*; do ls -d -l --time-style="full-iso" ${subdir}/* | awk '{print $6, $7, $9}' >> ${newxml_list}; done; done
    umount ${FTP_MNTPNT}
    # 1.1.4 calculate diff between existing files and files on PMCOA and download the new ones. If there are no pre-existing files, download the full repository
    if [[ -e ${XML_DIR}/current_filelist.txt ]]
    then
        # delete previous versions
        diff ${newxml_list} ${XML_DIR}/current_filelist.txt | grep "^<" | awk '{print $4}' | awk -F"/" '{print $NF}' | sed 's/.tar.gz//g' | xargs -I {} rm -rf "${XML_DIR}/{}"
        # download diff files
        diff ${newxml_list} ${XML_DIR}/current_filelist.txt | grep "^<" | awk '{print $4}' | awk -F"/" '{print $(NF-2)"/"$(NF-1)"/"$NF}' | xargs -n 1 -P ${N_PROC} -I {} sh -c 'wget -qO- "ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/{}" | tar xfz - --exclude="*.pdf" --exclude="*.PDF" --exclude="*.mp4" --exclude="*.webm" --exclude="*.flv" --exclude="*.avi" --exclude="*.zip" --exclude="*.mov" --exclude="*.csv" --exclude="*.xls*" --exclude="*.doc*" --exclude="*.ppt*" --exclude="*.rar" --exclude="*.txt" --exclude="*.TXT" --exclude="*.wmv" --exclude="*.DOC*" -C '"${XML_DIR}"
        diff ${newxml_list} ${XML_DIR}/current_filelist.txt | grep "^<" | sed 's/< //g' > ${diffxml_list}
    else
        # download all files
        awk '{print $3}' ${newxml_list} | awk -F"/" '{print $(NF-2)"/"$(NF-1)"/"$NF}' | xargs -n 1 -P ${N_PROC} -I {} sh -c 'wget -qO- "ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/{}" | tar xfz - --exclude="*.pdf" --exclude="*.PDF" --exclude="*.mp4" --exclude="*.webm" --exclude="*.flv" --exclude="*.avi" --exclude="*.zip" --exclude="*.mov" --exclude="*.csv" --exclude="*.xls*" --exclude="*.doc*" --exclude="*.ppt*" --exclude="*.rar" --exclude="*.txt" --exclude="*.TXT" --exclude="*.wmv" --exclude="*.DOC*" -C '"${XML_DIR}"
        cp ${newxml_list} ${diffxml_list}
    fi
    # remove empty files from diff list
    tmp_diff_file=$(mktemp)
    awk '{print $3}' ${diffxml_list} | awk -F"/" '{print $NF}' | sed 's/.tar.gz//g' | xargs -I {} bash -c 'if [[ -d "$0/{}" ]]; then echo "{}"; fi' "${XML_DIR}" > ${tmp_diff_file}
    mv ${tmp_diff_file} ${diffxml_list}

    # save the current list
    cp ${newxml_list} ${XML_DIR}/current_filelist.txt
    # 1.1.5 save new xml local file list
    cat ${diffxml_list} | xargs -I {} echo "${XML_DIR}/{}" > ${newxml_local_list}
    # 1.1.6 compress nxml and put images in a separate directory
    cat ${newxml_local_list} | xargs -I {} -n1 -P ${N_PROC} sh -c 'gzip "{}"/*.nxml; mkdir "{}"/images; ls -d "{}"/* | grep -v .nxml | grep -v "{}"/images | xargs -I [] mv [] "{}"/images'
else
     echo "Download phase for xml skipped. Using files in ${PDF_DIR} and ${XML_DIR}"
    find -L ${XML_DIR} -mindepth 1 -maxdepth 1 -type d > ${newxml_local_list}
fi

if [[ $(array_contains "${EXCLUDE_STEPS[@]}" "download_pdf") == "0" ]]
then
    echo "Downloading pdf papers ..."
    mkdir -p ${PDF_DIR}
    # 1.2. download new pdf files incrementally from tazendra
    # 1.2.1 download pdf files
    getpdfs.py -l ${logfile} -L INFO "${PDF_DIR}"
    grep -oP "Downloading paper: .* to \K.*\.pdf" ${logfile} > ${newpdf_list}
    grep -oP "Removing .* paper \K.*" ${logfile} > ${removedpdf_list}
else
    echo "Download phase for pdf skipped. Using files in ${PDF_DIR} and ${XML_DIR}"
    # use current files as 'new' and process them
    find -L "${PDF_DIR}" -mindepth 3 -maxdepth 3 -name "*.pdf" > ${newpdf_list}
    # remove previous tpcas versions
fi


#################################################################################
#####                      2. GENERATE TPCAS-1                              #####
#################################################################################

if [[ $(array_contains "${EXCLUDE_STEPS[@]}" "cas1") == "0" ]]
then
    echo "Generating CAS1 files ..."

    # 2.1 PDF FILES
    cd ${PDF_DIR}
    # obtain all the folder names in PDF_DIR then create tpcas1 folders for every corpus
    for folder in */ ; do
        mkdir -p "${CAS1_DIR}/${folder}"
    done
    cd ${CAS1_DIR}

    # generate TPCAS-1 for every corpus
    for folder in */ ; do
        echo ${folder}
        num_papers_to_process_together=$(python3 -c "from math import ceil; print(ceil($(grep "${PDF_DIR}/${folder}" ${newpdf_list} | wc -l) / ${N_PROC}))")
        n_lines_to_tail=$(grep "${PDF_DIR}/${folder}" ${newpdf_list} | wc -l)
        for ((i=1; i<=${N_PROC}; i++))
        do
            grep "${PDF_DIR}/${folder}" ${newpdf_list} | awk -F"/" '{print $NF}' | sed 's/.pdf//g' | tail -n ${n_lines_to_tail} | head -n ${num_papers_to_process_together} > /tmp/tmplist_$i.txt
            articles2cas -i "${PDF_DIR}/${folder}" -l /tmp/tmplist_$i.txt -t 1 -o "${folder}" -p &
            n_lines_to_tail=$(($n_lines_to_tail - $num_papers_to_process_together))
        done
        wait
        rm /tmp/tmplist_*.txt
    done

    # 2.2 XML FILES

    # remove old versions
    awk -F"/" '{print $NF}' ${newxml_local_list} | xargs -I {} rm -rf "${CAS1_DIR}/PMCOA/{}"

    mkdir -p ${CAS1_DIR}/PMCOA
    cd ${CAS1_DIR}
    num_papers_to_process_together=$(python3 -c "from math import ceil; print(ceil($(wc -l ${newxml_local_list} | awk '{print $1}') / ${N_PROC}))")
    n_lines_to_tail=$(wc -l ${newxml_local_list} | awk '{print $1}')
    for ((i=1; i<=${N_PROC}; i++))
    do
        awk 'BEGIN{FS="/"}{print $NF}' ${newxml_local_list} | tail -n ${n_lines_to_tail} | head -n ${num_papers_to_process_together} > /tmp/tmplist_$i.txt
        articles2cas -i "${XML_DIR}" -l /tmp/tmplist_$i.txt -t 2 -o PMCOA -p > logfile_$i.log &
        n_lines_to_tail=$(($n_lines_to_tail - $num_papers_to_process_together))
    done
    wait
    rm /tmp/tmplist_*.txt
    rm logfile_*.log

    # 2.3 add images to tpcas directory and gzip

    # 2.3.1 xml
    cat ${newxml_local_list} | awk 'BEGIN{FS="/"}{print $NF}' | xargs -n1 -P ${N_PROC} -I {} sh -c 'dirname=$(echo "{}"); rm -rf "$0/PMCOA/${dirname}/images";  ln -fs "$1/${dirname}/images" "$0/PMCOA/${dirname}/images"; find -L "$0/PMCOA/${dirname}" -name "*.tpcas" | xargs -I [] gzip -f "[]"' ${CAS1_DIR} ${XML_DIR}
    # 2.3.2 pdf
    cat ${newpdf_list} | xargs -n1 -P ${N_PROC} -I {} echo "{}" | awk 'BEGIN{FS="/"}{print $(NF-2)"/"$(NF-1)"/"$NF}' | sed 's/\.pdf/\.tpcas/g' | xargs -I [] gzip -f "[]"
fi

#################################################################################
#####                     3. GENERATE CAS-2                                 #####
#################################################################################

if [[ $(array_contains "${EXCLUDE_STEPS[@]}" "cas2") == "0" ]]
then
    echo "Generating CAS2 files ..."
    # 3.1 COPY FILES TO TMP DIR

    # 3.1.1 xml - subdirs are processed in parallel
    mkdir -p ${TMP_DIR}/tpcas-1/xml
    i=1
    subdir_idx=1
    num_papers_to_process_together=$(python3 -c "from math import ceil; print(ceil($(wc -l ${newxml_local_list} | awk '{print $1}') / ${N_PROC}))")
    mkdir -p ${TMP_DIR}/tpcas-1/xml/subdir_1
    cat ${newxml_local_list} | while read line
    do
        if [[ "$i" -gt "$num_papers_to_process_together" ]]
        then
            i=0
            subdir_idx=$((subdir_idx+1))
            mkdir -p ${TMP_DIR}/tpcas-1/xml/subdir_${subdir_idx}
        fi
        dirname=$(echo ${line} | awk 'BEGIN{FS="/"}{print $NF}')
        find -L "${CAS1_DIR}/PMCOA/${dirname}" -name *.tpcas.gz | xargs -I {} cp "{}" "${TMP_DIR}/tpcas-1/xml/subdir_${subdir_idx}/${dirname}.tpcas.gz"
        i=$((i+1))
    done

    # 3.1.2 pdf
    cd ${CAS1_DIR}
    for folder in */ ; do
        mkdir -p ${TMP_DIR}/tpcas-1/"${folder}"
    done

    cat ${newpdf_list} | awk -F"/" '{print $(NF-2)"/"$(NF-1)}' | while read line
    do
        tpcas1_filename=$(echo ${line} | awk -F"/" '{print $(NF)}')
        tpcas1_file=$(echo "${CAS1_DIR}/${line}/${tpcas1_filename}.tpcas.gz")
        echo ${tpcas1_file} | xargs -I {} cp "{}" "${TMP_DIR}/tpcas-1/${line}.tpcas.gz"
    done

    # 3.2 APPLY UIMA ANALYSIS
    # create dir structure if it does not exist
    for subdir in $(ls ${TMP_DIR}/tpcas-1/xml)
    do
        mkdir -p ${TMP_DIR}/tpcas-2/xml/${subdir}
        mkdir -p ${TMP_DIR}/tpcas-2/xml/1.${subdir}
    done
    for folder in */ ; do
        mkdir -p ${TMP_DIR}/tpcas-2/"${folder}"
        mkdir -p ${TMP_DIR}/tpcas-2/"1.${folder}"
    done

    # decompress all tpcas files in tmp dir before processing them
    find -L ${TMP_DIR}/tpcas-1 -name "*.tpcas.gz" -print0 | xargs -0 -n 1 -P ${N_PROC} gunzip

    # remove old versions
    awk -F"/" '{print $NF}' ${newxml_local_list} | xargs -I {} rm -rf "${CAS2_DIR}/PMCOA/{}"

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
	    i=$[i+1]
	    s=$(echo "select count(*) from tpontology" | psql www-data )
	    j=$(echo $s | cut -f 3 -d " ")
   	    (( j < 5000000)) && (( i < ${#TABLEARRAY[@]}))
	do true; done
        # UIMA analysis for nxml files
        for subdir in $(ls ${TMP_DIR}/tpcas-1/xml)
        do
            if (( $FIRSTTIME > 0 ))
            then
                runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi ${TMP_DIR}/tpcas-1/xml/${subdir} ${TMP_DIR}/tpcas-2/xml/${subdir} &
            else
                runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi ${TMP_DIR}/tpcas-2/xml/1.${subdir} ${TMP_DIR}/tpcas-2/xml/${subdir} &
            fi
        done
	wait
        # UIMA analysis for pdf files
        for folder in */ ; do
            if (( $FIRSTTIME > 0 ))
            then
                runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi "${TMP_DIR}/tpcas-1/${folder}" "${TMP_DIR}/tpcas-2/${folder}" &
            else
                runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi "${TMP_DIR}/tpcas-2/1.${folder}" "${TMP_DIR}/tpcas-2/${folder}" &
            fi
        done
	wait
	FIRSTTIME=0
        for subdir in $(ls ${TMP_DIR}/tpcas-1/xml)
        do
	    find ${TMP_DIR}/tpcas-2/xml/${subdir} -name "*tpcas" | xargs -I {} -n 1 -P ${N_PROC} mv {} ${TMP_DIR}/tpcas-2/xml/1.${subdir}/.
        done
        for folder in */
        do
	    find ${TMP_DIR}/tpcas-2/"${folder}" -name "*tpcas" | xargs -I {} -n 1 -P ${N_PROC} mv {} ${TMP_DIR}/tpcas-2/1."${folder}"/.
        done
    done
    for subdir in $(ls ${TMP_DIR}/tpcas-1/xml)
    do  
	find ${TMP_DIR}/tpcas-2/xml/1.${subdir} -name "*tpcas" | xargs -I {} -n 1 -P ${N_PROC} mv {} ${TMP_DIR}/tpcas-2/xml/.
    done
    for folder in */
    do
	find ${TMP_DIR}/tpcas-2/1."${folder}" -name "*tpcas" | xargs -I {} -n 1 -P ${N_PROC} mv {} ${TMP_DIR}/tpcas-2/"${folder}"/.
    done
    rmdir ${TMP_DIR}/tpcas-2/xml/*/
    echo "drop table tpontology" | psql www-data
    echo "drop table pcrelations" | psql www-data

    # 3.3 COMPRESS THE RESULTS
    find -L ${TMP_DIR}/tpcas-2 -name *.tpcas -print0 | xargs -0 -n 1 -P ${N_PROC} gzip

    # 3.4 COPY TPCAS1 to TPCAS2 DIRS AND REPLACE FILES WITH NEW ONES
    mkdir -p "${CAS2_DIR}/PMCOA"
    for folder in */ ; do
        mkdir -p "${CAS2_DIR}/${folder}"
    done

    # 3.4.1 xml
    cat ${newxml_local_list} | while read line
    do
        dirname=$(echo ${line} | awk 'BEGIN{FS="/"}{print $NF}')
        if [[ -d "${CAS1_DIR}/PMCOA/${dirname}" ]]
        then
            tpcas_file_name=$(ls ${CAS1_DIR}/PMCOA/${dirname}/*.tpcas.gz | head -n1 | awk 'BEGIN{FS="/"}{print $NF}')
            mkdir -p "${CAS2_DIR}/PMCOA/${dirname}"
            if [[ -e "${CAS2_DIR}/PMCOA/${dirname}/images" ]]
            then
                rm "${CAS2_DIR}/PMCOA/${dirname}/images"
            fi
            ln -s "${CAS1_DIR}/PMCOA/${dirname}/images" "${CAS2_DIR}/PMCOA/${dirname}/images"
            cp ${TMP_DIR}/tpcas-2/xml/${dirname}.tpcas.gz "${CAS2_DIR}/PMCOA/${dirname}/${tpcas_file_name}"
        fi
    done

    # 3.4.2 pdf
    cat ${newpdf_list} | awk -F"/" '{print $(NF-2)"/"$(NF-1)}' | while read line
    do
        dir_name=$(echo ${line} | awk -F"/" '{print $(NF)}')
        corpus_name=$(echo ${line} | awk -F"/" '{print $(NF-1)}')
        tpcas_file=$(echo "${CAS1_DIR}/${line}/${dir_name}.tpcas.gz")
        mkdir -p "${CAS2_DIR}/${corpus_name}/"${dir_name}
        ln -s "${CAS1_DIR}/${corpus_name}/${dir_name}/images" "${CAS2_DIR}/${corpus_name}/${dir_name}/images"
        cp "${TMP_DIR}/tpcas-2/${line}.tpcas.gz" "${CAS2_DIR}/${line}/${dir_name}.tpcas.gz"
    done
fi

#################################################################################
#####                     4. GENERATE BIB FILES                             #####
#################################################################################

if [[ $(array_contains "${EXCLUDE_STEPS[@]}" "bib") == "0" ]]
then
    echo "Downloading bib info for pdf files ..."
    # 1.2.2 download bib info for pdfs
    mkdir -p /usr/local/textpresso/celegans_bib
    download_pdfinfo.pl /usr/local/textpresso/celegans_bib/
    extract_pdfbibinfo.pl  /usr/local/textpresso/celegans_bib/
    echo "Generating bib files ..."
    export TPCAS_PATH=${CAS2_DIR}

    # 4.1 pdf
    getbib "${CAS2_DIR}/C. elegans"
    getbib "${CAS2_DIR}/C. elegans Supplementals"


    # 4.2 xml
    cas_dir_to_process="${CAS2_DIR}/PMCOA"
    if [[ -d "${TMP_DIR}/tpcas-2/xml" ]]
    then
        cas_dir_to_process="${TMP_DIR}/tpcas-2/xml"
    fi
    if [[ $(ls ${cas_dir_to_process} | wc -l) != "0" ]]
    then
        tempdir=$(mktemp -d)
        num_papers_to_process_together=$(python3 -c "from math import ceil; print(ceil($(ls "${cas_dir_to_process}" | wc -l) / ${N_PROC}))")
        ls "${cas_dir_to_process}" | sed 's/.tpcas.gz//g' | split -l ${num_papers_to_process_together} - ${tempdir}/file_to_process-
        for file_list in $(ls ${tempdir})
        do
            getbib4nxml "${CAS2_DIR}/PMCOA" -f ${tempdir}/${file_list} &
        done
        wait
        rm -rf ${tempdir}
    fi

    # 4.3 xenbase
    download_abstract.py --tpcas2_dir /data/textpresso/tpcas-2/xenbase/ --chunk_size 300
    make_bib.py --tpcas2_dir /data/textpresso/tpcas-2/xenbase/
fi

#################################################################################
#####                     5. INVERT IMAGES                                  #####
#################################################################################

if [[ $(array_contains "${EXCLUDE_STEPS[@]}" "invert_img") == "0" ]]
then
    cat ${newpdf_list} | awk -F"/" '{print $(NF-2)"/"$(NF-1)}' | while read line
    do
        dir_name=$(echo ${line} | awk -F"/" '{print $(NF)}')
        corpus_name=$(echo ${line} | awk -F"/" '{print $(NF-1)}')
        cmykinverter "${CAS1_DIR}/${line}/images"
    done
fi


#################################################################################
#####                     6. UPDATE INDEX                                   #####
#################################################################################

if [[ $(array_contains "${EXCLUDE_STEPS[@]}" "index") == "0" ]]
then
    echo "Updating index ..."
    export INDEX_PATH=${INDEX_DIR}
    INDEX_DIR_CUR="${INDEX_DIR}"
    if [[ -d ${INDEX_DIR} && $(ls ${INDEX_DIR} | grep -v "subindex_0" | wc -l) != "0" ]]
    then
        INDEX_DIR_CUR="${INDEX_DIR}_new"
    fi
    mkdir -p "${INDEX_DIR_CUR}/db"
    create_single_index.sh -m 100000 ${CAS2_DIR} ${INDEX_DIR_CUR}
    cd "${INDEX_DIR_CUR}"
    num_subidx_step=$(echo "${PAPERS_PER_SUBINDEX}/100000" | bc)
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
fi

#################################################################################
#####                  7. REMOVE INVALIDATED PAPERS                         #####
#################################################################################

if [[ $(array_contains "${EXCLUDE_STEPS[@]}" "remove_invalidated") == "0" ]]
then
    echo "Removing invalid papers deleted from server ..."
    # remove deleted or invalidated papers from cas dirs and from index
    templist=$(mktemp)
    grep -v "Supplemental" ${removedpdf_list} | awk -v cas2_dir="${CAS2_DIR}" -F"/" '{print cas2_dir"/C. elegans/"$(NF-1)}' | xargs -I {} find -L "{}" -name  *.tpcas.gz | awk -F "/" '{print $(NF-2)"/"$(NF-1)"/"$NF}' > ${templist}
    cas2index -i ${CAS2_DIR} -o ${INDEX_DIR} -r ${templist}
    grep "Supplemental" ${removedpdf_list} | awk -v cas2_dir="${CAS2_DIR}" -F"/" '{print cas2_dir"/C. elegans Supplementals/"$(NF-1)}' | xargs -I {} find -L "{}"* -name  *.tpcas.gz | awk -F "/" '{print $(NF-2)"/"$(NF-1)"/"$NF}' > ${templist}
    cas2index -i ${CAS2_DIR} -o ${INDEX_DIR} -r ${templist}
    awk -F"/" '{print $(NF-1)"/"$NF}' ${removedpdf_list} | xargs -I {} sh -c 'rm -rf ${CAS1_DIR}/"{}"*; rm -rf ${CAS2_DIR}/"{}"*'
fi

echo "Cleaning up temp files ..."
# delete tmp files
if [[ $(array_contains "${EXCLUDE_STEPS[@]}" "remove_temp") == "0" ]] # for testing/debugging purposes
then
    rm -rf ${TMP_DIR}/tpcas-1
    rm -rf ${TMP_DIR}/tpcas-2
fi
rm ${logfile}
rm ${newpdf_list}
rm ${newxml_list}
rm ${newxml_local_list}
rm ${removedpdf_list}
