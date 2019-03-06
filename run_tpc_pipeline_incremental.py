import os
import argparse
import shutil
import tempfile
import math
import multiprocessing

from getpdfs.getpdfs import download_pdfs

PDF_DIR = "/data/textpresso/raw_files/pdf"
XML_DIR = "/data/textpresso/raw_files/xml"
CAS1_DIR = "/data/textpresso/tpcas-1"
CAS2_DIR = "/data/textpresso/tpcas-2"
TMP_DIR = "/data/textpresso/tmp"
FTP_MNTPNT = "/mnt/pmc_ftp"
INDEX_DIR = "/data/textpresso/luceneindex"
N_PROC = 1
EXCLUDE_STEPS = ""
PAPERS_PER_SUBINDEX = 1000000

def set_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pdf-dir", action='store', default='',
                        help="directory where raw pdf files will be stored")
    parser.add_argument("-x", "--xml-dir", action='store', default='',
                        help="directory where raw xml files will be stored")
    parser.add_argument("-c", "--cas1-dir", action='store', default='',
                        help="directory where generated cas1 files will be stored")
    parser.add_argument("-C", "--cas2-dir", action='store', default='',
                        help="directory where generated cas2 files will be stored")
    parser.add_argument("-t", "--tmp-dir", action='store', default='',
                        help="temp directory")
    parser.add_argument("-f", "--ftp-dir", action='store', default='',
                        help="ftp mount point for pmcoa papers")
    parser.add_argument("-i", "--index-dir", action='store', default='',
                        help="directory for the lucene index")
    parser.add_argument("-P", "--num-proc", action='store', default='',
                        help="maximum number of parallel processes")
    parser.add_argument("-e", "--exclude-step", action='store', default='',
                        help="do not execute the steps specified by a comma separated list of step names. "
                             "Step names are: download_pdf,download_xml,cas1,cas2,bib,index,"
                             "invert_img,remove_invalidated,remove_temp.")
    args = parser.parse_args()
    print(args)
    if args.p:
        PDF_DIR = args.p
    if args.x:
        XML_DIR = args.x
    if args.c:
        CAS1_DIR = args.c
    if args.C:
        CAS2_DIR = args.C
    if args.t:
        TMP_DIR = args.t
    if args.f:
        FTP_MNTPNT = args.f
    if args.i:
        INDEX_DIR = args.i
    if args.P:
        N_PROC = int(args.P)
    if args.e:
        EXCLUDE_STEPS = args.e

def cas1_worker(tmp_file_idx, corpus):
    input_folder = os.path.join(PDF_DIR, corpus)
    output_folder = corpus
    tempfile = "/tmp/tmplist_{}".format(tmp_file_idx)
    os.system('article2cas -i {} -l {} -t 1 -o {}'.format(input_folder, tempfile, output_folder))

def generate_tpcas1():
    os.chdir(CAS1_DIR)
    for corpus in [d for d in os.listdir(CAS1_DIR) if os.path.isdir(os.path.join(CAS1_DIR, d))]:
        print(corpus)
        corpus_pdf_list = corpus_pdf_dict[corpus]
        n_pdf_per_process = [math.floor(len(corpus_pdf_list) / N_PROC)] * N_PROC
        for i in range(len(corpus_pdf_list) % N_PROC):
            n_pdf_per_process[i] += 1

        # split files for multiprocessing
        curr_idx = 0
        for proc_idx in range(N_PROC):
            with open('/tmp/tmplist_{}.txt'.format(proc_idx), 'w') as fpout:
                for filename in corpus_pdf_list[curr_idx:curr_idx + n_pdf_per_process[proc_idx]]:
                    fpout.write(filename + '\n')
            curr_idx += n_pdf_per_process[proc_idx]

        jobs = list()
        for proc_idx in range(N_PROC):
            p = multiprocessing.Process(target=cas1_worker, args=(proc_idx, corpus,))
            jobs.append(p)
            p.start()

        for job in jobs:
            job.join()

        for proc_idx in range(N_RPOC):
            os.remove('/tmp/tmplist_{}.txt'.format(proc_idx))

if __name__ == '__main__':
    set_argument_parser()

    os.environ['LD_LIBRARY_PATH'] = "{}:/usr/local/lib".format(os.environ['LD_LIBRARY_PATH'])
    os.environ['PATH'] = "{}:/usr/local/bin".format(os.environ['PATH'])

    logfile_fp = tempfile.TemporaryFile()
    newpdf_list_fp = tempfile.TemporaryFile()
    removedpdf_list_fp = tempfile.TemporaryFile()
    newxml_list_fp = tempfile.TemporaryFile()
    newxml_local_list_fp = tempfile.TemporaryFile()
    diffxml_list_fp = tempfile.TemporaryFile()

    excluded_steps = EXCLUDE_STEPS.split(',')

    #################################################################################
    #####                      1. DOWNLOAD PAPERS                               #####
    #################################################################################
    if 'download_xml' not in excluded_steps:
       pass

    if 'download_pdf' not in excluded_steps:
        print("Downloading pdf papers")
        if not os.path.isdir(PDF_DIR):
            os.mkdir(PDF_DIR)
        download_pdfs(False, logfile_fp.name, "INFO", PDF_DIR)

        # logging into newpdf_list and removedpdf_list does not seem necessary
        # grep - oP "Downloading paper: .* to \K.*\.pdf" ${logfile} > ${newpdf_list}
        # grep - oP "Removing .* paper \K.*" ${logfile} > ${removedpdf_list}

    # Obtain list of corpus and papers
    corpus_pdf_dict = dict()  # {corpus: list of pdf files of the corpus}
    pdf_corpus_list = [d for d in os.listdir(PDF_DIR) if os.path.isdir(os.path.join(PDF_DIR, d))]
    for corpus in pdf_corpus_list:
        corpus_paper_list = [d for d in os.listdir(PDF_DIR, corpus) if os.path.isdir(os.path.join(PDF_DIR, corpus, d))]
        corpus_pdf_dict[corpus] = corpus_paper_list
        for corpus_paper in corpus_paper:
            newpdf_list_fp.write("{}/{}\n".format(corpus, corpus_paper))


    #################################################################################
    #####                      2. GENERATE TPCAS-1                              #####
    #################################################################################

    if 'cas1' not in excluded_steps:
        print("Generating CAS1 files...")

        # 2.1 PDF FILES
        # obtain all the folder names in PDF_DIR then create tpcas1 folders for every corpus
        # folders correspond to corpus
        if not os.path.isdir(CAS1_DIR):
            os.mkdir(CAS1_DIR)

        for folder in [d for d in os.listdir(PDF_DIR) if os.path.isdir(os.path.join(PDF_DIR, d))]:
            if not os.path.isdir(os.path.join(CAS1_DIR, folder)):
                os.mkdir(os.path.join(CAS1_DIR, folder))

        generate_tpcas1()


        # 2.2 XML FILES

        # remove old versions
        # awk -F"/" '{print $NF}' ${newxml_local_list} | xargs -I {} rm -rf "${CAS1_DIR}/PMCOA/{}"
        #
        # mkdir -p ${CAS1_DIR}/PMCOA
        # cd ${CAS1_DIR}
        # num_papers_to_process_together=$(python3 -c "from math import ceil; print(ceil($(wc -l ${newxml_local_list} | awk '{print $1}') / ${N_PROC}))")
        # n_lines_to_tail=$(wc -l ${newxml_local_list} | awk '{print $1}')
        # for ((i=1; i<=${N_PROC}; i++))
        #     do
        # awk 'BEGIN{FS="/"}{print $NF}' ${newxml_local_list} | tail -n ${n_lines_to_tail} | head -n ${num_papers_to_process_together} > /tmp/tmplist_$i.txt
        # articles2cas -i "${XML_DIR}" -l /tmp/tmplist_$i.txt -t 2 -o PMCOA -p > logfile_$i.log &
        # n_lines_to_tail=$(($n_lines_to_tail - $num_papers_to_process_together))
        # done
        # wait
        # rm /tmp/tmplist_*.txt
        # rm logfile_*.log
        #
        # # 2.3 add images to tpcas directory and gzip
        #
        # # 2.3.1 xml
        # cat ${newxml_local_list} | awk 'BEGIN{FS="/"}{print $NF}' | xargs -n1 -P ${N_PROC} -I {} sh -c 'dirname=$(echo "{}"); rm -rf "$0/PMCOA/${dirname}/images";  ln -fs "$1/${dirname}/images" "$0/PMCOA/${dirname}/images"; find -L "$0/PMCOA/${dirname}" -name "*.tpcas" | xargs -I [] gzip -f "[]"' ${CAS1_DIR} ${XML_DIR}
        # # 2.3.2 pdf
        # cat ${newpdf_list} | xargs -n1 -P ${N_PROC} -I {} echo "{}" | awk 'BEGIN{FS="/"}{print $(NF-2)"/"$(NF-1)"/"$NF}' | sed 's/\.pdf/\.tpcas/g' | xargs -I [] gzip -f "[]"
        # fi

        ## generate tpcas-1 for unchanged pdfs


    #################################################################################
    #####                     3. GENERATE CAS-2                                 #####
    #################################################################################

    if 'cas2' not in excluded_steps:
        print("Generating CAS2 files ...")

    # 3.1 COPY FILES TO TMP DIR
    # 3.1.1 xml - subdirs are processed in parallel
#     mkdir - p ${TMP_DIR} / tpcas - 1 / xml
#     i = 1
#     subdir_idx = 1
#     num_papers_to_process_together =$(python3 - c
#                                       "from math import ceil; print(ceil($(wc -l ${newxml_local_list} | awk '{print $1}') / ${N_PROC}))")
#     mkdir - p ${TMP_DIR} / tpcas - 1 / xml / subdir_1
#     cat ${newxml_local_list} |
#     while read line
#     do
#     if [["$i" - gt "$num_papers_to_process_together"]]
#         then
#     i = 0
#     subdir_idx =$((subdir_idx + 1))
#     mkdir - p ${TMP_DIR} / tpcas - 1 / xml / subdir_${subdir_idx}
# fi
# dirname =$(echo ${line} | awk 'BEGIN{FS="/"}{print $NF}')
# find - L
# "${CAS1_DIR}/PMCOA/${dirname}" - name *.tpcas.gz | xargs - I
# {}
# cp
# "{}" "${TMP_DIR}/tpcas-1/xml/subdir_${subdir_idx}/${dirname}.tpcas.gz"
# i =$((i + 1))
# done

        # 3.1.2 pdf
        os.chdir(CAS1_DIR)
        for folder in [d for d in os.listdir(CAS1_DIR) if os.path.isdir(os.path.join(CAS1_DIR, d))]:
            os.makedirs(os.path.join(TMP_DIR, 'tpcas-1', folder))

        corpus_list = [d for d in os.listdir(CAS1_DIR) if os.path.isdir(os.path.join(CAS1_DIR, d))]
        for corpus in corpus_list:
            corpus_path = os.path.join(CAS1_DIR, corpus)
            for tpcas_id in [d for d in os.listdir(corpus_path) if os.path.isfile(os.path.join(corpus_path, d))]:
                shutil.copy(os.path.join(corpus_path, tpcas_id, tpcas_id + '.tpcas'),
                            os.path.join(TMP_DIR, 'tpcas-1', corpus))

        # 3.2 APPLY UIMA ANALYSIS

        # remove old versions
        # awk - F"/" '{print $NF}' ${newxml_local_list} | xargs - I
        # {}
        # rm - rf
        # "${CAS2_DIR}/PMCOA/{}"
        #
        # for subdir in $(ls ${TMP_DIR} / tpcas-1 / xml)
        # do
        # runAECpp / usr / local / uima_descriptors / TpLexiconAnnotatorFromPg.xml - xmi ${TMP_DIR} / tpcas - 1 / xml /${
        # subdir} ${TMP_DIR} / tpcas - 2 / xml &
        # done
        # wait

        # UIMA analysis for pdf files
        for corpus in corpus_list:
            os.system("runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi ")

        for folder in * /; do
        runAECpp / usr / local / uima_descriptors / TpLexiconAnnotatorFromPg.xml - xmi
        "${TMP_DIR}/tpcas-1/${folder}" "${TMP_DIR}/tpcas-2/${folder}"
        done

# 3.3 COMPRESS THE RESULTS
find - L ${TMP_DIR} / tpcas - 2 - name *.tpcas - print0 | xargs - 0 - n
1 - P ${N_PROC}
gzip

# 3.4 COPY TPCAS1 to TPCAS2 DIRS AND REPLACE FILES WITH NEW ONES
mkdir - p
"${CAS2_DIR}/PMCOA"
for folder in * /; do
mkdir - p
"${CAS2_DIR}/${folder}"
done

# 3.4.1 xml
cat ${newxml_local_list} |
while read line
do
dirname =$(echo ${line} | awk 'BEGIN{FS="/"}{print $NF}')
if [[-d "${CAS1_DIR}/PMCOA/${dirname}"]]
    then
tpcas_file_name =$(ls ${CAS1_DIR} / PMCOA / ${dirname} / *.tpcas.gz | head -n1 | awk 'BEGIN{FS="/"}{print $NF}')
mkdir - p
"${CAS2_DIR}/PMCOA/${dirname}"
if [[-e "${CAS2_DIR}/PMCOA/${dirname}/images"]]
    then
rm
"${CAS2_DIR}/PMCOA/${dirname}/images"
fi
ln - s
"${CAS1_DIR}/PMCOA/${dirname}/images" "${CAS2_DIR}/PMCOA/${dirname}/images"
cp ${TMP_DIR} / tpcas - 2 / xml /${dirname}.tpcas.gz
"${CAS2_DIR}/PMCOA/${dirname}/${tpcas_file_name}"
fi
done

# 3.4.2 pdf

cat ${newpdf_list} | awk - F"/" '{print $(NF-2)"/"$(NF-1)}' |
while read line
do
dir_name =$(echo ${line} | awk -F"/" '{print $(NF)}')
corpus_name =$(echo ${line} | awk -F"/" '{print $(NF-1)}')
tpcas_file =$(echo "${CAS1_DIR}/${line}/${dir_name}.tpcas.gz")
mkdir - p
"${CAS2_DIR}/${corpus_name}/"${dir_name}
ln - s
"${CAS1_DIR}/${corpus_name}/${dir_name}/images" "${CAS2_DIR}/${corpus_name}/${dir_name}/images"
cp
"${TMP_DIR}/tpcas-2/${line}.tpcas.gz" "${CAS2_DIR}/${line}/${dir_name}.tpcas.gz"
done
fi


    logfile_fp.close()
    newpdf_list_fp.close()
    removedpdf_list_fp.close()
    newxml_list_fp.close()
    newxml_local_list_fp.close()
    diffxml_list_fp.close()