#!/usr/bin/env python3

import os
import shutil
from urllib.request import urlopen
from lxml import etree
import argparse

DOWNLOAD_CHUNK_SIZE = 300 # the number of abstracts to download with one API call
TPCAS2_XENBASE_DIR = "/data/textpresso/tpcas-2/xenbase"


def download_abstract_chunk(corpus_dir, paper_id_list):
    """
    Download abstract xml files for the papers in the given paper_id_list
    :param corpus_dir: directory to download the abstracts to
    :param paper_id_list: list of papers to download abstract xml files
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&rettype=abstract&id={}".format(','.join(paper_id_list))
    source = urlopen(url)
    content = source.read()
    with open(os.path.join(corpus_dir, 'temp_abstract_chunk.xml'), 'wb') as fpout:
        fpout.write(content)

    # split the abstract_chunk into individual abstracts
    tree = etree.parse(os.path.join(corpus_dir, 'temp_abstract_chunk.xml'))
    root = tree.getroot()
    pubmed_article_list = root.xpath('./PubmedArticle')
    for idx, pubmed_article in enumerate(pubmed_article_list):
        pmid = pubmed_article.xpath('.//PMID')[0].text
        etree.ElementTree(pubmed_article).write(os.path.join(corpus_dir, '{}_abstract.xml'.format(pmid)))


def move_abstract_to_dir(corpus_dir):
    """
    Moves abstract xml files into their paper directories
    """
    # assume there is a directory for each paper
    papers = [d for d in os.listdir(corpus_dir) if os.path.isdir(os.path.join(corpus_dir, d))]
    files = [f for f in os.listdir(corpus_dir) if os.path.isfile(os.path.join(corpus_dir, f))]
    for paper in papers:
        paper_folder = os.path.join(corpus_dir, paper)
        for file in files:
            if file[-4:] == '.xml' and file.split('_')[0] == paper:
                if file not in os.listdir(paper_folder):
                    shutil.move(os.path.join(corpus_dir, file), paper_folder)


def get_abstracts(corpus_dir, chunk_size):
    paper_id_list = [d for d in os.listdir(corpus_dir) if os.path.isdir(os.path.join(corpus_dir, d))]
    if len(paper_id_list) < chunk_size:
        chunk_size = len(paper_id_list)

    # crawl in the unit of chunk_size
    n_crawl = int(len(paper_id_list) / chunk_size)
    for idx in range(n_crawl):
        paper_ids = paper_id_list[chunk_size * idx:chunk_size * (idx + 1)]
        download_abstract_chunk(corpus_dir, paper_ids)
        print("abstracts download chunk {}/{} complete".format(idx + 1, n_crawl))

    # download the remaining papers
    download_abstract_chunk(corpus_dir, paper_id_list[n_crawl * chunk_size:])
    move_abstract_to_dir(corpus_dir)
    os.remove(os.path.join(corpus_dir, "temp_abstract_chunk.xml"))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--tpcas2_dir', action='store', default='/data/textpresso/tpcas-2/xenbase')
    parser.add_argument('--chunk_size', action='store', default=300, type=int)
    args = parser.parse_args()

    paper_id_list = [d for d in os.listdir(args.tpcas2_dir) if os.path.isdir(os.path.join(args.tpcas2_dir, d))]

    n_crawl = int(len(paper_id_list) / args.chunk_size)
    for idx in range(n_crawl):
        paper_ids = paper_id_list[args.chunk_size * idx:args.chunk_size * (idx + 1)]
        download_abstract_chunk(paper_ids)
        print("chunk {} complete".format(idx))
    # download the remaining papers
    download_abstract_chunk(TPCAS2_XENBASE_DIR, paper_id_list[n_crawl * DOWNLOAD_CHUNK_SIZE:])
    move_abstract_to_dir(TPCAS2_XENBASE_DIR)
    os.remove(os.path.join(args.tpcas2_dir, "temp_abstract_chunk.xml"))