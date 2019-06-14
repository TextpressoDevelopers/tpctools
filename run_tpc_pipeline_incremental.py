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
import difflib

from getpdfs.getpdfs import download_pdfs
from getxmls.getxmls import get_newxml_list, download_xmls
from getbib.download_abstract import get_abstracts
from getbib.make_bib import create_bib
from pdf2text.pdf2text import convert_pdf2txt
from multiprocess_utils import mp_setup, cas1_worker, cas1_xml_worker, cas2_worker, cas2_xml_worker,\
                               gzip_worker, gunzip_worker


default_config = {
    "PDF_DIR": "/data/textpresso/raw_files/pdf",
    "XML_DIR": "/data/textpresso/raw_files/xml",
    "TXT_DIR": "/data/textpresso/raw_files/txt",
    "CAS1_DIR": "/data/textpresso/tpcas-1",
    "CAS2_DIR": "/data/textpresso/tpcas-2",
    "TMP_DIR": "/data/textpresso/tmp",
    "FTP_MNTPNT": "/mnt/pmc_ftp",
    "INDEX_DIR": "/data/textpresso/luceneindex",
    "DB_DIR": "/data2/textpresso/db",
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
    parser.add_argument("-d", "--db-dir", action='store', default='',
                        help="directory for lucene index db")
    parser.add_argument("-P", "--num-proc", action='store', default='',
                        help="maximum number of parallel processes")
    parser.add_argument("-e", "--exclude-step", action='store', default='',
                        help="do not execute the steps specified by a comma separated list of step names. "
                             "Step names are: download_pdf,download_xml,cas1,cas2,bib,index,"
                             "invert_img,remove_invalidated,remove_temp.")
    parser.add_argument("-test", "--test", action='store_true', default=False,
                        help="if True, run in test mode")
    args = parser.parse_args()

    # if there is no user input for directory and it is in test mode
    # change the directory name to prevent overwriting
    if args.test:
        config["TEST"] = args.test

    if args.pdf_dir:
        config["PDF_DIR"] = args.pdf_dir
    elif args.test:
        config["PDF_DIR"] = config["PDF_DIR"] + "_test"

    if args.xml_dir:
        config["XML_DIR"] = args.xml_dir
    elif args.test:
        config["XML_DIR"] = config["XML_DIR"] + "_test"

    if args.txt_dir:
        config["TXT_DIR"] = args.txt_dir
    elif args.test:
        config["TXT_DIR"] = config["TXT_DIR"] + "_test"

    if args.cas1_dir:
        config["CAS1_DIR"] = args.cas1_dir
    elif args.test:
        config["CAS1_DIR"] = config["CAS1_DIR"] + "_test"

    if args.cas2_dir:
        config["CAS2_DIR"] = args.cas2_dir
    elif args.test:
        config["CAS2_DIR"] = config["CAS2_DIR"] + "_test"

    if args.tmp_dir:
        config["TMP_DIR"] = args.tmp_dir
    elif args.test:
        config["TMP_DIR"] = config["TMP_DIR"] + "_test"

    if args.ftp_dir:
        config["FTP_MNTPNT"] = args.ftp_dir
    elif args.test:
        config["FTP_MNTPNT"] = config["FTP_MNTPNT"] + "_test"

    if args.index_dir:
        config["INDEX_DIR"] = args.index_dir
    elif args.test:
        config["INDEX_DIR"] = config["INDEX_DIR"] + "_test"

    if args.db_dir:
        config["DB_DIR"] = args.db_dir
    elif args.test:
        config["DB_DIR"] = config["DB_DIR"] + "_test"

    if args.num_proc:
        config["N_PROC"] = int(args.num_proc)
    if args.exclude_step:
        config["EXCLUDE_STEPS"] = args.exclude_step


def generate_tpcas1(input_dir, file_format, n_proc):
    """
    Generates tpcas1 files
    :param input_dir: PDF_DIR, XML_DIR, or TXT_DIR
    :param file_format: 1 if PDF, 2 if XML, 3 if TXT - only 1 and 3 used. xml in different function
    :param n_proc: number of processes to run in parallel
    """
    os.chdir(CAS1_DIR)

    for corpus in [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]:
        print("processing {}".format(corpus))
        corpus_file_list = os.listdir(os.path.join(input_dir, corpus))

        cas1_mp_args = mp_setup(corpus_file_list, (corpus, input_dir, file_format), n_proc, create_temp_files=True)

        # execute cas1_worker in parallel
        pool = multiprocessing.Pool(processes=n_proc)
        pool.starmap(cas1_worker, cas1_mp_args)
        pool.close()
        pool.join()

        print("{} cas1 complete".format(corpus))
        for proc_idx in range(n_proc):
            os.remove("/tmp/tmplist_{}.txt".format(proc_idx))


def generate_xml_tpcas1(input_dir, xml_list_file, n_proc):
    """
    Generates xml tpcas1 files
    :param input_dir: XML_DIR
    :param xml_list_file: file that stores the list of nxml files to be processed
    :param n_proc: number of processes to run in parallel
    """
    os.chdir(CAS1_DIR)

    # read the list of xml files to be be processed from input file
    file_list = list()
    with open(xml_list_file, 'r') as fpin:
        line = fpin.readline()
        while line:
            line = line.strip()
            if line != '':
                file_list.append(line.split('/')[-1])
            line = fpin.readline()

    cas1_mp_args = mp_setup(file_list, (input_dir,), n_proc, create_temp_files=True)

    # execute cas1_xml_worker in parallel
    pool = multiprocessing.Pool(processes=n_proc)
    pool.starmap(cas1_xml_worker, cas1_mp_args)
    pool.close()
    pool.join()

    print("xml cas1 complete")
    for proc_idx in range(n_proc):
        os.remove("/tmp/tmplist_{}.txt".format(proc_idx))


def generate_tpcas2(corpus_list, n_proc, input_dir, output_dir):
    """
    Generates tpcas-2 files using multiprocessing
    :param corpus_list: list of corpus to be processed
    :param n_proc: number of processes to run in parallel
    :param input_dir: path where the tpcas-1 files are stored at
    :param output_dir: path where the tpcas-2 files are generated to
    """
    cas2_mp_args = mp_setup(corpus_list, (input_dir, output_dir), n_proc)

    pool = multiprocessing.Pool(processes=n_proc)
    pool.starmap(cas2_worker, cas2_mp_args)
    pool.close()
    pool.join()


def generate_xml_tpcas2(n_proc, input_dir, output_dir):
    """
    Generates tpcas-2 xml files using multiprocessing
    :param n_proc: number of processes to run in parallel
    :param input_dir: path where the tpcas-1 files are stored at
    :param output_dir: path where the tpcas-2 files are generated to
    """
    cas2_mp_args = list()

    # all the files are allocated into n_proc folders to be used for multiprocessing
    for subdir in [d for d in os.listdir(input_dir)
                   if os.path.isdir(os.path.join(input_dir, d))]:
        cas2_mp_args.append((subdir, input_dir, output_dir))

    pool = multiprocessing.Pool(processes=n_proc)
    pool.starmap(cas2_xml_worker, cas2_mp_args)
    pool.close()
    pool.join()


def compress_tpcas(input_dir, n_proc, cas_type, is_xml=False, target_corpus=None):
    """
    Compresses .tpcas files in input_dir to .tpcas.gz using multiprocessing
    :param input_dir: for cas_type 1 - directory of the corpus
                      for cas_type 2 - directory where .tpcas files are located at
    :param n_proc: number of processes to run in parallel
    :param cas_type: 1 if cas1, 2 if cas2
    :param is_xml: True if compressing xml tpcas, False if not
    :param target_corpus: specific target corpus to gzip
    """
    assert cas_type == 1 or cas_type == 2

    for corpus in [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]:
        if is_xml and corpus != 'xml':
            continue
        if target_corpus is not None and corpus != target_corpus:
            continue

        tpcas_file_list = os.listdir(os.path.join(input_dir, corpus))

        gzip_mp_args = mp_setup(tpcas_file_list, (os.path.join(input_dir, corpus), cas_type), n_proc)

        # run gzip_worker on multiprocess
        pool = multiprocessing.Pool(processes=n_proc)
        pool.starmap(gzip_worker, gzip_mp_args)
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
    DB_DIR = default_config["DB_DIR"]
    N_PROC = default_config["N_PROC"]
    EXCLUDE_STEPS = default_config["EXCLUDE_STEPS"]
    TEST_MODE = default_config["TEST"]

    # set environment variable
    if 'LD_LIBRARY_PATH' in os.environ:
        os.environ['LD_LIBRARY_PATH'] = "{}:/usr/local/lib".format(os.environ['LD_LIBRARY_PATH'])
    else:
        os.environ['LD_LIBRARY_PATH'] = "/usr/local/lib"
    os.environ['PATH'] = "{}:/usr/local/bin".format(os.environ['PATH'])

    logfile_fp = tempfile.NamedTemporaryFile()
    removedpdf_list_fp = tempfile.NamedTemporaryFile()

    # add configuration if running in test mode
    if TEST_MODE:
        print("running in testing mode")

    newxml_list_file = os.path.join(XML_DIR, "newxml_list.txt")  # list of new xml files
    diffxml_list_file = os.path.join(XML_DIR, "diff_list.txt")  # list of xml files that have changed
    newxml_local_list_file = os.path.join(XML_DIR, "newxml_local_list.txt")  # list of path to new xml files

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

        if not TEST_MODE:
            get_newxml_list(FTP_MNTPNT, newxml_list_file)

        # 1.1.2 calculate diff between existing files and files on PMCOA and download the new ones.
        # If there are no pre-existing files, download the full repository

        newxml_id_list = []  # list of paper ids to be downloaded

        if os.path.isfile(os.path.join(XML_DIR, "current_filelist.txt")):
            # obtain the difference between original xml list and new xml list
            newxml_list_text = open(newxml_list_file, 'r').readlines()
            current_filelist_text = open(os.path.join(XML_DIR, "current_filelist.txt")).readlines()
            with open(diffxml_list_file, 'w') as fpout:
                for line in difflib.unified_diff(current_filelist_text, newxml_list_text):
                    line = line.strip()
                    if line in {'', '+', '+++', '-', '---'}:
                        continue
                    if line[0] == '+':
                        newxml_id_list.append(line.split()[-1].split('/')[-1][:-7])
                        fpout.write(line[1:] + '\n')
            print("newxml id list: ", newxml_id_list)

            # delete previous versions and get a list of updated/new files
            for newxml_file_id in newxml_id_list:
                if os.path.isdir(os.path.join(XML_DIR, newxml_file_id)) and newxml_file_id != '':
                    shutil.rmtree(os.path.join(XML_DIR, newxml_file_id), ignore_errors=True)

            # download diff files
            if len(newxml_id_list) > 0:
                if len(newxml_id_list) < N_PROC:
                    n_proc = len(newxml_id_list)
                else:
                    n_proc = N_PROC
                download_xmls(diffxml_list_file, XML_DIR, n_proc)

        else:
            # download all files
            download_xmls(newxml_list_file, XML_DIR, N_PROC)

            # copy newxml_list to diffxml_list
            with open(diffxml_list_file, 'w') as fpout:
                with open(newxml_list_file, 'r') as newxml_list_fp:
                    line = newxml_list_fp.readline()
                    while line:
                        if line.strip() != '':
                            fpout.write(line)
                            newxml_id_list.append(line.split()[-1].split('/')[-1][:-7])
                        line = newxml_list_fp.readline()

        # remove empty files from diffxml_list_file by rewriting the file
        shutil.move(diffxml_list_file, os.path.join(XML_DIR, "diff_list_temp.txt"))
        with open(diffxml_list_file, 'w') as fpout:
            with open(os.path.join(XML_DIR, "diff_list_temp.txt"), 'r') as fpin:
                line = fpin.readline()
                while line:
                    file_id = line.strip().split()[-1].split('/')[-1][:-7]
                    if os.path.isdir(os.path.join(XML_DIR, file_id)):
                        fpout.write(line)
                    line = fpin.readline()
        os.remove(os.path.join(XML_DIR, "diff_list_temp.txt"))

        # save the current list
        with open(os.path.join(XML_DIR, "current_filelist.txt"), 'w') as fpout:
            with open(newxml_list_file, 'r') as fpin:
                line = fpin.readline()
                while line:
                    if line.strip() != '':
                        fpout.write(line)
                    line = fpin.readline()

        # 1.1.3 save new xml local file list
        with open(newxml_local_list_file, 'w') as fpout:
            for newxml_id in newxml_id_list:
                fpout.write(os.path.join(XML_DIR, newxml_id) + '\n')

        # 1.1.4 compress nxml and put images in a separate directory

        # obtain list of nxml file names and rename the .nxml files to PMC Id
        nxml_file_list = list()  # list of file_id/nxml_file_name
        for newxml_id in newxml_id_list:
            for nxml_file in os.listdir(os.path.join(XML_DIR, newxml_id)):
                if nxml_file.endswith(".nxml") and os.path.isfile(os.path.join(XML_DIR, newxml_id, nxml_file)):
                    os.rename(os.path.join(XML_DIR, newxml_id, nxml_file),
                              os.path.join(XML_DIR, newxml_id, newxml_id + '.nxml'))
                    nxml_file_list.append(os.path.join(newxml_id, newxml_id + '.nxml'))

        gzip_nxml_mp_args = mp_setup(nxml_file_list, (XML_DIR, 3), N_PROC)

        pool = multiprocessing.Pool(processes=N_PROC)
        pool.starmap(gzip_worker, gzip_nxml_mp_args)
        pool.close()
        pool.join()

        # move images to separate subdirectory inside the id folder
        for newxml_id in newxml_id_list:
            os.makedirs(os.path.join(XML_DIR, newxml_id, "images"), exist_ok=True)
            for f in os.listdir(os.path.join(XML_DIR, newxml_id)):
                if '.nxml' not in f and f != 'images':
                    shutil.move(os.path.join(XML_DIR, newxml_id, f),
                                os.path.join(XML_DIR, newxml_id, "images", f))

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
                removedpdf_list_fp.write(match.group(2))  # write the paper name to the file
            line = logfile_fp.readline()
    else:
        print("skipping download_pdf")


    #################################################################################
    #####                      2. GENERATE TPCAS-1                              #####
    #################################################################################

    if 'cas1' not in excluded_steps:
        print("Generating CAS1 files...")

        # 2.1 Generate TPCAS-1 files from PDF files

        # Obtain all the folder names in PDF_DIR then create tpcas1 folders for every corpus
        # folder names correspond to corpus names
        os.makedirs(CAS1_DIR, exist_ok=True)
        for folder in [d for d in os.listdir(PDF_DIR) if os.path.isdir(os.path.join(PDF_DIR, d))]:
            os.makedirs(os.path.join(CAS1_DIR, folder), exist_ok=True)

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

        print("Number of failures")
        for corpus in missing_files_dict:
            print("{}: {}".format(corpus, len(missing_files_dict[corpus])))

        convert_pdf2txt(missing_files_dict, PDF_DIR, TXT_DIR, N_PROC)

        # assume there are more txt files than N_PROC
        if sum([len(missing_files_dict[corpus]) for corpus in missing_files_dict]) < N_PROC:
            n_proc = 1
        else:
            n_proc = N_PROC
        generate_tpcas1(TXT_DIR, 3, n_proc)  # convert txt files to cas1 files
        compress_tpcas(CAS1_DIR, n_proc, 1)

        # move newly converted cas1 to tmp files
        for corpus in missing_files_dict:
            if len(missing_files_dict[corpus]) == 0:
                continue
            for file_id in missing_files_dict[corpus]:
                cas_file = os.path.join(CAS1_DIR, corpus, file_id, file_id + '.tpcas.gz')
                if os.path.isfile(cas_file):
                    shutil.copy(cas_file, os.path.join(TMP_DIR, 'tpcas-1', corpus))

        # 2.2 Generate TPCAS-1 from XML FILES
        if os.path.exists(newxml_local_list_file):
            print("Generating tpcas-1 of xml files")
            # remove old versions
            with open(newxml_local_list_file, 'r') as fpin:
                line = fpin.readline()
                while line:
                    line = line.strip()
                    if line != '':
                        file_id = line.split('/')[-1]
                        shutil.rmtree(os.path.join(CAS1_DIR, "PMCOA", file_id), ignore_errors=True)
                    line = fpin.readline()

            os.makedirs(os.path.join(CAS1_DIR, 'PMCOA'), exist_ok=True)
            generate_xml_tpcas1(XML_DIR, newxml_local_list_file, N_PROC)

            # create symbolic link in CAS1_DIR, pointing to images in XML_DIR
            with open(newxml_local_list_file, 'r') as fpin:
                line = fpin.readline()
                while line:
                    line = line.strip()
                    if line != '':
                        file_id = line.split('/')[-1]
                        shutil.rmtree(os.path.join(CAS1_DIR, "PMCOA", file_id, "images"), ignore_errors=True)
                        os.symlink(os.path.join(XML_DIR, file_id, "images"),
                                   os.path.join(CAS1_DIR, 'PMCOA', file_id, "images"))
                    line = fpin.readline()

            # compress files in CAS1_DIR
            compress_tpcas(CAS1_DIR, N_PROC, 1, target_corpus="PMCOA")

            # 2.2.1 copy xml files to TMP_DIR
            os.makedirs(os.path.join(TMP_DIR, 'tpcas-1', 'xml'), exist_ok=True)

            dir_list = list()
            with open(newxml_local_list_file, 'r') as fpin:
                line = fpin.readline()
                while line:
                    line = line.strip()
                    if line != '':
                        dir_list.append(line.split("/")[-1])
                    line = fpin.readline()

            num_papers_to_process_together = int(math.ceil(len(dir_list) / N_PROC))
            i, subdir_idx = 1, 1
            os.makedirs(os.path.join(TMP_DIR, 'tpcas-1', 'xml', 'subdir_1'), exist_ok=True)
            for dirname in dir_list:
                if i > num_papers_to_process_together:
                    i = 1
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

        # 3.1 Prepare UIMA Analysis

        # create directory structure of tmp/tpcas-2 if it does not exist
        os.chdir(CAS1_DIR)
        for folder in [d for d in os.listdir(CAS1_DIR) if os.path.isdir(os.path.join(CAS1_DIR, d))]:
            os.makedirs(os.path.join(TMP_DIR, 'tpcas-2', folder), exist_ok=True)
        os.makedirs(os.path.join(TMP_DIR, 'tpcas-2', 'xml'), exist_ok=True)

        # 3.1.1 Decompress all pdf cas files in tmp/tpcas-1 before running UIMA analysis
        for corpus in [d for d in os.listdir(os.path.join(TMP_DIR, 'tpcas-1'))
                       if os.path.isdir(os.path.join(TMP_DIR, 'tpcas-1', d))]:
            if corpus == 'xml':
                continue
            cas1_zipped_list = [f for f in os.listdir(os.path.join(TMP_DIR, 'tpcas-1', corpus))
                                if f[-3:] == '.gz']

            gunzip_mp_args = mp_setup(cas1_zipped_list, (os.path.join(TMP_DIR, 'tpcas-1', corpus),), N_PROC)

            pool = multiprocessing.Pool(processes=N_PROC)
            pool.starmap(gunzip_worker, gunzip_mp_args)
            pool.close()
            pool.join()
        
        # 3.1.2 Decompress all xml cas files in tmp/tpcas-1 before running UIMA analysis
        if os.path.exists(newxml_local_list_file):
            gunzip_mp_args = list()
            for subdir in [d for d in os.listdir(os.path.join(TMP_DIR, 'tpcas-1', 'xml'))
                           if os.path.isdir(os.path.join(TMP_DIR, 'tpcas-1', 'xml', d))]:
                gunzip_mp_args.append(([f for f in os.listdir(os.path.join(TMP_DIR, 'tpcas-1', 'xml', subdir))
                                        if os.path.isfile(os.path.join(TMP_DIR, 'tpcas-1', 'xml', subdir, f))
                                        and f.endswith('.tpcas.gz')],
                                       os.path.join(TMP_DIR, 'tpcas-1', 'xml', subdir)))
            pool = multiprocessing.Pool(processes=N_PROC)
            pool.starmap(gunzip_worker, gunzip_mp_args)
            pool.close()
            pool.join()
            print("Successfully unzipped .tpcas.gz files")

        # 3.2 APPLY UIMA ANALYSIS
        
        # 3.2.1 Run UIMA analysis on pdf files
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
        
        # 3.2.2 Run UIMA analysis on xml files
        if os.path.exists(newxml_local_list_file):
            print("Running UIMA analysis for xml...")

            # remove old versions of xml
            with open(newxml_local_list_file, 'r') as fpin:
                line = fpin.readline()
                while line:
                    line = line.strip()
                    if line != '':
                        shutil.rmtree(os.path.join(CAS2_DIR, "PMCOA", line.split('/')[-1]), ignore_errors=True)
                    line = fpin.readline()

            generate_xml_tpcas2(N_PROC, os.path.join(TMP_DIR, 'tpcas-1', 'xml'),
                                os.path.join(TMP_DIR, 'tpcas-2', 'xml'))
            compress_tpcas(os.path.join(TMP_DIR, "tpcas-2"), N_PROC, 2, is_xml=True)

        # 3.3 Setup TPCAS-2 DIRS

        # create TPCAS-2 directory and its subdirectories
        os.makedirs(CAS2_DIR, exist_ok=True)
        os.makedirs(os.path.join(CAS2_DIR, "PMCOA"), exist_ok=True)
        for corpus in [d for d in os.listdir(CAS1_DIR)
                       if os.path.isdir(os.path.join(CAS1_DIR, d))]:
            os.makedirs(os.path.join(CAS2_DIR, corpus), exist_ok=True)

        # 3.3.1 pdf
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

        # 3.3.2 xml
        if os.path.exists(newxml_local_list_file):
            with open(newxml_local_list_file, 'r') as fpin:
                line = fpin.readline()
                while line:
                    line = line.strip()
                    if line != '':
                        dirname = line.split('/')[-1]
                        if os.path.isdir(os.path.join(CAS1_DIR, 'PMCOA', dirname)):
                            tpcas_filename = [f for f in os.listdir(os.path.join(CAS1_DIR, 'PMCOA', dirname))
                                              if f.endswith('.tpcas.gz')][0]
                            os.makedirs(os.path.join(CAS2_DIR, 'PMCOA', dirname), exist_ok=True)
                            if os.path.exists(os.path.join(CAS2_DIR, 'PMCOA', dirname, 'images')):
                                os.remove(os.path.join(CAS2_DIR, 'PMCOA', dirname, 'images'))
                            os.symlink(os.path.join(CAS1_DIR, 'PMCOA', dirname, 'images'),
                                       os.path.join(CAS2_DIR, 'PMCOA', dirname, 'images'))
                            shutil.copy(os.path.join(TMP_DIR, 'tpcas-2', 'xml', dirname + '.tpcas.gz'),
                                        os.path.join(CAS2_DIR, 'PMCOA', dirname, tpcas_filename))
                    line = fpin.readline()

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
        cas_dir_to_process = os.path.join(CAS2_DIR, "PMCOA")
        if os.path.isdir(os.path.join(TMP_DIR, "tpcas-2", "xml")):
            cas_dir_to_process = os.path.join(TMP_DIR, "tpcas-2", "xml")

        cas_file_list = os.listdir(cas_dir_to_process)
        cas_file_list = list(map(lambda x: x.replace('.tpcas.gz', ''), cas_file_list))

        # multiprocess gebib4nxml
        if len(cas_file_list) > 0:
            def xml_bib_worker(proc_idx, output_path):
                input_file = "/tmp/tmplist_{}.txt".format(proc_idx)
                os.system("getbib4nxml \"{}\" -f {}".format(output_path, input_file))

            xml_bib_args = mp_setup(cas_file_list, (os.path.join(CAS2_DIR, 'PMCOA'),), N_PROC, create_temp_files=True)

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

            invert_img_mp_args = mp_setup(file_id_list, (os.path.join(CAS1_DIR, corpus),), N_PROC)

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

        # obtain the total number of cas files to process
        n_cas_files = 0
        for corpus in os.listdir(CAS2_DIR):
            n_cas_files += len(os.listdir(os.path.join(CAS2_DIR, corpus)))
        n_files_per_index = math.ceil(n_cas_files / N_PROC)
        if n_files_per_index > 100000:
            n_files_per_index = 100000

        os.makedirs(os.path.join(INDEX_DIR_CUR, "db"), exist_ok=True)
        # assume there is no space in CAS2_DIR and INDEX_DIR_CUR
        os.system("create_single_index.sh -m {} {} {}".format(n_files_per_index, CAS2_DIR, INDEX_DIR_CUR))

        os.chdir(INDEX_DIR_CUR)
        num_subidx_step = int(math.ceil(PAPERS_PER_SUBINDEX / n_files_per_index))
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

        print("Saving ids to db...")
        INDEX_DIR_CUR = INDEX_DIR
        os.system("saveidstodb -i {}".format(INDEX_DIR_CUR))
        for root, dirs, files in os.walk(os.path.join(INDEX_DIR_CUR, "db")):
            for d in dirs:
                os.chmod(os.path.join(root, d), 777)
            for f in files:
                os.chmod(os.path.join(root, f), 777)
        shutil.rmtree(DB_DIR + ".bk", ignore_errors=True)
        if os.path.exists(DB_DIR):
            shutil.move(DB_DIR, DB_DIR + ".bk")
        shutil.move(os.path.join(INDEX_DIR, "db"), DB_DIR)
        os.symlink(DB_DIR, os.path.join(INDEX_DIR, "db"))
    else:
        print("Skipping index...")

    #################################################################################
    #####                  7. REMOVE INVALIDATED PAPERS                         #####
    #################################################################################

    # TODO: test

    if "remove_invalidated" not in EXCLUDE_STEPS:
        print("Removing invalid papers deleted from server...")
        tpcas2_file_dict = dict()
        for corpus in [d for d in os.listdir(CAS2_DIR)
                       if os.path.isdir(os.path.join(CAS2_DIR, d))]:
            if corpus not in tpcas2_file_dict:
                tpcas2_file_dict[corpus] = list()
            for file_id in [d for d in os.listdir(os.path.join(CAS2_DIR, corpus))
                            if os.path.isfile(os.path.join(CAS2_DIR, corpus, d, d + '.tpcas.gz'))]:
                tpcas2_file_dict[corpus].append(file_id)

        tempfile_fp = tempfile.TemporaryFile()  # temp file for listing files to be deleted
        removedpdf_list_fp.seek(0, 0)
        line = removedpdf_list_fp.readline()
        while line:
            line = line.strip()
            if line != '':
                corpus, file_id = line.split("/")[5], line.split("/")[6]
                if file_id in tpcas2_file_dict[corpus]:
                    tempfile_fp.write(os.path.join(corpus, file_id, file_id + '.tpcas.gz' + '\n'))
            line = removedpdf_list_fp.readline()
        os.system("cas2index -i {} -o {} -r {}".format(CAS2_DIR, INDEX_DIR, tempfile_fp.name))

        removedpdf_list_fp.seek(0, 0)
        line = removedpdf_list_fp.readline()
        while line:
            line = line.strip()
            if line != '':
                file_dir = '/'.join(line.split('/')[5:7])
                shutil.rmtree(os.path.join(CAS1_DIR, file_dir))
                shutil.rmtree(os.path.join(CAS2_DIR, file_dir))
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

    if os.path.exists(newxml_list_file):
        os.remove(newxml_list_file)
    if os.path.exists(diffxml_list_file):
        os.remove(diffxml_list_file)
    if os.path.exists(newxml_local_list_file):
        os.remove(newxml_local_list_file)
