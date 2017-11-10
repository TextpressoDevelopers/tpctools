#!/usr/bin/env bash

function usage {
    echo "this is the main tpc pipeline script. It downloads articles from tazendra (C. elegans pdf) and PMCOA (xml), "
    echo "and converts them into uima cas files with the addition of semantic annotations. The script maintains a list "
    echo "of the downloaded files and performs incremental updates. It can be executed periodically to maintain an "
    echo "updated cas files repository"
    echo
    echo "usage: $(basename $0) [-p]"
    echo "  -p --pdf-dir      directory where raw pdf files will be stored"
    echo "  -x --xml-dir      directory where raw xml files will be stored"
    echo "  -c --cas1-dir     directory where generated cas1 files will be stored"
    echo "  -C --cas2-dir     directory where generated cas2 files will be stored"
    echo "  -t --tmp-dir      temp directory"
    echo "  -f --ftp-dir      ftp mount point for pmcoa papers"
    echo "  -P --num-proc     maximum number of parallel processes"
    echo "  -h --help         display help"
    exit 1
}

if [[ "${#}" < 2 ]]
then
    usage
fi

PDF_DIR="/data/textpresso/raw_files/pdf"
XML_DIR="/data/textpresso/raw_files/xml"
CAS2_DIR="/data/textpresso/tpcas-2"
CAS1_DIR="/data/textpresso/tpcas-1"
TMP_DIR="/data/textpresso/tmp"
FTP_MNTPNT="/mnt/pmc_ftp"
INDEX_DIR="/data/textpresso/luceneindex"
N_PROC=1

while [[ $# -gt 0 ]]
do
key=$1

case $key in
    -p|--pdf-dir)
    shift
    if [[ -d $key ]]
    then
        PDF_DIR="$key"
    fi
    shift
    ;;
    -x|--xml-dir)
    shift
    if [[ -d $key ]]
    then
        XML_DIR="$key"
    fi
    shift
    ;;
    -c|--cas1-dir)
    shift
    if [[ -d $key ]]
    then
        CAS1_DIR="$key"
    fi
    shift
    ;;
    -C|--cas2-dir)
    shift
    if [[ -d $key ]]
    then
        CAS2_DIR="$key"
    fi
    shift
    ;;
    -t|--tmp-dir)
    shift
    if [[ -d $key ]]
    then
        TMP_DIR="$key"
    fi
    shift
    ;;
    -f|--ftp-dir)
    shift
    if [[ -d $key ]]
    then
        FTP_MNTPNT="$key"
    fi
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

# temp files
logfile=$(mktemp)
newpdf_list=$(mktemp)
removedpdf_list=$(mktemp)
newxml_list=$(mktemp)
newxml_local_list=$(mktemp)

# download new xml files from pmcoa
## create directory for unclassified xml files
mkdir -p ${XML_DIR}
mkdir -p ${FTP_MNTPNT}
## mount pmcoa ftp locally through curl
curlftpfs ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/ ${FTP_MNTPNT}
# retrieve a list of files on pmcoa
for dir in ${FTP_MNTPNT}/*; do for subdir in ${dir}/*; do ls -d -l --time-style="full-iso" ${subdir}/* | awk '{print $6, $7, $9}' >> ${newxml_list}; done; done
umount ${FTP_MNTPNT}
if [[ -e ${XML_DIR}/current_filelist.txt ]]
then
    ## download diff files
    diff ${newxml_list} ${XML_DIR}/current_filelist.txt | grep "^<" | awk '{print $3}' | awk -F"/" '{print $(NF-2)"/"$(NF-1)"/"$NF}' | xargs -n 1 -P ${N_PROC} -I {} sh -c 'wget -qO- "ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/{}" | tar xfz - --exclude="*.pdf" --exclude="*.PDF" --exclude="*.mp4" --exclude="*.webm" --exclude="*.flv" --exclude="*.avi" --exclude="*.zip" --exclude="*.mov" --exclude="*.csv" --exclude="*.xls*" --exclude="*.doc*" --exclude="*.ppt*" --exclude="*.rar" --exclude="*.txt" --exclude="*.TXT" --exclude="*.wmv" --exclude="*.DOC*" -C '"${XML_DIR}"
    ## save new current list
    diff ${newxml_list} ${XML_DIR}/current_filelist.txt | grep "^<" | awk '{print $3}' >> ${XML_DIR}/current_filelist.txt
else
    ## download all files
    awk '{print $3}' ${newxml_list} | awk -F"/" '{print $(NF-2)"/"$(NF-1)"/"$NF}' | xargs -n 1 -P ${N_PROC} -I {} sh -c 'wget -qO- "ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/{}" | tar xfz - --exclude="*.pdf" --exclude="*.PDF" --exclude="*.mp4" --exclude="*.webm" --exclude="*.flv" --exclude="*.avi" --exclude="*.zip" --exclude="*.mov" --exclude="*.csv" --exclude="*.xls*" --exclude="*.doc*" --exclude="*.ppt*" --exclude="*.rar" --exclude="*.txt" --exclude="*.TXT" --exclude="*.wmv" --exclude="*.DOC*" -C '"${XML_DIR}"
    ## save file list as current
    cp ${newxml_list} ${XML_DIR}/current_filelist.txt
fi
## save new xml local file list
cut -d " " -f 3 ${newxml_list} | sed "s/\/mnt\/pmc\_ftp\/.\{2\}\/.\{2\}\///g;s/\.tar\.gz//g" | xargs -I {} echo ${XML_DIR}/{} > ${newxml_local_list}
## compress nxml and put images in a separate directory
cat ${newxml_local_list} | xargs -I {} -n1 -P ${N_PROC} sh -c 'gzip "{}"/*.nxml; mkdir "{}"/images; ls -d "{}"/* | grep -v .nxml | grep -v "{}"/images | xargs -I [] mv [] "{}"/images'

# download new pdf files incrementally from tazendra
## download pdf files
getpdfs.py -l ${logfile} -L INFO "${PDF_DIR}"
grep -oP "Downloading paper: .* to \K.*\.pdf" ${logfile} > ${newpdf_list}
grep -oP "Removing .* paper \K.*" ${logfile} > ${removedpdf_list}
## download bib info for pdfs
mkdir -p /usr/local/textpresso/celegans_bib
download_pdfinfo.pl /usr/local/textpresso/celegans_bib/
extract_pdfbibinfo.pl  /usr/local/textpresso/celegans_bib/

# generate tpcas-1
## pdf files
mkdir -p ${CAS1_DIR}/C.\ elegans
mkdir -p ${CAS1_DIR}/C.\ elegans\ Supplementals
cd ${CAS1_DIR}
num_papers_to_process_together=$(python3 -c "from math import ceil; print(ceil($(grep -v "Supplementals" ${newpdf_list} | wc -l) / ${N_PROC}))")
n_lines_to_tail=$(grep -v "Supplementals" ${newpdf_list} | wc -l)
for ((i=1; i<=${N_PROC}; i++))
do
    articles2cas -i ${PDF_DIR}/C.\ elegans -l <(grep -v "Supplementals" ${newpdf_list} | awk -F"/" '{print $NF}' | cut -f 1 -d '.' | tail -n ${n_lines_to_tail} | head -n ${num_papers_to_process_together}) -t 1 -o C.\ elegans -p &
    n_lines_to_tail=$(($n_lines_to_tail - $num_papers_to_process_together))
done
wait
num_papers_to_process_together=$(python3 -c "from math import ceil; print(ceil($(grep "Supplementals" ${newpdf_list} | wc -l) / ${N_PROC}))")
n_lines_to_tail=$(grep "Supplementals" ${newpdf_list} | wc -l)
for ((i=1; i<=${N_PROC}; i++))
do
    articles2cas -i ${PDF_DIR}/C.\ elegans\ Supplementals -l <(grep "Supplementals" ${newpdf_list} | awk -F"/" '{print $NF}' | sed 's/.pdf//g' | tail -n ${n_lines_to_tail} | head -n ${num_papers_to_process_together}) -t 1 -o C.\ elegans\ Supplementals -p &
    n_lines_to_tail=$(($n_lines_to_tail - $num_papers_to_process_together))
done
wait

# nxml files
mkdir -p ${CAS1_DIR}/PMCOA
cd ${CAS1_DIR}
num_papers_to_process_together=$(python3 -c "from math import ceil; print(ceil($(wc -l ${newxml_local_list} | awk '{print $1}') / ${N_PROC}))")
n_lines_to_tail=$(wc -l ${newxml_local_list} | awk '{print $1}')
for ((i=1; i<=${N_PROC}; i++))
do
    articles2cas -i "${XML_DIR}" -l <(awk 'BEGIN{FS="/"}{print $NF}' ${newxml_local_list} | tail -n ${n_lines_to_tail} | head -n ${num_papers_to_process_together}) -t 2 -o PMCOA -p &
    n_lines_to_tail=$(($n_lines_to_tail - $num_papers_to_process_together))
done
wait
# TODO test from here! - redo pdf conversion for supplementals to cas1
# add images to tpcas directory and gzip
## xml
cat ${newxml_local_list} | while read line
do
    dirname=$(echo ${line} | awk 'BEGIN{FS="/"}{print $NF}')
    rm -rf "${CAS1_DIR}/PMCOA/${dirname}/images"
    ln -fs "${XML_DIR}/${dirname}/images" "${CAS1_DIR}/PMCOA/${dirname}/images"
    find "${CAS1_DIR}/PMCOA/${dirname}" -name *.tpcas | xargs -I {} gzip "{}"
done
## pdf
cat ${newpdf_list} | while read line
do
    gzip "${CAS1_DIR}"/$(echo "${line}" | awk 'BEGIN{FS="/"}{print $NF-2"/"$NF-1"/"$NF}' | sed 's/.pdf/.tpcas/g')
done

# generate cas2 files from cas1
## copy files to temp directory
rm -rf ${TMP_DIR}/tpcas-1
## xml
mkdir -p ${TMP_DIR}/tpcas-1/xml
cat ${newxml_local_list} | while read line
do
    dirname=$(echo ${line} | awk 'BEGIN{FS="/"}{print $NF}')
    find "${CAS1_DIR}/PMCOA/${dirname}" -name *.tpcas.gz | xargs -I {} cp "{}" ${TMP_DIR}/tpcas-1/xml/${dirname}.tpcas.gz
done

mkdir -p ${TMP_DIR}/tpcas-1/pdf_celegans
mkdir -p ${TMP_DIR}/tpcas-1/pdf_celegans_sup
grep -v "Supplementals" ${newpdf_list} | while read line
do
    find "${CAS1_DIR}/C. elegans/$(echo ${line} | awk -F\"/\" '{print $(NF-1)}')" -name *.tpcas.gz | xargs -I {} cp "{}" ${TMP_DIR}/tpcas-1/pdf_celegans/${line}.tpcas.gz
done
grep "Supplementals" ${newpdf_list} | while read line
do
    find "${CAS1_DIR}/C. elegans Supplementals/$(echo ${line} | awk -F\"/\" '{print $(NF-1)}')" -name *.tpcas.gz | xargs -I {} cp "{}" ${TMP_DIR}/tpcas-1/pdf_celegans_sup/${line}.tpcas.gz
done

## apply uima analysis
rm -rf "${TMP_DIR}/tpcas-2"
mkdir -p "${TMP_DIR}/tpcas-2/xml"
mkdir -p "${TMP_DIR}/tpcas-2/pdf_celegans"
mkdir -p "${TMP_DIR}/tpcas-2/pdf_celegans_sup"
find ${TMP_DIR}/tpcas-1 -name *.tpcas.gz | xargs -n 1 -P ${N_PROC} gunzip
runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi ${TMP_DIR}/tpcas-1/xml ${TMP_DIR}/tpcas-2/xml
runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi ${TMP_DIR}/tpcas-1/pdf_celegans ${TMP_DIR}/tpcas-2/pdf_celegans
runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi ${TMP_DIR}/tpcas-1/pdf_celegans_sup ${TMP_DIR}/tpcas-2/pdf_celegans_sup
find ${TMP_DIR}/tpcas-2 -name *.tpcas | xargs -n 1 -P ${N_PROC} gzip

# copy tpcas1 dirs to tpcas2 and replace tpcas files with the new ones
mkdir -p "${CAS2_DIR}/PMCOA"
mkdir -p "${CAS2_DIR}/C. elegans"
mkdir -p "${CAS2_DIR}/C. elegans Supplementals"
## xml
cat ${newxml_local_list} | while read line
do
    dirname=$(echo ${line} | awk 'BEGIN{FS="/"}{print $NF}')
    tpcas_file_name=$(ls ${CAS1_DIR}/PMCOA/${dirname}/*.tpcas.gz | awk 'BEGIN{FS="/"}{print $NF}')
    mkdir "${CAS2_DIR}/PMCOA/${dirname}"
    ln -s "${CAS1_DIR}/PMCOA/${dirname}/images" "${CAS2_DIR}/PMCOA/${dirname}/images"
    cp ${TMP_DIR}/tpcas-2/xml/${dirname}.tpcas.gz "${CAS2_DIR}/PMCOA/${dirname}/${tpcas_file_name}"
done
## pdf
grep -v "Supplementals" ${newpdf_list} | while read line
do
    mkdir "${CAS2_DIR}/C. elegans/$(echo ${line} | awk -F\"/\" '{print $(NF-1)}')"
    ln -s "${CAS1_DIR}/C. elegans/$(echo ${line} | awk -F\"/\" '{print $(NF-1)}')/images" "${CAS2_DIR}/C. elegans/${line}/images"
    find "${CAS1_DIR}/C. elegans/$(echo ${line} | awk -F\"/\" '{print $(NF-1)}')/" -name *.tpcas.gz | awk 'BEGIN{FS="/"}{print $NF}' | xargs -I {} cp ${TMP_DIR}/tpcas-1/pdf_celegans/"{}" "${CAS2_DIR}/C. elegans/$(echo ${line} | awk -F\"/\" '{print $(NF-1)}')/"
done
grep "Supplementals" ${newpdf_list} | while read line
do
    mkdir "${CAS2_DIR}/C. elegans Supplementals/$(echo ${line} | awk -F\"/\" '{print $(NF-1)}')"
    ln -s "${CAS1_DIR}/C. elegans Supplementals/$(echo ${line} | awk -F\"/\" '{print $(NF-1)}')/images" "${CAS2_DIR}/C. elegans Supplementals/$(echo ${line} | awk -F\"/\" '{print $(NF-1)}')/images"
    find "${CAS1_DIR}/C. elegans Supplementals/$(echo ${line} | awk -F\"/\" '{print $(NF-1)}')/" -name *.tpcas.gz | awk 'BEGIN{FS="/"}{print $NF}' | xargs -I {} cp ${TMP_DIR}/tpcas-1/pdf_celegans/"{}" "${CAS2_DIR}/C. elegans Supplementals/$(echo ${line} | awk -F\"/\" '{print $(NF-1)}')/"
done

# generate bib files for cas files
getallbibfiles.sh -p ${N_PROC} ${CAS2_DIR}

if [[ ! -d ${INDEX_DIR} || $(ls ${INDEX_DIR} | grep -v "subindex_0" | wc -l) == "0" ]]
then
    mkdir -p ${INDEX_DIR}
    create_single_index.sh -m 100000 ${CAS2_DIR} ${INDEX_DIR}
else
    ## pdf
    cas2index -i ${CAS2_DIR} -o ${INDEX_DIR} -a <(grep -v "Supplemental" ${newpdf_list} | awk -v cas2_dir="${CAS2_DIR}" -F"/" '{print cas2_dir"/C. elegans/"$(NF-1)}' | xargs -I {} find "{}" -name  *.tpcas.gz)
    cas2index -i ${CAS2_DIR} -o ${INDEX_DIR} -a <(grep "Supplemental" ${newpdf_list} | awk -v cas2_dir="${CAS2_DIR}" -F"/" '{print cas2_dir"/C. elegans Supplementals/"$(NF-1)}' | xargs -I {} find "{}" -name  *.tpcas.gz)
    ## xml
    cas2index -i ${CAS2_DIR} -o ${INDEX_DIR} -a <(awk -v cas2_dir="${CAS2_DIR}" -F"/" '{print cas2_dir"/PMCOA/"$NF}' ${newxml_local_list} | xargs -I {} find "{}" -name  *.tpcas.gz)
fi

# remove deleted or invalidated papers from cas dirs and from index
cas2index -i ${CAS2_DIR} -o ${INDEX_DIR} -r <(grep -v "Supplemental" ${removedpdf_list} | awk -v cas2_dir="${CAS2_DIR}" -F"/" '{print cas2_dir"/C. elegans/"$(NF-1)}' | xargs -I {} find "{}" -name  *.tpcas.gz)
cas2index -i ${CAS2_DIR} -o ${INDEX_DIR} -r <(grep "Supplemental" ${removedpdf_list} | awk -v cas2_dir="${CAS2_DIR}" -F"/" '{print cas2_dir"/C. elegans Supplementals/"$(NF-1)}' | xargs -I {} find "{}"* -name  *.tpcas.gz)
awk -F"/" '{print $(NF-1)"/"$NF}' ${removedpdf_list} | xargs -I {} sh -c 'rm -rf ${CAS1_DIR}/"{}"*; rm -rf ${CAS2_DIR}/"{}"*'

# cleanup tmp files
rm -rf ${TMP_DIR}
rm ${logfile}
rm ${newpdf_list}
rm ${newxml_list}
rm ${newxml_local_list}