import copy
import logging
import re
import shutil
import os

import PyPDF2 as PyPDF2
from PyPDF2.generic import TextStringObject
from PyPDF2.pdf import ContentStream, b_, FloatObject, NumberObject
from PyPDF2.utils import u_

def get_fulltext_from_pdfs(pdfs_urls):

    def customExtractText(self):
        text = u_("")
        content = self["/Contents"].getObject()
        if not isinstance(content, ContentStream):
            content = ContentStream(content, self.pdf)
        # Note: we check all strings are TextStringObjects.  ByteStringObjects
        # are strings where the byte->string encoding was unknown, so adding
        # them to the text here would be gibberish.
        for operands, operator in content.operations:
            if operator == b_("Tj"):
                _text = operands[0]
                if isinstance(_text, TextStringObject):
                    text += _text
            elif operator == b_("T*"):
                text += "\n"
            elif operator == b_("'"):
                text += "\n"
                _text = operands[0]
                if isinstance(_text, TextStringObject):
                    text += operands[0]
            elif operator == b_('"'):
                _text = operands[2]
                if isinstance(_text, TextStringObject):
                    text += "\n"
                    text += _text
            elif operator == b_("TJ"):
                for i in operands[0]:
                    if isinstance(i, TextStringObject):
                        text += i
                    elif isinstance(i, FloatObject) or isinstance(i, NumberObject):
                        if i < -100:
                            text += " "
            elif operator == b_("TD") or operator == b_("Tm"):
                if len(text) > 0 and text[-1] != " " and text[-1] != "\n":
                    text += " "
        return text

    logger = logging.getLogger("AFP fulltext extraction")
    complete_fulltext = ""
    for pdf_url in pdfs_urls:
        pdf_fulltext = ""
        with urllib.request.urlopen(pdf_url) as response:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                shutil.copyfileobj(response, tmp_file)

        try:
            pdf_reader = PyPDF2.PdfFileReader(open(tmp_file.name, 'rb'))
            for i in range(pdf_reader.numPages):
                page_obj = pdf_reader.getPage(i)
                page_obj.extractText = customExtractText
                pdf_fulltext += page_obj.extractText(page_obj)
        except:
            pass

        sentences = pdf_fulltext.split("\n")
        if not any(["reviewer" in sentence and "comment" in sentence for sentence in sentences]):
            complete_fulltext += pdf_fulltext
        else:
            logger.info("Skipping response to reviewers")
    complete_fulltext = complete_fulltext.replace("\n", " ")

    return complete_fulltext


def get_fulltext_from_pdfs_from_file(pdf_file):
    def customExtractText(self):
        text = u_("")
        content = self["/Contents"].getObject()
        if not isinstance(content, ContentStream):
            content = ContentStream(content, self.pdf)
        # Note: we check all strings are TextStringObjects.  ByteStringObjects
        # are strings where the byte->string encoding was unknown, so adding
        # them to the text here would be gibberish.
        for operands, operator in content.operations:
            if operator == b_("Tj"):
                _text = operands[0]
                if isinstance(_text, TextStringObject):
                    text += _text
            elif operator == b_("T*"):
                text += "\n"
            elif operator == b_("'"):
                text += "\n"
                _text = operands[0]
                if isinstance(_text, TextStringObject):
                    text += operands[0]
            elif operator == b_('"'):
                _text = operands[2]
                if isinstance(_text, TextStringObject):
                    text += "\n"
                    text += _text
            elif operator == b_("TJ"):
                for i in operands[0]:
                    if isinstance(i, TextStringObject):
                        text += i
                    elif isinstance(i, FloatObject) or isinstance(i, NumberObject):
                        if i < -100:
                            text += " "
            elif operator == b_("TD") or operator == b_("Tm"):
                if len(text) > 0 and text[-1] != " " and text[-1] != "\n":
                    text += " "
        return text

    logger = logging.getLogger("AFP fulltext extraction")
    complete_fulltext = ""
    pdf_fulltext = ""
    try:
        pdf_reader = PyPDF2.PdfFileReader(open(pdf_file, 'rb'))
        for i in range(pdf_reader.numPages):
            page_obj = pdf_reader.getPage(i)
            page_obj.extractText = customExtractText
            pdf_fulltext += page_obj.extractText(page_obj)
    except:
        print("conversion failed")
        pass
    # pdf_reader = PyPDF2.PdfFileReader(open(pdf_file, 'rb'))
    # for i in range(pdf_reader.numPages):
    #     page_obj = pdf_reader.getPage(i)
    #     page_obj.extractText = customExtractText
    #     pdf_fulltext += page_obj.extractText(page_obj)
    #     print("Page {} complete".format(i + 1))

    sentences = pdf_fulltext.split("\n")
    if not any(["reviewer" in sentence and "comment" in sentence for sentence in sentences]):
        complete_fulltext += pdf_fulltext
    else:
        logger.info("Skipping response to reviewers")
    complete_fulltext = complete_fulltext.replace("\n", " ")

    return complete_fulltext


if __name__ == '__main__':
    pdf_list_file = "/home/daniel/tpcas1_missed_pdf.txt"
    PDF_DIR = "/data/textpresso/raw_files_temp_new/pdf/xenbase"
    TEXT_DIR = "/data/textpresso/raw_files/txt/xenbase"
    with open(pdf_list_file, 'r') as fpin:
        line = fpin.readline()
        while line:
            print("processing {}".format(line.strip()))
            assert line.strip()[-4:] == '.pdf'
            pmid = line.split('.')[0]
            pdf_file = os.path.join(PDF_DIR, pmid, pmid + ".pdf")
            text = get_fulltext_from_pdfs_from_file(pdf_file)
            if not os.path.isdir(os.path.join(TEXT_DIR, pmid)):
                os.mkdir(os.path.join(TEXT_DIR, pmid))
            with open(os.path.join(TEXT_DIR, pmid, pmid + ".txt"), 'w') as fpout:
                fpout.write(text)
            line = fpin.readline()

    # pmid = '24233724'
    # pdf_filename = "/data/textpresso/raw_files/pdf/xenbase/{}/{}.pdf".format(pmid, pmid)
    # full_text = get_fulltext_from_pdfs_from_file(pdf_filename)
    # with open("{}_text.txt".format(pmid), 'w') as fpout:
    #     fpout.write(full_text)
