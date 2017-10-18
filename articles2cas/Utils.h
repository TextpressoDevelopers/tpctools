/**
    Project: libtpc
    File name: Utils.h
    
    @author valerio
    @version 1.0 7/26/17.
*/

#ifndef LIBTPC_UTILS_H
#define LIBTPC_UTILS_H

#include <string>

class Utils {
public:
    /*!
     * generate a random path name for a tmp directory
     */
    static std::string get_temp_dir_path();

    /*!
     * write a uima descriptor for an index to file
     * @param index_path the path of the index
     * @param descriptor_path the path of the descriptor to be created
     * @param tmp_conf_files_path the path of the directory containing the temp files for the index
     */
    static void write_index_descriptor(const std::string& index_path, const std::string& descriptor_path,
                                       const std::string& tmp_conf_files_path);

    /*!
     * decompress file to a new file and return file path of the latter
     * @param gz_file the gx file to decompress
     * @return the file path of the decompressed file
     */
    static std::string decompress_gzip(const std::string & gz_file, const std::string& tmp_dir);
};


#endif //LIBTPC_UTILS_H
