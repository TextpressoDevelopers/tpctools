import os
import time
import tarfile
import urllib.request
import multiprocessing
import shutil


def get_newxml_list(ftp_mount_path, newxml_list_file):
    # mount pmcoa ftp locally through curl
    os.system("curlftpfs ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/ {}".format(ftp_mount_path))

    # retrieve a list of files on pmcoa
    # original file format is "date(YYYY-MM-DD) iso-time(hh:mm:ss.sssssssss) /mnt/pmc_ftp/00/00/PMC1790863.tar.gz
    # write "Y-m-d H:M:S filename" to newxml_list temp file
    # Python and shell script both lists in alphabetically/numerically ascending order
    with open(newxml_list_file, 'r') as newxml_list_fp:
        for dir in [d for d in os.listdir(ftp_mount_path)
                    if os.path.isdir(os.path.join(ftp_mount_path, d))]:
            for subdir in [sd for sd in os.listdir(os.path.join(ftp_mount_path, dir))
                           if os.path.isdir(os.path.join(ftp_mount_path, dir, sd))]:
                for xml_file in [f for f in os.listdir(os.path.join(ftp_mount_path, dir, subdir))
                                 if os.path.isfile(os.path.join(ftp_mount_path, dir, subdir, f))]:
                    mtime = os.path.getmtime(os.path.join(ftp_mount_path, dir, subdir, xml_file))
                    isotime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
                    xml_filepath = os.path.join(ftp_mount_path, dir, subdir, xml_file)
                    newxml_list_fp.write("{} {}\n".format(isotime, xml_filepath))

    os.system("umount {}".format(FTP_MNTPNT))


def tar_extract_files(members):
    """ helper function to choose specific file types that are to be extract """
    exclude_filetype_set = {".pdf", ".PDF", ".mp4", ".webm", ".flv", ".avi", ".zip", ".mov",
                            ".csv", ".xls", ".xlsx", ".doc", ".docx", ".docs", ".docm",
                            ".ppt", ".pptx", ".rar", ".txt", ".TXT", ".wmv", ".DOC"}
    for tarinfo in members:
        if os.path.splitext(tarinfo.name)[1] not in exclude_filetype_set:
            yield tarinfo


def xml_download_worker(xml_list_file, offset, n_lines, output_dir):
    """
    Worker to be used for downloading xml files
    :param xml_list_fp: file pointer of file holding a list of xml files (.tar.gz) to download
    :param offset: offset of file to start reading from
    :param n_lines: number of lines to read starting from the offset
    """
    with open(xml_list_file, 'r') as xml_list_fp:
        xml_list_fp.seek(offset)
        line_cnt = 0
        while line_cnt < n_lines:
            line = xml_list_fp.readline().strip()
            line_cnt += 1
            if line == '':
                continue
            ftp_filepath = '/'.join(line.split()[2].split("/")[-3:])
            tar_filename = line.split('/')[-1]
            if os.path.isdir(os.path.join(output_dir, tar_filename)) and tar_filename != '':
                shutil.rmtree(os.path.join(output_dir, tar_filename))
            urllib.request.urlretrieve("ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/" + ftp_filepath,
                                       filename=os.path.join(output_dir, tar_filename))
            tar_file = tarfile.open(os.path.join(output_dir, tar_filename))
            tar_file.extractall(members=tar_extract_files(tar_file), path=output_dir)
            tar_file.close()
            os.remove(os.path.join(output_dir, tar_filename))


def download_xmls(xml_list_file, output_dir, n_proc):
    # prepare for multiprocessing
    line_offset_list = list()
    offset = 0
    with open(xml_list_file, 'r') as xml_list_fp:
        xml_list_fp.seek(0)
        line = xml_list_fp.readline()
        while line:
            line_offset_list.append(offset)
            offset += len(line)
            line = xml_list_fp.readline()

    # obtain the list of (offset, number of lines to read) pair
    n_lines = len(line_offset_list)
    n_lines_per_process = [int(n_lines / n_proc)] * n_proc
    for i in range(n_lines % n_proc):
        n_lines_per_process[i] += 1

    # set up multiprocessing arguments
    xml_download_mp_args = list()
    offset, offset_idx = 0, 0
    for proc_idx in range(n_proc):
        xml_download_mp_args.append((xml_list_file, offset, n_lines_per_process[proc_idx], output_dir))
        offset_idx += n_lines_per_process[proc_idx]
        if proc_idx < n_proc - 1:
            offset = line_offset_list[offset_idx]

    pool = multiprocessing.Pool(processes=n_proc)
    pool.starmap(xml_download_worker, xml_download_mp_args)
    pool.close()
    pool.join()