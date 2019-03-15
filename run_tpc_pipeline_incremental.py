import os
import argparse
import shutil
import tempfile
import math
import multiprocessing
import subprocess
import gzip

from getpdfs.getpdfs import download_pdfs
from getbib.download_abstract import get_abstracts
from getbib.make_bib import create_bib
import pdf2text


default_config = {
    "PDF_DIR": "/data/textpresso/raw_files/pdf",
    "XML_DIR": "/data/textpresso/raw_files/xml",
    "TXT_DIR": "/data/textpresso/raw_files/txt",
    "CAS1_DIR": "/data/textpresso/tpcas-1",
    "CAS2_DIR": "/data/textpresso/tpcas-2",
    "TMP_DIR": "/data/textpresso/tmp",
    "FTP_MNTPNT": "/mnt/pmc_ftp",
    "INDEX_DIR": "/data/textpresso/luceneindex",
    "N_PROC": 1,
    "EXCLUDE_STEPS": ""
}

PAPERS_PER_SUBINDEX = 1000000


def set_argument_parser(config):
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pdf-dir", action='store', default='',
                        help="directory where raw pdf files will be stored")
    parser.add_argument("-x", "--xml-dir", action='store', default='',
                        help="directory where raw xml files will be stored")
    parser.add_argument("-txt", "--txt-dir", action='store', default='',
                        help="directory where raw txt files will be stored")
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
    if args.pdf_dir:
        config["PDF_DIR"] = args.pdf_dir
    if args.xml_dir:
        config["XML_DIR"] = args.xml_dir
    if args.txt_dir:
        config["TXT_DIR"] = args.txt_dir
    if args.cas1_dir:
        config["CAS1_DIR"] = args.cas1_dir
    if args.cas2_dir:
        config["CAS2_DIR"] = args.cas2_dir
    if args.tmp_dir:
        config["TMP_DIR"] = args.tmp_dir
    if args.ftp_dir:
        config["FTP_MNTPNT"] = args.ftp_dir
    if args.index_dir:
        config["INDEX_DIR"] = args.index_dir
    if args.num_proc:
        config["N_PROC"] = int(args.num_proc)
    if args.exclude_step:
        config["EXCLUDE_STEPS"] = args.exclude_step


def cas1_worker(tmp_file_idx, corpus, input_dir, file_format):
    """
    Worker to be used for processing pdf/txt/xml to tpcas file with multiprocessing
    :param tmp_file_idx: idx of the tmp_file to read the ids from
    :param corpus: name of the corpus
    :param input_dir: PDF_DIR, XML_DIR, or TXT_DIR
    :param file_format: 1 if PDF, 2 if XML, 3 if TXT
    """
    corpus = '\ '.join(corpus.strip().split(" "))
    input_folder = os.path.join(input_dir, corpus) + '/'
    output_folder = corpus + '/'
    dirlist_file = "/tmp/tmplist_{}.txt".format(tmp_file_idx)
    command = 'articles2cas -i {} -l {} -o {} -t {} -p'.format(input_folder, dirlist_file, output_folder, file_format)
    os.system(command)


def cas2_worker(corpus_list, input_path, output_path):
    for corpus in corpus_list:
        corpus = '\ '.join(corpus.strip().split(" "))
        command = "runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi {} {}".format(os.path.join(input_path, corpus),
                                                                                                        os.path.join(output_path, corpus))
        os.system(command)


def gzip_tpcas_worker(file_list, path, type):
    """
    Worker to be used for compressing .tpcas files
    :param file_list: list of files to compress - file_id for tpcas1, file_id.tpcas for tpcas2
    :param path: path to the corpus of the target files to be compressed
    :param type: 1 if cas1, 2 if cas2
    """
    assert type == 1 or type == 2
    for file in file_list:
        if type == 1:
            tpcas_file = os.path.join(path, file, file + '.tpcas')
        else:  # if type == 2
            tpcas_file = os.path.join(path, file)
        if tpcas_file.endswith('.tpcas') and os.path.isfile(tpcas_file):
            subprocess.check_call(['gzip', tpcas_file])


def gunzip_worker(zipped_file_list, path):
    for filename in zipped_file_list:
        tpcas_file = os.path.join(path, filename)
        if os.path.isfile(tpcas_file):
            subprocess.check_call(['gunzip', tpcas_file])


def pdf2txt_worker(input_path, output_path, file_id_list):
    """
    Converts pdf file to text file
    :param input_path: path to pdf corpus directory
    :param file_id_list: list of ids of files to process
    """
    for file_id in file_id_list:
        pdf_file = os.path.join(input_path, file_id, file_id + '.pdf')
        text = pdf2text.get_fulltext_from_pdfs_from_file(pdf_file)
        if not os.path.isdir(os.path.join(output_path, file_id)):
            os.mkdir(os.path.join(output_path, file_id))
        with open(os.path.join(output_path, file_id, file_id + ".txt"), 'w') as fpout:
            fpout.write(text)


def generate_tpcas1(input_dir, file_format, n_proc):
    """
    Generates tpcas1 files
    :param input_dir: PDF_DIR, XML_DIR, or TXT_DIR
    :param file_format: 1 if PDF, 2 if XML, 3 if TXT
    :param n_proc: number of processes to run in parallel
    """
    os.chdir(CAS1_DIR)
    print("Using {} processes".format(n_proc))
    for corpus in [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]:
        print("processing {}".format(corpus))
        corpus_file_list = os.listdir(os.path.join(input_dir, corpus))
        n_pdf_per_process = [math.floor(len(corpus_file_list) / n_proc)] * n_proc
        for i in range(len(corpus_file_list) % n_proc):
            n_pdf_per_process[i] += 1

        # split files i.e. allocate files to each cpu for multiprocessing
        # TODO: skip ids of existing files
        curr_idx = 0
        cas1_mp_args = list()
        for proc_idx in range(n_proc):
            with open('/tmp/tmplist_{}.txt'.format(proc_idx), 'w') as fpout:
                for filename in corpus_file_list[curr_idx:curr_idx + n_pdf_per_process[proc_idx]]:
                    fpout.write(filename + '\n')
            cas1_mp_args.append((proc_idx, corpus, input_dir, file_format))
            curr_idx += n_pdf_per_process[proc_idx]

        # execute cas1_worker in parallel
        pool = multiprocessing.Pool(processes=n_proc)
        pool.starmap(cas1_worker, cas1_mp_args)
        pool.close()
        pool.join()

        print("{} cas1 complete".format(corpus))
        for proc_idx in range(n_proc):
            os.remove("/tmp/tmplist_{}.txt".format(proc_idx))


def generate_tpcas2(corpus_list, n_proc, input_dir, output_dir):
    n_corpus_per_process = [math.floor(len(corpus_list) / n_proc)] * n_proc
    for i in range(len(corpus_list) % n_proc):
        n_corpus_per_process[i] += 1

    # split corpus i.e. allocate corpus to each cpu for multiprocessing
    curr_idx = 0
    cas2_mp_args = list()
    for proc_idx in range(n_proc):
        cas2_mp_args.append((corpus_list[curr_idx:curr_idx + n_corpus_per_process[proc_idx]], input_dir, output_dir))
        curr_idx += n_corpus_per_process[proc_idx]
    pool = multiprocessing.Pool(processes=n_proc)
    pool.starmap(cas2_worker, cas2_mp_args)
    pool.close()
    pool.join()


def compress_tpcas(input_dir, n_proc, type):
    """
    Compresses .tpcas files in input_dir in parallel using n_proc cpus
    :param input_dir: for type 1 - directory of the corpus
                      for type 2 - directory where .tpcas files are located at
    :param n_proc: number of processes to use
    :param type: 1 if cas1, 2 if cas2
    """
    assert type == 1 or type == 2
    for corpus in [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]:
        tpcas_file_list = os.listdir(os.path.join(input_dir, corpus))
        # obtain the number of files assigned to each process
        n_tpcas_per_process = [math.floor(len(tpcas_file_list) / n_proc)] * n_proc
        for i in range(len(tpcas_file_list) % n_proc):
            n_tpcas_per_process[i] += 1

        # set up arguments to be used for each worker in multi-processing
        curr_idx = 0
        gzip_mp_args = list()
        for proc_idx in range(n_proc):
            gzip_mp_args.append((tpcas_file_list[curr_idx:curr_idx + n_tpcas_per_process[proc_idx]],
                                 os.path.join(input_dir, corpus), type))
            curr_idx += n_tpcas_per_process[proc_idx]

        # run gzip_tpcas_worker on multiprocess
        pool = multiprocessing.Pool(processes=n_proc)
        pool.starmap(gzip_tpcas_worker, gzip_mp_args)
        pool.close()
        pool.join()


if __name__ == '__main__':
    set_argument_parser(default_config)
    PDF_DIR = default_config["PDF_DIR"]
    XML_DIR = default_config["XML_DIR"]
    TXT_DIR = default_config["TXT_DIR"]
    CAS1_DIR = default_config["CAS1_DIR"]
    CAS2_DIR = default_config["CAS2_DIR"]
    TMP_DIR = default_config["TMP_DIR"]
    FTP_MNTPNT = default_config["FTP_MNTPNT"]
    INDEX_DIR = default_config["INDEX_DIR"]
    N_PROC = default_config["N_PROC"]
    EXCLUDE_STEPS = default_config["EXCLUDE_STEPS"]

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
    else:
        print("skipping download_xml")

    if 'download_pdf' not in excluded_steps:
        print("Downloading pdf papers")
        if not os.path.isdir(PDF_DIR):
            os.mkdir(PDF_DIR)
        download_pdfs(False, logfile_fp.name, "INFO", PDF_DIR)

        # logging into newpdf_list and removedpdf_list does not seem necessary
        # grep - oP "Downloading paper: .* to \K.*\.pdf" ${logfile} > ${newpdf_list}
        # grep - oP "Removing .* paper \K.*" ${logfile} > ${removedpdf_list}
    else:
        print("skipping download_pdf")

    # Obtain list of corpus and papers
    # corpus_pdf_dict = dict()  # {corpus: list of pdf files of the corpus}
    # pdf_corpus_list = [d for d in os.listdir(PDF_DIR) if os.path.isdir(os.path.join(PDF_DIR, d))]
    # print(pdf_corpus_list)
    # for corpus in pdf_corpus_list:
    #     corpus_paper_list = [d for d in os.listdir(os.path.join(PDF_DIR, corpus))
    #                          if os.path.isdir(os.path.join(PDF_DIR, corpus, d))]
    #     corpus_pdf_dict[corpus] = corpus_paper_list
    #     for corpus_paper in corpus_paper:
    #         newpdf_list_fp.write("{}/{}\n".format(corpus, corpus_paper))


    #################################################################################
    #####                      2. GENERATE TPCAS-1                              #####
    #################################################################################

    if 'cas1' not in excluded_steps:
        print("Generating CAS1 files...")

        # 2.1 Generate TPCAS-1 files from PDF files

        # obtain all the folder names in PDF_DIR then create tpcas1 folders for every corpus
        # folders correspond to corpus
        if not os.path.isdir(CAS1_DIR):
            os.mkdir(CAS1_DIR)

        for folder in [d for d in os.listdir(PDF_DIR) if os.path.isdir(os.path.join(PDF_DIR, d))]:
            if not os.path.isdir(os.path.join(CAS1_DIR, folder)):
                os.mkdir(os.path.join(CAS1_DIR, folder))

        generate_tpcas1(PDF_DIR, 1, N_PROC)
        compress_tpcas(CAS1_DIR, N_PROC, 1)

        # 2.1.1 Copy .tpcas.gz files to TMP_DIR

        # create directories for each corpus in TMP_DIR
        for folder in [d for d in os.listdir(CAS1_DIR) if os.path.isdir(os.path.join(CAS1_DIR, d))]:
            os.makedirs(os.path.join(TMP_DIR, 'tpcas-1', folder))

        # copy .tpcas.gz files to TMP_DIR and keep track of missing files
        missing_files_dict = dict()  # {corpus: list of ids of missing .tpcas files}
        corpus_list = [d for d in os.listdir(CAS1_DIR) if os.path.isdir(os.path.join(CAS1_DIR, d))]
        for corpus in corpus_list:
            missing_files_dict[corpus] = list()
            corpus_path = os.path.join(CAS1_DIR, corpus)
            for tpcas_id in [d for d in os.listdir(corpus_path) if os.path.isdir(os.path.join(corpus_path, d))]:
                cas_file = os.path.join(corpus_path, tpcas_id, tpcas_id + '.tpcas.gz')
                if os.path.isfile(cas_file):
                    shutil.copy(cas_file, os.path.join(TMP_DIR, 'tpcas-1', corpus))
                else:
                    missing_files_dict[corpus].append(tpcas_id)

        # 2.1.2 Convert PDF to TXT file for files of missing tpcas and generate tpcas-1

        print(missing_files_dict)
        print("Number of failures")
        for corpus in missing_files_dict:
            print("{}: {}".format(corpus, len(missing_files_dict[corpus])))

        # convert pdf files to txt files
        if not os.path.isdir(TXT_DIR):
            os.mkdir(TXT_DIR)
        for corpus in missing_files_dict:
            if len(missing_files_dict[corpus]) == 0:
                continue
            if not os.path.isdir(os.path.join(TXT_DIR, corpus)):
                os.mkdir(os.path.join(TXT_DIR, corpus))
            if len(missing_files_dict) > N_PROC:  # multiprocess
                pdf2txt_mp_args = list()
                n_pdf_per_process = [math.floor(len(missing_files_dict[corpus]) / N_PROC)] * N_PROC
                for i in range(len(missing_files_dict[corpus]) % N_PROC):
                    n_pdf_per_process[i] += 1

                curr_idx = 0
                for proc_idx in range(N_PROC):
                    pdf2txt_mp_args.append((os.path.join(PDF_DIR, corpus), os.path.join(TXT_DIR, corpus),
                                            missing_files_dict[corpus][curr_idx:curr_idx + n_pdf_per_process[proc_idx]]))
                    curr_idx += n_pdf_per_process[proc_idx]
                pool = multiprocessing.Pool(processes=n_proc)
                pool.starmap(pdf2text_worker, pdf2txt_mp_args)
                pool.close()
                pool.join()
            else:
                pdf2txt_worker(os.path.join(PDF_DIR, corpus), os.path.join(TXT_DIR, corpus),
                               missing_files_dict[corpus])

        # convert txt files to cas1 files
        # assume there are more txt files than N_PROC
        generate_tpcas1(TXT_DIR, 3, N_PROC)
        compress_tpcas(CAS1_DIR, N_PROC, 1)

        # move newly converted cas1 to tmp files
        for corpus in missing_files_dict:
            if len(missing_files_dict[corpus]) == 0:
                continue
            for file_id in missing_files_dict[corpus]:
                cas_file = os.path.join(CAS1_DIR, corpus, file_id, file_id + '.tpcas.gz')
                if os.path.isfile(cas_file):
                    shutil.copy(cas_file, os.path.join(TMP_DIR, 'tpcas-1', corpus))

        # 2.2 XML FILES

        # remove old versions
        # awk -F"/" '{print $NF}' ${newxml_local_list} | xargs -I {} rm -rf "${CAS1_DIR}/PMCOA/{}"
        #
        # mkdir -p ${CAS1_DIR}/PMCOA
        # cd ${CAS1_DIR}
        # num_papers_to_process_together=$(python3 -c "from math import ceil; print(ceil($(wc -l ${newxml_local_list} | awk '{print $1}') / ${N_PROC}))")
        # n_lines_to_tail=$(wc -l ${newxml_local_list} | awk '{print $1}')
        # for ((i=1; i<=${N_PROC}; i++))
        # do
        #   awk 'BEGIN{FS="/"}{print $NF}' ${newxml_local_list} | tail -n ${n_lines_to_tail} | head -n ${num_papers_to_process_together} > /tmp/tmplist_$i.txt
        #   articles2cas -i "${XML_DIR}" -l /tmp/tmplist_$i.txt -t 2 -o PMCOA -p > logfile_$i.log &
        #   n_lines_to_tail=$(($n_lines_to_tail - $num_papers_to_process_together))
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

        # 3.1 COPY FILES TO TMP DIR
        # 3.1.1 xml - subdirs are processed in parallel
        # mkdir - p ${TMP_DIR}/tpcas-1/xml
        # i = 1
        # subdir_idx = 1
        # num_papers_to_process_together =$(python3 - c "from math import ceil; print(ceil($(wc -l ${newxml_local_list} | awk '{print $1}') / ${N_PROC}))")
        # mkdir - p ${TMP_DIR} / tpcas - 1 / xml / subdir_1
        # cat ${newxml_local_list} | while read line
        # do
        #     if [["$i" - gt "$num_papers_to_process_together"]]
        #     then
        #       i = 0
        #       subdir_idx =$((subdir_idx + 1))
        #       mkdir - p ${TMP_DIR}/tpcas-1/xml/subdir_${subdir_idx}
        #     fi
        #     dirname =$(echo ${line} | awk 'BEGIN{FS="/"}{print $NF}')
        #     find - L "${CAS1_DIR}/PMCOA/${dirname}" - name *.tpcas.gz | xargs - I {} cp "{}" "${TMP_DIR}/tpcas-1/xml/subdir_${subdir_idx}/${dirname}.tpcas.gz"
        #     i =$((i + 1))
        # done

    else:
        print("skipping cas1...")

    # TODO
    # take care of situations when the folder and zip files already exist and etc...


    #################################################################################
    #####                     3. GENERATE CAS-2                                 #####
    #################################################################################

    if 'cas2' not in excluded_steps:
        print("Generating CAS2 files ...")

        # 3.1 APPLY UIMA ANALYSIS

        # create directory structure of tmp/tpcas-2 if it does not exist
        os.chdir(CAS1_DIR)
        for folder in [d for d in os.listdir(CAS1_DIR) if os.path.isdir(os.path.join(CAS1_DIR, d))]:
            if not os.path.isdir(os.path.join(TMP_DIR, 'tpcas-2', folder)):
                os.makedirs(os.path.join(TMP_DIR, 'tpcas-2', folder))

        # decompress all cas files in tmp/tpcas-1 before running UIMA analysis
        for corpus in [d for d in os.listdir(os.path.join(TMP_DIR, 'tpcas-1'))
                       if os.path.isdir(os.path.join(TMP_DIR, 'tpcas-1', d))]:
            cas1_zipped_list = [f for f in os.listdir(os.path.join(TMP_DIR, 'tpcas-1', corpus))
                                if f[-3:] == '.gz']
            gunzip_mp_args = list()
            n_files_per_process = [math.floor(len(cas1_zipped_list) / N_PROC)] * N_PROC
            for i in range(len(cas1_zipped_list) % N_PROC):
                n_files_per_process[i] += 1

            curr_idx = 0
            for proc_idx in range(N_PROC):
                gunzip_mp_args.append((cas1_zipped_list[curr_idx:curr_idx + n_files_per_process[proc_idx]],
                                       os.path.join(TMP_DIR, 'tpcas-1', corpus)))
                curr_idx += n_files_per_process[proc_idx]
            pool = multiprocessing.Pool(processes=N_PROC)
            pool.starmap(gunzip_worker, gunzip_mp_args)
            pool.close()
            pool.join()
        print("Successfully unzipped .tpcas.gz files")


        # 3.2 APPLY UIMA ANALYSIS

        # remove old versions
        # awk - F"/" '{print $NF}' ${newxml_local_list} | xargs - I {} rm - rf "${CAS2_DIR}/PMCOA/{}"

        # for subdir in $(ls ${TMP_DIR} / tpcas-1 / xml)
        # do
        # runAECpp / usr / local / uima_descriptors / TpLexiconAnnotatorFromPg.xml - xmi ${TMP_DIR} / tpcas - 1 / xml /${subdir} ${TMP_DIR} / tpcas - 2 / xml &
        # done
        # wait

        # run UIMA analysis on pdf files
        print("Running UIMA analysis for pdf...")
        corpus_list = [d for d in os.listdir(os.path.join(TMP_DIR, 'tpcas-1'))
                       if os.path.isdir(os.path.join(TMP_DIR, 'tpcas-1', d))]
        if len(corpus_list) < N_PROC:
            n_proc = len(corpus_list)
        else:
            n_proc = N_PROC

        # generate_tpcas2(corpus_list, len(corpus_list), os.path.join(TMP_DIR, "tpcas-1"),
        #                 os.path.join(TMP_DIR, "tpcas-2"))
        # compress_tpcas(os.path.join(TMP_DIR, "tpcas-2"), N_PROC, 2)

        # 3.3 Setup TPCAS-2 DIRS

        # create TPCAS-2 directory and its subdirectories
        if not os.path.isdir(CAS2_DIR):
            os.mkdir(CAS2_DIR)
        if not os.path.isdir(os.path.join(CAS2_DIR, "PMCOA")):
            os.mkdir(os.path.join(CAS2_DIR, "PMCOA"))
        for corpus in [d for d in os.listdir(os.path.join(TMP_DIR, "tpcas-2"))
                       if os.path.isdir(os.path.join(TMP_DIR, "tpcas-2", d))]:
            if not os.path.isdir(os.path.join(CAS2_DIR, corpus)):
                os.mkdir(os.path.join(CAS2_DIR, corpus))

        # 3.3.1 xml
        # cat ${newxml_local_list} | while read line
        # do
        # dirname =$(echo ${line} | awk 'BEGIN{FS="/"}{print $NF}')
        # if [[-d "${CAS1_DIR}/PMCOA/${dirname}"]]
        #     then
        # tpcas_file_name =$(ls ${CAS1_DIR} / PMCOA / ${dirname} / *.tpcas.gz | head -n1 | awk 'BEGIN{FS="/"}{print $NF}')
        # mkdir - p "${CAS2_DIR}/PMCOA/${dirname}"
        # if [[-e "${CAS2_DIR}/PMCOA/${dirname}/images"]]
        #     then
        # rm "${CAS2_DIR}/PMCOA/${dirname}/images"
        # fi
        # ln - s
        # "${CAS1_DIR}/PMCOA/${dirname}/images" "${CAS2_DIR}/PMCOA/${dirname}/images"
        # cp ${TMP_DIR} / tpcas - 2 / xml /${dirname}.tpcas.gz
        # "${CAS2_DIR}/PMCOA/${dirname}/${tpcas_file_name}"
        # fi
        # done

        # 3.3.2 pdf
        for corpus in [d for d in os.listdir(PDF_DIR) if os.path.isdir(os.path.join(PDF_DIR, d))]:
            for file_id in [d for d in os.listdir(os.path.join(CAS1_DIR, corpus))
                            if os.path.isdir(os.path.join(CAS1_DIR, corpus, d))]:
                os.makedirs(os.path.join(CAS2_DIR, corpus, file_id), exist_ok=True)
                # create symlink to images folder of CAS1
                if not os.path.islink(os.path.join(CAS2_DIR, corpus, file_id, "images")):
                    os.symlink(os.path.join(CAS1_DIR, corpus, file_id, "images"),
                               os.path.join(CAS2_DIR, corpus, file_id, "images"))
                # copy .tpcas.gz files to CAS2_DIR
                if not os.path.isfile(os.path.join(CAS2_DIR, corpus, file_id, file_id + ".tpcas.gz")):
                    shutil.copy(os.path.join(TMP_DIR, "tpcas-2", corpus, file_id + ".tpcas.gz"),
                                os.path.join(CAS2_DIR, corpus, file_id, file_id + ".tpcas.gz"))

    else:
        print("skipping cas2...")

    #################################################################################
    #####                     4. GENERATE BIB FILES                             #####
    #################################################################################

    if 'bib' not in excluded_steps:
        # 4.1 download bib info for pdfs
        print("Donwloading bib info for pdf files...")
        os.makedirs("/usr/local/textpresso/celegans_bib", exist_ok=True)

        # download bibs for C. elegans
        subprocess.check_call(['download_pdfinfo.pl', '/usr/local/textpresso/celegans_bib/'])
        subprocess.check_call(['extract_pdfbibinfo.pl', '/usr/local/textpresso/celegans_bib/'])

        print("Generating bib files...")
        os.chdir(CAS2_DIR)

        def gen_bib_worker(path):
            path = '\ '.join(path.strip().split(" "))
            os.system("getbib {}".format(path))
            print("completed .bib generation for {}".format(path))

        bib_mp_args = [os.path.join(CAS2_DIR, "C. elegans"), os.path.join(CAS2_DIR, "C. elegans Supplementals")]
        print(bib_mp_args)
        pool = multiprocessing.Pool(processes=2)
        pool.map(gen_bib_worker, bib_mp_args)
        pool.close()
        pool.join()

        # generate bib for xenbase or other corpora
        # the paper ids in the corpora directory needs to be the pmid
        get_abstracts(os.path.join(CAS2_DIR, "xenbase"), 300)
        create_bib(os.path.join(CAS2_DIR, "xenbase"), "/home/daniel/xenbase_info")


    else:
        print("Skipping bib...")

#
#     # 4.2 xml
#     cas_dir_to_process = "${CAS2_DIR}/PMCOA"
#     if [[-d "${TMP_DIR}/tpcas-2/xml"]]
#         then
#     cas_dir_to_process = "${TMP_DIR}/tpcas-2/xml"
# if [[ $(ls ${cas_dir_to_process} | wc -l) != "0"]]
# then
# tempdir =$(mktemp - d)
# num_papers_to_process_together =$(python3 - c
#                                   "from math import ceil; print(ceil($(ls "${cas_dir_to_process}" | wc -l) / ${N_PROC}))")
# ls
# "${cas_dir_to_process}" | sed
# 's/.tpcas.gz//g' | split - l ${num_papers_to_process_together} - ${tempdir} / file_to_process -
# for file_list in $(ls ${tempdir})
# do
# getbib4nxml
# "${CAS2_DIR}/PMCOA" - f ${tempdir} /${file_list} &
# done
# wait
# rm - rf ${tempdir}
# fi
# fi


    logfile_fp.close()
    newpdf_list_fp.close()
    removedpdf_list_fp.close()
    newxml_list_fp.close()
    newxml_local_list_fp.close()
    diffxml_list_fp.close()