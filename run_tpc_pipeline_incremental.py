import os
import argparse
import shutil
import tempfile
import math
import multiprocessing
import subprocess
import gzip
import re
import time

from getpdfs.getpdfs import download_pdfs
from getxmls.getxmls import get_newxml_list, download_xmls
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
    "EXCLUDE_STEPS": "",
    "TEST": False,
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
    parser.add_argument("-test", "--test", action='store_true', default=False,
                        help="if True, run in test mode")
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
    if args.test:
        config["TEST"] = args.test


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


def cas1_xml_worker(tmp_file_idx, input_dir):
    dirlist_file = "/tmp/tmplist_{}.txt".format(tmp_file_idx)
    command = 'articles2cas -i {} -l {} -t 2 -o PMCOA -p'.format(input_dir, dirlist_file)
    os.system(command)


def cas2_worker(corpus_list, input_path, output_path):
    for corpus in corpus_list:
        corpus = '\ '.join(corpus.strip().split(" "))
        command = ("runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi "
                   "{} {}").format(os.path.join(input_path, corpus), os.path.join(output_path, corpus))
        os.system(command)


def cas2_xml_worker(subdir, input_path, output_path):
    command = ("runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi "
               "{} {}").format(os.path.join(input_path, subdir), output_path)
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
            subprocess.check_call(['gzip', '-f', tpcas_file])


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


def xml_bib_worker(input_file, output_path):
    os.system("getbib4nxml {} -f {}".format(output_path, input_file))


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


def generate_xml_tpcas1(input_dir, file_list_fp, n_proc):
    print("Using {} processes".format(n_proc))
    os.chdir(CAS1_DIR)
    file_list = list()
    file_list_fp.seek(0, 0)
    line = file_list_fp.readline()
    while line:
        file_list.append(line.strip())
        line = file_list_fp.readline()
    n_xml_per_process = [math.floor(len(file_list) / n_proc)] * n_proc
    for i in range(len(file_list) % n_proc):
        n_xml_per_process[i] += 1

    curr_idx = 0
    cas1_mp_args = list()
    for proc_idx in range(n_proc):
        with open('/tmp/tmplist_{}.txt'.format(proc_idx), 'w') as fpout:
            for file_id in file_list[curr_idx:curr_idx + n_xml_per_process[proc_idx]]:
                fpout.write(file_id.split('/')[-1] + '\n')
            cas1_mp_args.append((proc_idx, input_dir))
            curr_idx += n_xml_per_process[proc_idx]

    # execute cas1_xml_worker in parallel
    pool = multiprocessing.Pool(processes=n_proc)
    pool.starmap(cas1_xml_worker, cas1_mp_args)
    pool.close()
    pool.join()

    print("xml cas1 complete")
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


def generate_xml_tpcas2(n_proc, input_dir, output_dir):
    cas2_mp_args = list()
    for subdir in [d for d in os.listdir(input_dir)
                   if os.path.isdir(os.path.join(input_dir, d))]:
        cas2_mp_args.append((subdir, input_dir, output_dir))
    pool = multiprocessing.Pool(processes=n_proc)
    pool.starmap(cas2_xml_worker, cas2_mp_args)
    pool.close()
    poo.join()


def compress_tpcas(input_dir, n_proc, type, is_xml=False):
    """
    Compresses .tpcas files in input_dir in parallel using n_proc cpus
    :param input_dir: for type 1 - directory of the corpus
                      for type 2 - directory where .tpcas files are located at
    :param n_proc: number of processes to use
    :param type: 1 if cas1, 2 if cas2
    :param is_xml: True if compressing xml tpcas, False if not
    """
    assert type == 1 or type == 2
    for corpus in [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]:
        if is_xml and corpus != 'xml':
            continue
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
    TEST_MODE = default_config["TEST"]

    if 'LD_LIBRARY_PATH' in os.environ:
        os.environ['LD_LIBRARY_PATH'] = "{}:/usr/local/lib".format(os.environ['LD_LIBRARY_PATH'])
    else:
        os.environ['LD_LIBRARY_PATH'] = "/usr/local/lib"
    os.environ['PATH'] = "{}:/usr/local/bin".format(os.environ['PATH'])

    logfile_fp = tempfile.NamedTemporaryFile()
    removedpdf_list_fp = tempfile.NamedTemporaryFile()

    # for testing use actual files not temporary files
    if TEST_MODE:
        print("running in testing mode")
        # newxml_list_fp = open("/home/daniel/newxml_list.txt")
        newxml_list_file = "/home/daniel/newxml_list.txt"
        newxml_local_list_fp = open("/home/daniel/newxml_local_list.txt")
        diffxml_list_fp = open("/home/daniel/diffxml_list.txt")
    else:
        # newxml_list_fp = tempfile.NamedTemporaryFile()
        newxml_list_file = os.path.join(XML_DIR, "newxml_list.txt")
        newxml_local_list_fp = tempfile.NamedTemporaryFile()
        diffxml_list_fp = tempfile.NamedTemporaryFile()

    excluded_steps = EXCLUDE_STEPS.split(',')

    #################################################################################
    #####                      1. DOWNLOAD PAPERS                               #####
    #################################################################################

    # 1.1 Download XML files from PMCOA
    if 'download_xml' not in excluded_steps:
        print("Downloading xml papers ...")

        # 1.1.1 create directory for unclassified xml files
        os.makedirs(XML_DIR, exist_ok=True)
        os.makedirs(FTP_MNTPNT, exist_ok=True)

        # get_newxml_list(FTP_MNTPNT, newxml_list_file)

        # 1.1.4 calculate diff between existing files and files on PMCOA and download the new ones.
        # If there are no pre-existing files, download the full repository

        if os.path.isfile(os.path.join(XML_DIR, "current_filelist.txt")):
            # delete previous versions
            command = ("diff {} {}/current_filelist.txt | grep \"^<\" | "
                       "awk '{{print $4}}' | awk -F\"/\" '{{print $NF}}' | sed 's/.tar.gz//g' | "
                       "xargs -I {{}} rm -rf \"{}/{{}}\"").format(newxml_list_fp.name, XML_DIR, XML_DIR)
            os.system(command)
            # download diff files and update diffxml_list file
            command = ("diff {} {}/current_filelist.txt | grep \"^<\" | "
                       "awk '{{print $4}}' | awk -F\"/\" '{{print $(NF-2)\"/\"$(NF-1)\"/\"$NF}}' | "
                       "xargs -n 1 -P {} -I {{}} sh -c "
                       "'wget -qO- \"ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/{{}}\" | tar xfz - "
                       "--exclude=\"*.pdf\" --exclude=\"*.PDF\" --exclude=\"*.mp4\" --exclude=\"*.webm\" "
                       "--exclude=\"*.flv\" --exclude=\"*.avi\" --exclude=\"*.zip\" --exclude=\"*.mov\" "
                       "--exclude=\"*.csv\" --exclude=\"*.xls*\" --exclude=\"*.doc*\" --exclude=\"*.ppt*\" "
                       "--exclude=\"*.rar\" --exclude=\"*.txt\" --exclude=\"*.TXT\" --exclude=\"*.wmv\" "
                       "--exclude=\"*.DOC*\" -C '\"${XML_DIR}\"").format(newxml_list_fp.name, XML_DIR, N_PROC)
            os.system(command)
            command = ("diff {} {}/current_filelist.txt | grep \"^<\" | "
                       "sed 's/< //g' > {}").format(newxml_list_fp.name, XML_DIR, diffxml_list_fp.name)
            os.system(command)

        else:
            download_xmls(newxml_list_file, XML_DIR, N_PROC)

            # copy newxml_list to diffxml_list
            with open(newxml_list_file, 'r') as newxml_list_fp:
                line = newxml_list_fp.readline()
                while line:
                    diffxml_list_fp.write(line)
                    line = newxml_list_fp.readline

        """
        # remove empty files from diff list
        temp_diff_fp = tempfile.NamedTemporaryFile()
        command = ("awk '{{print $3}}' {} | awk -F\"/\" '{{print $NF}}' | sed 's/.tar.gz//g' | "
                   "xargs -I {{}} bash -c 'if [[ -d \"$0/{{}}\" ]]; then echo \"{{}}\"; fi' \"{}\" "
                   "> {}").format(diffxml_list_fp.name, XML_DIR, temp_diff_fp.name)
        os.system(command)
        diffxml_list_fp.close()
        diffxml_list_fp = tempfile.NamedTemporaryFile()
        temp_diff_fp.seek(0, 0)
        line = temp_diff_fp.readline()
        while line:
            diffxml_list_fp.write(line)
            line = temp_diff_fp.readline()
        temp_diff_fp.close()

        # save the current list
        with open(os.path.join(XML_DIR, "current_filelist.txt"), 'w') as fpout:
            newxml_list_fp.seek(0, 0)
            line = newxml_list_fp.readline()
            while line:
                fpout.write(line)
                line = newxml_list_fp.readline()

        # 1.1.5 save new xml local file list
        diffxml_list_fp.seek(0, 0)
        line = diffxml_list_fp.readline()
        while line:
            line = line.strip()
            newxml_local_list_fp.write(os.path.join(XML_DIR, line) + '\n')
            line = diffxml_list_fp.readline()
        """
        # 1.1.6 compress nxml and put images in a separate directory
        # command = ("cat {} | xargs -I {{}} -n1 -P {} sh -c 'gzip \"{{}}\"/*.nxml; "
        #            "mkdir \"{{}}\"/images; ls -d \"{{}}\"/* | grep -v .nxml | grep -v \"{{}}\"/images | "
        #            "xargs -I [] mv [] \"{{}}\"/images'").format(newxml_local_list_fp.name, N_PROC)
        # os.system(command)
    else:
        print("skipping download_xml")

    # 1.2 Download PDF files from tazendra
    if 'download_pdf' not in excluded_steps:
        print("Downloading pdf papers")
        os.makedirs(PDF_DIR, exist_ok=True)
        download_pdfs(False, logfile_fp.name, "INFO", PDF_DIR)

        # save the list of files to remove
        logfile_fp.seek(0, 0)
        removedpdf_list_fp.seek(0, 0)
        remove_pattern = 'Removing (deleted|invalid) paper (.*)'
        line = logfile_fp.readline()
        while line:
            line = line.decode('utf-8').strip()
            match = re.search(remove_pattern, line)
            if match:
                removedpdf_list_fp.write(match.gropu(2))
            line = logfile_fp.readline()
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
        os.makedirs(CAS1_DIR, exist_ok=True)

        for folder in [d for d in os.listdir(PDF_DIR) if os.path.isdir(os.path.join(PDF_DIR, d))]:
            if not os.path.isdir(os.path.join(CAS1_DIR, folder)):
                os.mkdir(os.path.join(CAS1_DIR, folder))

        generate_tpcas1(PDF_DIR, 1, N_PROC)
        compress_tpcas(CAS1_DIR, N_PROC, 1)

        # 2.1.1 Copy .tpcas.gz files to TMP_DIR

        # create directories for each corpus in TMP_DIR
        for folder in [d for d in os.listdir(CAS1_DIR) if os.path.isdir(os.path.join(CAS1_DIR, d))]:
            os.makedirs(os.path.join(TMP_DIR, 'tpcas-1', folder), exist_ok=True)

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
        os.makedirs(TXT_DIR, exist_ok=True)
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

        # 2.2 Generate TPCAS-1 from XML FILES

        # remove old versions
        newxml_local_list_fp.seek(0, 0)
        line = newxml_local_list_fp.readline()
        while line:
            line = line.strip()
            file_id = line.split('/')[-1]
            os.system("rm -rf {}/PMCOA/{}".format(CAS1_DIR, file_id))
            line = newxml_local_list_fp.readline()

        os.makedirs(os.path.join(CAS1_DIR, 'PMCOA'), exist_ok=True)
        generate_xml_tpcas1(XML_DIR, newxml_local_list_fp, N_PROC)
        # add images to tpcas directory and gzip
        # TODO: translate into Python and add multiprocessing
        command = ("cat {} | awk 'BEGIN{{FS=\"/\"}}{{print $NF}}' | "
                   "xargs -n1 -P {} -I {{}} sh -c 'dirname=$(echo \"{{}}\"); "
                   "rm -rf \"$0/PMCOA/${dirname}/images\";  ln -fs \"$1/${dirname}/images\" "
                   "\"$0/PMCOA/${dirname}/images\"; find -L \"$0/PMCOA/${dirname}\" -name \"*.tpcas\" | "
                   "xargs -I [] gzip -f \"[]\"' {} {}").format(newxml_local_list_fp.name, N_PROC, CAS1_DIR, XML_DIR)
        os.system(command)

        # 2.2.1 copy files to TMP_DIR
        os.makedirs(os.path.join(TMP_DIR, 'tpcas-1', 'xml'), exist_ok=True)

        # TODO: test parallel vs nonparallel for copying files
        dir_list = list()
        newxml_local_list_fp.seek(0, 0)
        line = newxml_local_list_fp.readline()
        while line:
            dir_list.append(line.strip().split("/")[-1])
            line = newxml_local_list_fp.readline()

        num_papers_to_process_together = int(math.ceil(len(dir_list) / N_PROC))
        i, subdir_idx = 1, 1
        os.makedirs(os.path.join(TMP_DIR, 'tpcas-1', 'xml', 'subdir_1'), exist_ok=True)
        for dirname in dir_list:
            if i > num_papers_to_process_together:
                i = 0
                subdir_idx += 1
                os.makedirs(os.path.join(TMP_DIR, 'tpcas-1', 'xml', 'subdir_{}'.format(subdir_idx)), exist_ok=True)
            shutil.copy(os.path.join(CAS1_DIR, 'PMCOA', dirname, dirname + ".tpcas.gz"),
                        os.path.join(TMP_DIR, "tpcas-1", "xml", "subdir_{}".format(subdir_idx), dirname + ".tpcas.gz"))
            i += 1
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
            os.makedirs(os.path.join(TMP_DIR, 'tpcas-2', folder), exist_ok=True)
        os.makedirs(os.path.join(TMP_DIR, 'tpcas-2', 'xml'), exist_ok=True)

        # decompress all pdf cas files in tmp/tpcas-1 before running UIMA analysis
        for corpus in [d for d in os.listdir(os.path.join(TMP_DIR, 'tpcas-1'))
                       if os.path.isdir(os.path.join(TMP_DIR, 'tpcas-1', d))]:
            if corpus == 'xml':
                continue
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

        # decompress all xml cas files in tmp/tpcas-1 before running UIMA analysis
        gunzip_mp_args = list()
        for subdir in [d for d in os.listdir(os.path.join(TMP_DIR, 'tpcas-1', 'xml'))
                       if os.path.isdir(os.path.join(TMP_DIR, 'tpcas-1', 'xml', d))]:
            gunzip_mp_args.append(([f for f in os.listdir(os.path.join(TMP_DIR, 'tpcas-1', 'xml', subdir))
                                    if os.path.isfile(os.path.join(TMP_DIR, 'tpcas-1', 'xml', subdir, f))
                                    and f.endswith('.tpcas.gz')],
                                   os.path.join(TMP_DIR, 'tpcas-1', xml, subdir)))
        pool = multiprocessing.Pool(processes=N_PROC)
        pool.starmap(gunzip_worker, gunzip_mp_args)
        pool.close()
        pool.join()
        print("Successfully unzipped .tpcas.gz files")

        # 3.2 APPLY UIMA ANALYSIS

        # run UIMA analysis on pdf files
        print("Running UIMA analysis for pdf...")
        corpus_list = [d for d in os.listdir(os.path.join(TMP_DIR, 'tpcas-1'))
                       if os.path.isdir(os.path.join(TMP_DIR, 'tpcas-1', d))]
        if len(corpus_list) < N_PROC:
            n_proc = len(corpus_list)
        else:
            n_proc = N_PROC

        generate_tpcas2(corpus_list, len(corpus_list), os.path.join(TMP_DIR, "tpcas-1"),
                        os.path.join(TMP_DIR, "tpcas-2"))
        compress_tpcas(os.path.join(TMP_DIR, "tpcas-2"), N_PROC, 2)

        # run UIMA analysis on xml files
        print("Running UIMA analysis for xml...")

        # remove old versions of xml
        newxml_local_list_fp.seek(0, 0)
        line = newxml_local_list_fp.readline()
        while line:
            os.system("rm -r {}".format(os.path.join(CAS2_DIR, 'PMCOA', line.strip().split('/')[-1])))
            line = newxml_local_list_fp.readline()

        generate_xml_tpcas2(N_PROC, os.path.join(TMP_DIR, 'tpcas-1', 'xml'),
                            os.path.join(TMP_DIR, 'tpcas-2', 'xml'))
        compress_tpcas(os.path.join(TMP_DIR, "tpcas-2"), N_PROC, 2, is_xml=True)

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

        # 3.3.1 pdf
        for corpus in [d for d in os.listdir(PDF_DIR) if os.path.isdir(os.path.join(PDF_DIR, d))]:
            for file_id in [d for d in os.listdir(os.path.join(CAS1_DIR, corpus))
                            if os.path.isdir(os.path.join(CAS1_DIR, corpus, d))]:
                os.makedirs(os.path.join(CAS2_DIR, corpus, file_id), exist_ok=True)
                # create symlink to images folder of CAS1
                if not os.path.islink(os.path.join(CAS2_DIR, corpus, file_id, "images")):
                    os.system("ln -s {} {}".format(os.path.join(CAS1_DIR, corpus, file_id, "images"),
                               os.path.join(CAS2_DIR, corpus, file_id, "images")))
                # copy .tpcas.gz files to CAS2_DIR
                if not os.path.isfile(os.path.join(CAS2_DIR, corpus, file_id, file_id + ".tpcas.gz")):
                    shutil.copy(os.path.join(TMP_DIR, "tpcas-2", corpus, file_id + ".tpcas.gz"),
                                os.path.join(CAS2_DIR, corpus, file_id, file_id + ".tpcas.gz"))

        # 3.3.2 xml
        newxml_local_list_fp.seek(0, 0)
        line = newxml_local_list_fp.readline()
        while line:
            dirname = line.strip().split('/')[-1]
            if os.path.isdir(os.path.join(CAS1_DIR, 'PMCOA', dirname)):
                tpcas_filename = [f for f in os.listdir(os.path.join(CAS1_DIR, 'PMCOA', dirname))
                                  if os.path.isfile(f) and f.endswith('.tpcas.gz')][0]
                os.makedirs(os.path.join(CAS2_DIR, 'PMCOA', dirname), exist_ok=True)
                if os.path.exists(os.path.join(CAS2_DIR, 'PMCOA', dirname, 'images')):
                    os.remove(os.path.join(CAS2_DIR, 'PMCOA', dirname, 'images'))
                os.system("ln -s {} {}".format(os.path.join(CAS1_DIR, 'PMCOA', dirname, 'images'),
                                               os.path.join(CAS2_DIR, 'PMCOA', dirname, 'images')))
                shutil.copy(os.path.join(TMP_DIR, 'tpcas-2', 'xml', dirname + '.tpcas.gz'),
                            os.path.join(CAS2_DIR, 'PMCOA', dirname, tpcas_filename))
            line = newxml_local_list_fp.readline()
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

        # 4.2 xml
        cas_dir_to_process = "${CAS2_DIR}/PMCOA"
        if os.path.isdir(os.path.join(TMP_DIR, "tpcas-2", "xml")):
            cas_dir_to_process = os.path.join(TMP_DIR, "tpcas-2", "xml")
        cas_file_list = os.listdir(cas_dir_to_process)
        if len(cas_file_list) > 0:
            # multiprocess gebib4nxml
            curr_idx = 0
            xml_bib_args = list()
            with tempfile.TemporaryDirectory() as tempdir:
                n_files_per_process = [math.floor(len(cas_file_list) / N_PROC)] * N_PROC
                for i in range(len(cas_file_list) % N_PROC):
                    n_files_per_process[i] += 1

                for proc_idx in range(N_PROC):
                    xml_filelist = open(os.path.join(tempdir, "file_to_process-{}".format(proc_idx)))
                    for filename in cas_file_list[curr_idx:curr_idx + n_files_per_process[proc_idx]]:
                        xml_filelist.write(filename.replace('.tpcas.gz', '') + '\n')
                    xml_filelist.close()
                    xml_bib_args.append((os.path.join(tempdir, xml_filelist), os.path.join(CAS2_DIR, 'PMCOA')))
                    curr_idx += n_files_per_process[proc_idx]

                pool = multiprocessing.Pool(processes=N_PROC)
                pool.starmap(xml_bib_worker, xml_bib_args)
                pool.close()
                pool.join()

    else:
        print("Skipping bib...")

    #################################################################################
    #####                     5. INVERT IMAGES                                  #####
    #################################################################################

    if 'invert_img' not in excluded_steps:
        print("Inverting images...")
        def invert_img_worker(file_id_list, corpus_dir):
            corpus_dir = '\ '.join(corpus_dir.strip().split(" "))
            for file_id in file_id_list:
                os.system("cmykinverter {}".format(os.path.join(corpus_dir, file_id, "images")))


        # invert images of each corpus in parallel
        for corpus in [d for d in os.listdir(CAS2_DIR) if os.path.isdir(os.path.join(CAS2_DIR, d))]:
            file_id_list = os.listdir(os.path.join(CAS2_DIR, corpus))
            n_files_per_process = [math.floor(len(file_id_list) / N_PROC)] * N_PROC
            for i in range(len(file_id_list) % N_PROC):
                n_files_per_process[i] += 1

            curr_idx = 0
            invert_img_mp_args = list()
            for proc_idx in range(N_PROC):
                invert_img_mp_args.append((file_id_list[curr_idx:curr_idx + n_files_per_process[proc_idx]],
                                     os.path.join(CAS1_DIR, corpus)))
                curr_idx += n_files_per_process[proc_idx]

            pool = multiprocessing.Pool(processes=N_PROC)
            pool.starmap(invert_img_worker, invert_img_mp_args)
            pool.close()
            pool.join()

    else:
        print("Skipping invert_img...")

    #################################################################################
    #####                     6. UPDATE INDEX                                   #####
    #################################################################################

    if "index" not in excluded_steps:
        print("Updating index...")

        os.environ['INDEX_PATH'] = INDEX_DIR
        INDEX_DIR_CUR = INDEX_DIR
        if os.path.isdir(INDEX_DIR):
            INDEX_DIR_CUR = INDEX_DIR + "_new"

        os.makedirs(os.path.join(INDEX_DIR_CUR, "db"), exist_ok=True)
        # assume there is no space in CAS2_DIR and INDEX_DIR_CUR
        os.system("create_single_index.sh -m 100000 {} {}".format(CAS2_DIR, INDEX_DIR_CUR))

        # TODO: test with lower papers_per_subindex

        os.chdir(INDEX_DIR_CUR)
        num_subidx_step = int(math.ceil(PAPERS_PER_SUBINDEX / 100000))
        first_idx_in_master = 0
        final_counter = 0
        last_idx_in_master = num_subidx_step
        num_subidx = len([f for f in os.listdir(INDEX_DIR_CUR) if 'subindex' in f])
        found = False
        while not found:
            if last_idx_in_master >= num_subidx:
                found = True
            for i in range(first_idx_in_master + 1, last_idx_in_master):
                os.system("indexmerger subindex_{} subindex_{} no".format(first_idx_in_master, i))
                os.system("rm -rf subindex_{}".format(i))
            if first_idx_in_master != final_counter:
                os.system("mv subindex_{} subindex_{}".format(first_idx_in_master, final_counter))
            first_idx_in_master = first_idx_in_master + num_subidx_step
            last_idx_in_master = last_idx_in_master + num_subidx_step
            final_counter += 1
        os.system("saveidstodb -i {}".format(INDEX_DIR_CUR))
        for root, dirs, files in os.walk(os.path.join(INDEX_DIR_CUR, "db")):
            for d in dirs:
                os.chmod(os.path.join(root, d), 777)
            for f in files:
                os.chmod(os.path.join(root, f), 777)
        os.system("rm -rf /data2/textpresso/db.bk")
        os.system("mv {} {}".format("/data2/textpresso/db", "/data2/textpresso/db.bk"))
        os.system("mv {} {}".format(os.path.join(INDEX_DIR_CUR, "db"), "/data2/textpresso/db"))
        os.system("ln -s {} {}".format("/data2/textpresso/db",
                                       os.path.join(INDEX_DIR_CUR, "db")))
        if os.path.isdir("{}_new".format(INDEX_DIR)):
            os.system("rm -rf {}.bk".format(INDEX_DIR))
            os.system("mv {} {}.bk".format(INDEX_DIR, INDEX_DIR))
            os.system("mv {} {}".format(INDEX_DIR_CUR, INDEX_DIR))
    else:
        print("Skipping index...")

    #################################################################################
    #####                  7. REMOVE INVALIDATED PAPERS                         #####
    #################################################################################

    # TODO: test

    if "remove_invalidated" not in EXCLUDE_STEPS:
        print("Removing invalid papers deleted from server...")
        # temp file for listing files to be deleted
        tpcas2_file_dict = dict()
        for corpus in [d for d in os.listdir(CAS2_DIR)
                       if os.path.isdir(os.path.join(CAS2_DIR, d))]:
            if corpus not in tpcas2_file_dict:
                tpcas2_file_dict[corpus] = list()
            for file_id in [d for d in os.listdir(os.path.join(CAS2_DIR, corpus))
                            if os.path.isfile(os.path.join(CAS2_DIR, corpus, d, d + '.tpcas.gz'))]:
                tpcas2_file_dict[corpus].append(file_id)

        tempfile_fp = tempfile.TemporaryFile()
        removedpdf_list_fp.seek(0, 0)
        line = removedpdf_list_fp.readline()
        while line:
            line = line.strip()
            corpus, file_id = line.split("/")[5], line.split("/")[6]
            if file_id in tpcas2_file_dict[corpus]:
                tempfile_fp.write(os.path.join(corpus, file_id, file_id + '.tpcas.gz' + '\n'))
            line = removedpdf_list_fp.readline()
        os.system("cas2index -i {} -o {} -r {}".format(CAS2_DIR, INDEX_DIR, tempfile_fp.name))

        removedpdf_list_fp.seek(0, 0)
        line = removedpdf_list_fp.readline()
        while line:
            line = line.strip()
            file_dir = '/'.join(line.split('/')[5:7])
            os.system("rm -rf {}".format(os.path.join(CAS1_DIR, file_dir)))
            os.system("rm -rf {}".format(os.path.join(CAS2_DIR, file_dir)))
            line = removedpdf_list_fp.readline()

        tempfile_fp.close()
    else:
        print("Skipping remove_invalidated...")

    if "remove_temp" not in EXCLUDE_STEPS:
        os.system("rm -r {}".format(os.path.join(TMP_DIR, "tpcas-1")))
        os.system("rm -r {}".format(os.path.join(TMP_DIR, "tpcas-2")))
        os.system("rm -r {}".format(TMP_DIR))

    logfile_fp.close()
    removedpdf_list_fp.close()
    # newxml_list_fp.close()
    newxml_local_list_fp.close()
    diffxml_list_fp.close()