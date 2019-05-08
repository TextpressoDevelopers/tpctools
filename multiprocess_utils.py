import os
import math
import subprocess
import gzip
import re

TEMP_DIR = "/data/textpresso/tempdir"


def mp_setup(file_list, const_arg_tup, n_proc, create_temp_files=False):
    """
    Returns the arguments used for multiprocessing
    :param file_list: list of files to multiprocess. if create_temp_files=True, assume the entries in
                      file_list are correctly formatted
    :param const_arg_tup: tuple of arguments that are constant among all processes
    :param n_proc: number of processes
    :param create_temp_files: whether the temp file is passed into the worker
    :return: arguments to be passed to multiprocessing worker
    """
    mp_args = list()
    n_files_per_process = [int(len(file_list) / n_proc)] * n_proc
    for i in range(len(file_list) % n_proc):
        n_files_per_process[i] += 1
    curr_idx = 0
    for proc_idx in range(n_proc):
        if create_temp_files:
            with open("/tmp/tmplist_{}.txt".format(proc_idx), 'w') as fpout:
                for filename in file_list[curr_idx:curr_idx + n_files_per_process[proc_idx]]:
                    fpout.write(filename + '\n')
            mp_args.append((proc_idx,) + const_arg_tup)
        else:
            mp_args.append((file_list[curr_idx:curr_idx + n_files_per_process[proc_idx]],) + const_arg_tup)
        curr_idx += n_files_per_process[proc_idx]

    return mp_args


def cas1_worker(tmp_file_idx, corpus, input_dir, file_format):
    """
    Worker used for processing pdf/txt/xml to tpcas file with multiprocessing
    :param tmp_file_idx: idx of the tmp_file to read the ids from
    :param corpus: name of the corpus
    :param input_dir: PDF_DIR, XML_DIR, or TXT_DIR
    :param file_format: 1 if PDF, 2 if XML, 3 if TXT - only 1 and 3 used. xml supported in another function
    """
    corpus = '\ '.join(corpus.strip().split(" "))
    input_folder = os.path.join(input_dir, corpus) + '/'
    output_folder = corpus + '/'
    dirlist_file = "/tmp/tmplist_{}.txt".format(tmp_file_idx)
    command = 'articles2cas -i {} -l {} -o {} -t {} -p'.format(input_folder, dirlist_file, output_folder, file_format)
    os.system(command)


def cas1_xml_worker(tmp_file_idx, input_dir):
    """
    Worker used for processing xml to tpcas file with multiprocessing
    :param tmp_file_idx: idx of the temp_file to read the ids from
    :param input_dir: XML_DIR
    """
    dirlist_file = "/tmp/tmplist_{}.txt".format(tmp_file_idx)
    command = 'articles2cas -i {} -l {} -t 2 -o PMCOA -p'.format(input_dir, dirlist_file)
    os.system(command)


def cas2_worker(corpus_list, input_path, output_path):
    """
    Worker used for processing tpcas-1 files to tpcas-2 files with multiprocessing
    :param corpus_list: list of corpuses
    :param input_path: path of tpcas-1 directory
    :param output_path: path of tpcas-2 directory
    """
    for corpus in corpus_list:
        corpus = '\ '.join(corpus.strip().split(" "))
        command = ("runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi "
                   "{} {}").format(os.path.join(input_path, corpus), os.path.join(output_path, corpus))
        os.system(command)


def cas2_xml_worker(subdir, input_path, output_path):
    """
    Worker used for processing xml tpcas-1 files to tpcas-2 files with multiprocessing
    :param subdir:
    :param input_path:
    :param output_path:
    :return:
    """
    command = ("runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi "
               "{} {}").format(os.path.join(input_path, subdir), output_path)
    os.system(command)


def gzip_worker(file_list, path, type):
    """
    Worker used for compressing .tpcas files
    :param file_list: list of files to compress - file_id for tpcas1, file_id.tpcas for tpcas2
    :param path: path to the corpus of the target files to be compressed
    :param type: 1 if cas1, 2 if cas2, 3 if .nxml
    """
    assert type in {1, 2, 3}
    for file in file_list:
        if type == 1:
            target_file = os.path.join(path, file, file + '.tpcas')
        elif type == 2 or type == 3:
            target_file = os.path.join(path, file)
        print(target_file)
        if type == 1 or type == 2:  # tpcas
            if target_file.endswith('.tpcas') and os.path.isfile(target_file):
                subprocess.check_call(['gzip', '-f', target_file])
        elif type == 3:  # nxml
            if target_file.endswith('.nxml') and os.path.isfile(target_file):
                subprocess.check_call(['gzip', '-f', target_file])


def gunzip_worker(zipped_file_list, path):
    """
    Worker used for uncomressing .tpcas.tar.gz files
    :param zipped_file_list: list of files to be unzipped
    :param path: the path where the zipped files are stored
    """
    for filename in zipped_file_list:
        tpcas_file = os.path.join(path, filename)
        if os.path.isfile(tpcas_file):
            subprocess.check_call(['gunzip', tpcas_file])
