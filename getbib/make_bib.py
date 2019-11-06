#!/usr/bin/env python3

import os
import re
import shutil
import xml.etree.ElementTree
from lxml import etree
import argparse

TPCAS2_XENBASE_DIR = "/data/textpresso/tpcas-2/xenbase"
INFO_FILE_DIR = "/data/textpresso/xenbase_info"


def format_date(date_str):
    """
    Convert input date_str to the format of "YYYY-MM-DD"
    :param date_str: input date_str to be formatted
    :return: formatted date string
    """
    date_component = date_str.split("/")
    if len(date_component) == 3:
        if len(date_component[0]) == 4:
            date_str = "-".join(date_component)
        elif len(date_component[2]) == 4:
            date_str = date_component[2] + "-" + date_component[0] + "-" + date_component[1]
    return date_str


def parse_abstract_xml(corpus_dir, file):
    """
    Parse abstract text from the given xml file
    :param file: abstract xml file to be parsed
    :return: parsed abstract text
    """
    abstract_text = ""

    try:
        tree = etree.parse(os.path.join(corpus_dir, file))
        root = tree.getroot()
        pubmed_article_list = root.xpath('./PubmedArticle')
        if len(pubmed_article_list) == 0:
            article = root.xpath('.//Article')[0]
        else:
            pubmed_article = pubmed_article_list[0]
            article = pubmed_article.xpath('.//Article')[0]
        abstract = article.xpath('.//AbstractText')
        if len(abstract) > 0:
            abstract_text = abstract[0].text

    except OSError:
        pass

    if abstract_text is None:
        abstract_text = ""

    return abstract_text


def parse_accession(corpus_dir, file):
    """
    Parse full accession of the paper from the given xml file
    :param file: abstract xml file to be parsed
    :return: parsed accession string
    """
    accession_str = ""

    try:
        tree = etree.parse(os.path.join(corpus_dir, file))
        root = tree.getroot()
        pubmed_article_list = root.xpath('./PubmedArticle')
        if len(pubmed_article_list) == 0:
            article = root.xpath('.//Article')[0]
        else:
            pubmed_article = pubmed_article_list[0]
            article = pubmed_article.xpath('.//Article')[0]
        accession_list = article.xpath('./ELocationID')
        for idx, accession in enumerate(accession_list):
            if accession.attrib['EIdType'] == "doi":
                accession_str = "Other:doi:" + accession_list[idx].text

    except OSError:
        pass

    if accession_str is None:
        accession_str = ""

    return accession_str


def parse_type(corpus_dir, file):
    """
    Parse the type of paper from the given xml file. Only return the first type in the type list
    of the xml file.
    :param file: abstract xml file to be parsed
    :return: type of the paper
    """
    paper_type = ""
    try:
        tree = etree.parse(os.path.join(corpus_dir,  file))
        root = tree.getroot()
        pubmed_article_list = root.xpath('./PubmedArticle')
        if len(pubmed_article_list) == 0:
            article = root.xpath('.//Article')[0]
        else:
            pubmed_article = pubmed_article_list[0]
            article = pubmed_article.xpath('.//Article')[0]
        type_list = article.xpath('.//PublicationType')
        if len(type_list) > 0:
            paper_type = type_list[0].text

    except OSError:
        pass

    if paper_type is None:
        paper_type = ""

    return paper_type


def write_to_bib_file(fpout, field, bib_dict):
    if field in bib_dict:
        fpout.write(field + '|' + bib_dict[field] + '\n')
    else:
        fpout.write(field + '|\n')


def generate_bib(corpus_dir, paper_id, info_file):
    """
    Generate .bib file of the given paper_id using given info_file
    :param paper_id: id of the paper to generate .bib file for
    :param info_file: .info file of the paper id provided
    """
    bib_dict = dict()
    with open(info_file, 'r') as fpin:
        with open(os.path.join(corpus_dir, paper_id, paper_id + '.bib'), 'w') as fpout:
            line = fpin.readline()
            volume, pages = "", ""
            pmid, pmcid, full_accession = "", "", ""
            while line:
                # there may be '=' in the content
                field = line.split("=")[0].strip()
                content = "=".join(line.split("=")[1:]).strip()
                # field, content = list(map(lambda x: x.strip(), line.split("=")))
                if field == 'Authors':
                    author_list = content.split(',')
                    author_list = list(map(lambda x: x.strip(), author_list))
                    # fpout.write('author|' + ' ; '.join(author_list) + '\n')
                    bib_dict['author'] = ' ; '.join(author_list)
                elif field == 'Title':
                    # fpout.write('title|' + content + '\n')
                    bib_dict['title'] = content
                elif field == 'Journal':
                    # fpout.write('journal|' + content + '\n')
                    bib_dict['journal'] = content
                elif field == 'Date':
                    # fpout.write('year|' + format_date(content) + '\n')
                    bib_dict['year'] = format_date(content)
                elif field == 'PubMedId':
                    pmid = content
                elif field == 'PMCId':
                    pmcid = content
                elif field == 'Volume':
                    if content != '':
                        volume = "V: " + content.strip()
                elif field == 'Pages':
                    if content.strip() != '':
                        pages = "P: " + content.strip()
                line = fpin.readline()

            full_accession = parse_accession(corpus_dir, '{}/{}_abstract.xml'.format(paper_id, paper_id))
            if pmid != "":
                full_accession += " PMID:" + pmid + " "
            if pmcid != "":
                if pmcid[:3] == 'PMC':
                    pmcid = pmcid[3:]
                full_accession += " PMCID:" + pmcid + " "
            paper_type = parse_type(corpus_dir, '{}/{}_abstract.xml'.format(paper_id, paper_id))
            if paper_type != "":
                bib_dict['type'] = paper_type
            bib_dict['accession'] = full_accession
            bib_dict['citation'] = volume + pages
            bib_dict['abstract'] = parse_abstract_xml(corpus_dir, '{}/{}_abstract.xml'.format(paper_id, paper_id))

            # write .bib file in order - error if this order is not followed
            write_to_bib_file(fpout, 'author', bib_dict)
            write_to_bib_file(fpout, 'accession', bib_dict)
            write_to_bib_file(fpout, 'type', bib_dict)
            write_to_bib_file(fpout, 'title', bib_dict)
            write_to_bib_file(fpout, 'journal', bib_dict)
            write_to_bib_file(fpout, 'citation', bib_dict)
            write_to_bib_file(fpout, 'year', bib_dict)
            write_to_bib_file(fpout, 'abstract', bib_dict)


def gather_info_files(corpus_dir, info_file_dir):
    """ Copy .info files into the paper tpcas-2 directories in order to use them for creating .bib files """
    # assume there is a directory for each paper
    papers = [d for d in os.listdir(corpus_dir) if os.path.isdir(os.path.join(corpus_dir, d))]
    files = [f for f in os.listdir(info_file_dir) if os.path.isfile(os.path.join(info_file_dir, f))]
    for paper in papers:
        paper_folder = os.path.join(corpus_dir, paper)
        for file in files:
            if file[:len(paper) + 1] == paper + '-' and file[-5:] == '.info':
                shutil.copyfile(os.path.join(info_file_dir, file), os.path.join(paper_folder, file))


def create_bib(corpus_dir, info_file_dir):
    gather_info_files(corpus_dir, info_file_dir)
    print("info files copied")
    # assume every paper is in the folder named by its pmid
    paper_id_list = [d for d in os.listdir(corpus_dir) if os.path.isdir(os.path.join(corpus_dir, d))]
    for paper_id in paper_id_list:
        try:
            paper_folder = os.path.join(corpus_dir, paper_id)
            # open .info file
            for file in os.listdir(paper_folder):
                if file.endswith('.info'):
                    generate_bib(corpus_dir, paper_id, os.path.join(paper_folder, file))
                    # print("{}.bib generated".format(paper_id))
        except:
            print("Error while processing paper " + paper_id)

    for paper_id in paper_id_list:
        if os.path.exists(os.path.join(corpus_dir, paper_id, paper_id + '_abstract.xml')):
            os.remove(os.path.join(corpus_dir, paper_id, paper_id + '_abstract.xml'))
    print("completed creating .bib files for {}".format(corpus_dir))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--tpcas2_dir', action='store', default='/data/textpresso/tpcas-2/xenbase')
    args = parser.parse_args()

    create_bib(args.tpcas2_dir, INFO_FILE_DIR)
