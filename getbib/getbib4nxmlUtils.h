/* 
 * File:   Utils.h
 * Author: lyl
 *
 * Created on November 15, 2013, 3:48 PM
 */

#ifndef UTILS_H
#define	UTILS_H

#include <iostream>
#include <uima/api.hpp>
#include <boost/iostreams/filtering_streambuf.hpp>
#include <boost/iostreams/copy.hpp>
#include <boost/iostreams/filter/gzip.hpp>
#include <boost/date_time.hpp>
#include <unistd.h>

extern std::string uncompressGzip(std::string gzFile); // uncompress gz file
extern std::string getTempDir(); // generate a temp dir under /run/shm to store all temp files for each run. using year+month+day+min
extern void writeToIndexDescriptor(std::string indexpath, std::string descriptor, std::string tempDir); //write to Tpcas2index.xml descriptor
void writeDefaultBibFile(const std::string& file_path);

#endif	/* UTILS_H */

