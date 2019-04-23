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
