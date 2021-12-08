#!/usr/bin/env python3

"""Copy pdf files from server and map file names"""
import hashlib
import logging
import shutil
import urllib.request
import urllib.error
import urllib.parse
import re
import os
import argparse
import glob
import psycopg2
import time

__author__ = "Valerio Arnaboldi"

__version__ = "1.0.1"


def download_pdfs(args_delete_old, args_log_file, args_log_level, args_out_dir):
    logging.basicConfig(filename=args_log_file, level=getattr(logging, args_log_level.upper()))
    if args_delete_old:
        shutil.rmtree(args_out_dir)
    try:
        os.makedirs(os.path.join(args_out_dir, "C. elegans"))
        os.makedirs(os.path.join(args_out_dir, "C. elegans Supplementals"))
    except FileExistsError:
        logging.warning("Directories already exist")
    non_nematode_papers = set()
#    conn = psycopg2.connect("dbname='testdb' user='acedb' host='131.215.52.76'")
    conn = psycopg2.connect("dbname='muellerdb' user='mueller' host='131.215.76.23' password='goldturtle'")
    cur = conn.cursor()
    cur.execute("""SELECT * FROM pap_curation_flags WHERE pap_curation_flags = 'non_nematode'""")
    rows = cur.fetchall()
    for row in rows:
        non_nematode_papers.add("WBPaper" + row[0])

    # read papers mapping
    id = None
    papers_cgc_map = {}
    papers_pubmed_map = {}
    wb_2_pmid = {}
    invalid_papers = set()
    for line in urllib.request.urlopen("http://tazendra.caltech.edu/~postgres/michael/papers.ace"):
        line = line.decode('utf-8')
        linearr = line.strip().split()
        if len(linearr) > 1:
            if linearr[0] == "Paper":
                id = linearr[2][1:len(linearr[2])-1]
            elif linearr[0] == "Name" and linearr[1].startswith("\"cgc"):
                papers_cgc_map[linearr[1][4:len(linearr[1])-1]] = id
            elif len(linearr) >= 4 and linearr[0] == "Database" and linearr[2] == "\"PMID\"":
                papers_pubmed_map[linearr[3][1:len(linearr[3])-1]] = id
                wb_2_pmid[id] = linearr[3][1:len(linearr[3])-1]
            elif linearr[0] == "Status" and linearr[1] == "\"Invalid\"":
                invalid_papers.add(id)

    # read papers list and map them
    p = re.compile('href="(.*)"')

    pdflink = ""
    all_wbpapers = set()
    files_to_download = {}
    for line in urllib.request.urlopen("http://tazendra.caltech.edu/~azurebrd/cgi-bin/allpdfs.cgi?action=textpresso"):
        try:
            line = line.decode('utf-8')
            linearr = line.strip().split()
            if len(linearr) > 1:
                filetype = linearr[0]
                namescheme = linearr[1]
                pdflink = p.findall(" ".join(linearr[3:]))[0]
                if pdflink.lower().endswith(".pdf"):
                    if filetype == "supplemental":
                        pdfname = re.split("_|-", pdflink.split("/")[-2])[0]
                    else:
                        pdfname = re.split("_|-", pdflink.split("/")[-1])[0]
                    subdir = "C. elegans"
                    if namescheme == "wb":
                        pdfname = "WBPaper" + str(pdfname)
                    elif namescheme == "cgc":
                        if str(pdfname).lstrip("0") in papers_cgc_map:
                            pdfname = papers_cgc_map[str(pdfname).lstrip("0")]
                        else:
                            continue
                    elif namescheme == "pubmed":
                        if str(pdfname).lstrip("0") in papers_pubmed_map:
                            pdfname = papers_pubmed_map[str(pdfname).lstrip("0")]
                        else:
                            continue
                        subdir = "C. elegans"
                    if pdfname in non_nematode_papers or pdfname in invalid_papers:
                        if len(glob.glob(os.path.join(args_out_dir, "C. elegans", pdfname + "*"))) > 0:
                            for file in glob.glob(os.path.join(args_out_dir, "C. elegans", pdfname + "*")):
                                shutil.rmtree(file)
                            logging.info("Removing invalid paper " + os.path.join(args_out_dir, "C. elegans", pdfname))
                        if len(glob.glob(os.path.join(args_out_dir, "C. elegans Supplementals", pdfname + "*"))) > 0:
                            for file in glob.glob(os.path.join(args_out_dir, "C. elegans Supplementals", pdfname + "*")):
                                shutil.rmtree(file)
                            logging.info("Removing invalid paper " + os.path.join(args_out_dir,
                                                                                  "C. elegans Supplementals", pdfname))
                        continue
                    if filetype == "supplemental":
                        subdir = "C. elegans Supplementals"
                        pdfname += ".sup."
                        skip_file = False
                        simfiles = glob.glob(os.path.join(args_out_dir, subdir, pdfname, pdfname) + "*.pdf")
                        for simfile_name in simfiles:
                            if hashlib.md5(urllib.request.urlopen(pdflink).read()).digest() == \
                                    hashlib.md5(open(simfile_name, "rb").read()).digest():
                                skip_file = True
                                break
                        if skip_file:
                            continue
                        sup_num = len(simfiles) + 1
                        while pdfname + str(sup_num) in files_to_download:
                            all_wbpapers.add(pdfname + str(sup_num))
                            sup_num += 1
                        all_wbpapers.add(pdfname + str(sup_num))
                        pdfname += str(sup_num)
                    else:
                        all_wbpapers.add(pdfname)
                        if pdflink.lower().endswith("_temp.pdf") and pdfname in files_to_download or \
                                        pdflink.lower().endswith("_ocr.pdf") and pdfname in files_to_download:
                            continue
                    if pdfname in files_to_download:
                        link_re = re.search("[0-9]+[\_\-][^\d]+([0-9]+)", pdflink.replace(" ", ""))
                        link_num = 0
                        if link_re is not None:
                            link_num = int(link_re.group(1))
                        stored_re = re.search("[0-9]+[\_\-][^\d]+([0-9]+)",
                                              files_to_download[pdfname][0].replace("%20", ""))
                        stored_num = 0
                        if stored_re is not None:
                            stored_num = int(stored_re.group(1))
                        if link_num <= stored_num:
                            continue
                    files_to_download[pdfname] = (pdflink.replace(" ", "%20"), os.path.join(args_out_dir, subdir,
                                                                                            pdfname, pdfname + ".pdf"))
                else:
                    logging.warning("Skipping file: " + pdflink)
        except UnicodeDecodeError:
            pass

    for pdflink, file_path in files_to_download.values():
        try:
            # check if best file selected for download is already present in the dest dir
            if not args_delete_old and len(glob.glob(file_path)) > 0 and \
                            hashlib.md5(urllib.request.urlopen(pdflink).read()).digest() == \
                            hashlib.md5(open(file_path, "rb").read()).digest():
                logging.info("File already present in collection, skipping " + pdflink)
                continue
            if "WBPaperdaniel" in file_path:
                logging.info("Skipping WBPaperdaniel " + pdflink)
                continue
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            urllib.request.urlretrieve(pdflink, file_path)
            time.sleep(1.0)
            logging.info("Downloading paper: " + pdflink + " to " + file_path)
        except urllib.error.HTTPError:
            logging.error("Paper not found: " + pdflink)
            shutil.rmtree(os.path.dirname(file_path))
            continue

    # delete local files that have been removed from server
    local_files = set(os.listdir(os.path.join(args_out_dir, "C. elegans")))
    for file_to_remove in local_files.difference(all_wbpapers):
        shutil.rmtree(os.path.join(args_out_dir, "C. elegans", file_to_remove))
        logging.info("Removing deleted paper " + os.path.join("C. elegans", file_to_remove))
    local_files = set(os.listdir(os.path.join(args_out_dir, "C. elegans Supplementals")))
    for file_to_remove in local_files.difference(all_wbpapers):
        shutil.rmtree(os.path.join(args_out_dir, "C. elegans Supplementals", file_to_remove))
        logging.info("Removing deleted paper " + os.path.join("C. elegans Supplementals", file_to_remove))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Download pdf files from Tazendra server and store them in a local "
                                                 "directory, after applying name conversion")
    parser.add_argument("-d", "--delete-old", dest="delete_old", action="store_true",
                        help="delete old files before downloading the new ones")
    parser.add_argument("-l", "--log-file", metavar="log_file", dest="log_file", default="info.log", type=str,
                        help="path to log file")
    parser.add_argument("-L", "--log-level", metavar="log_level", dest="log_level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="log level")
    parser.add_argument("out_dir", metavar="out_dir", type=str, help="output directory")

    args = parser.parse_args()

    download_pdfs(args.delete_old, args.log_file, args.log_level, args.out_dir)
