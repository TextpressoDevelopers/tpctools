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
#include <lucene++/targetver.h>
#include <lucene++/LuceneHeaders.h>
#include <boost/iostreams/filtering_streambuf.hpp>
#include <boost/iostreams/copy.hpp>
#include <boost/iostreams/filter/gzip.hpp>
#include <unistd.h>

using namespace std;
using namespace uima;
using namespace Lucene;


//extern const char* newindexflag;  //new index lock flag
#endif	/* UTILS_H */


extern string uncompressGzip(string gzFile); // uncompress gz file
extern string getTempDir(); // generate a temp dir under /run/shm to store all temp files for each run. using year+month+day+min
extern void writeToIndexDescriptor(string indexpath, string descriptor, string tempDir); //write to Tpcas2index.xml descriptor
//extern void optimizeIndex(string indexpath);
