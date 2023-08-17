import argparse
import logging
import requests
import json
import gzip
from os import environ, path, remove

from okta_utils import (
    get_authentication_token,
    generate_headers
)

logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

limit = 100
loop_count = 1300

start_reference_id = 0
start_count = 0

start_ref_list_url = environ['API_URL'] + "reference/get_textpresso_reference_list/"
start_bib_url = environ['API_URL'] + "reference/get_bib_info/"
start_pdf_url = environ['API_URL'] + "reference/referencefile/download_file/"


def download_files(mod, pdf_dir, biblio_dir):

    token = get_authentication_token()    
    headers = generate_headers(token)

    count = start_count
    from_reference_id = start_reference_id
    for index in range(loop_count):
        offset = index * limit
        ref_list_url = f"{start_ref_list_url}{mod}?page_size={limit}&from_reference_id={from_reference_id}"
        data = get_data_from_url(ref_list_url, headers)
        if data is None:
            continue

        logger.info(f"offset={offset} data={len(data)}")
        
        if len(data) == 0:
            break
        
        for x in data:

            count += 1
            ref_curie = x['reference_curie']
            reference_id = x['reference_id']

            (md5sum, referencefile_id) = get_md5sum_reffile_id(mod, x['main_referencefiles'])

            logger.info(f"{count}: {reference_id} {ref_curie} {md5sum} {referencefile_id}")

            ## generating bib files
            bib_url = f"{start_bib_url}{ref_curie}?mod_abbreviation={mod}&return_format=txt" 
            biblioTxt = get_data_from_url(bib_url, headers)
            if not isinstance(biblioTxt, str):
                for index in range(5):
                    sleep(60)
                    biblioTxt = get_data_from_url(bib_url, headers)
                    if isinstance(biblioTxt, str):
                        break
            if isinstance(biblioTxt, str):
                with open(biblio_dir + ref_curie + ".txt", "w") as bib_file:
                    bib_file.write(biblioTxt)
            else:
                logger.info(f"Error Generating bib file for {ref_curie}. returning {str(biblioTxt)}") 

            ## downloading PDFs
            pdf_url = f"{start_pdf_url}{referencefile_id}"
            pdf_content = get_data_from_url(pdf_url, headers, 'pdf')
            if 'Internal Server Error' in str(pdf_content):
                for index in range(5):
                    sleep(60)
                    pdf_content = get_data_from_url(pdf_url, headers, 'pdf')
                    if 'Internal Server Error' not in str(pdf_content):
                        break
            if 'Internal Server Error' in str(pdf_content):
                logger.info(f"Error downloading pdf for {ref_curie}.")
            else:
                with open(pdf_dir + ref_curie + ".pdf", "wb") as pdf_file:
                    pdf_file.write(pdf_content)
            from_reference_id = reference_id
    
    logger.info("DONE!")


def get_md5sum_reffile_id(mod, pdffiles):

    # this logic is for mod = 'SGD'
    # TODO: add logic for mod = 'WB' and other mods

    md5sum = None
    referencefile_id = None
    for x in sorted(pdffiles, key=lambda p: p['date_created']):        
        if x['source_is_pmc']:
            md5sum = x['md5sum']
            referencefile_id = x['referencefile_id']
            break
        md5sum = x['md5sum']
        referencefile_id = x['referencefile_id']
            
    return(md5sum, referencefile_id)

                    
def get_data_from_url(url, headers, file_type='json'):

    try:
        response = requests.request("GET", url, headers=headers)
        # response.raise_for_status()  # Check if the request was successful
        if file_type == 'pdf':
            return response.content
        else:
            content = response.json()
            if content is None:
                content = response.text()
            return content
    except requests.exceptions.RequestException as e:
        logger.info(f"Error occurred for accessing/retrieving data from {url}: {e}")
        return None

    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('-m', '--mod', action='store', type=str,
                        help='download pdfs and bib files for MOD',
                        choices=['WB', 'SGD', 'FB', 'ZFIN', 'MGI', 'RGD', 'XB'])

    parser.add_argument('-p', '--pdf_dir', action='store',
                        help='directory_with_full_path for storing the pdfs')

    parser.add_argument('-b', '--bib_dir', action='store',
			help='directory_with_full_path for storing the biblio files')
    
    args = vars(parser.parse_args())

    if not args['mod'] or not args['pdf_dir'] or not args['bib_dir']:
        print("Example usage: python3 download_pdfs_bib_files.py -m WB -p ./pdfs/ -b ./biblio_files/")
        exit()

    download_files(args['mod'], args['pdf_dir'], args['bib_dir'])
