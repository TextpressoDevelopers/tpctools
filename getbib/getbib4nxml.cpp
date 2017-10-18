/* 
 * File:   main.cpp
 * Author: mueller
 *
 * Created on October 26, 2016, 12:31 PM
 */

//#include "../TextpressoCentralGlobals.h"
#include "../../TextpressoCentralGlobalDefinitions.h"
#include "xercesc/util/XMLString.hpp"
#include <uima/api.hpp>
#include <uima/xmideserializer.hpp>
#include <cstdio>
#include <fstream>
#include "getbib4nxmlUtils.h"
#include <boost/filesystem.hpp>
#include <boost/date_time.hpp>

#define TPCAS_2_LINDEX_VERSION "0.9.0"

//using namespace boost::filesystem;

void print_who() {
    std::cout << std::endl << "CAS file bib extracter" << std::endl;
    std::cout << "Build Date: " << __DATE__ << std::endl;
    std::cout << "Version: " << TPCAS_2_LINDEX_VERSION << std::endl;
}

void print_help() {
    std::cout << std::endl;
    std::cout << "Usage: getbib [tpcas_file_directory]" << std::endl;
    std::cout << std::endl;
}

void addCasFile(const char* pszInput, std::string indexdescriptor) {
    std::string gzfile(pszInput);
    std::cout << gzfile << std::endl;
    if (boost::filesystem::path(gzfile).filename().string().find("tpcas") == std::string::npos)
        return;
    const char * descriptor = indexdescriptor.c_str();
    std::string tpcasfile = uncompressGzip(gzfile);
    try {
        /* Create/link up to a UIMACPP resource manager instance (singleton) */
        (void) uima::ResourceManager::createInstance("TPCAS2LINDEXAE");
        uima::ErrorInfo errorInfo;
        uima::AnalysisEngine * pEngine
                = uima::Framework::createAnalysisEngine(descriptor, errorInfo);
        if (errorInfo.getErrorId() != UIMA_ERR_NONE) {
            std::cerr << std::endl
                    << "  Error string  : "
                    << uima::AnalysisEngine::getErrorIdAsCString(errorInfo.getErrorId())
                    << std::endl
                    << "  UIMACPP Error info:" << std::endl
                    << errorInfo << std::endl;
            exit((int) errorInfo.getErrorId());
        }
        uima::TyErrorId utErrorId; // Variable to store UIMACPP return codes
        /* Get a new CAS */
        uima::CAS* cas = pEngine->newCAS();
        if (cas == NULL) {
            std::cerr << "pEngine->newCAS() failed." << std::endl;
            exit(1);
        }
        /* process input / cas */
        try {
            /* initialize from an xmicas */
            XMLCh* native = XMLString::transcode(tpcasfile.c_str());
            LocalFileInputSource fileIS(native);
            XMLString::release(&native);
            uima::XmiDeserializer::deserialize(fileIS, *cas, true);
            std::string filename(tpcasfile);
            /* process the CAS */
            ((uima::AnalysisEngine*) pEngine)->process(*cas);
        } catch (uima::Exception e) {
            uima::ErrorInfo errInfo = e.getErrorInfo();
            std::cerr << "Error " << errInfo.getErrorId() << " " << errInfo.getMessage() << std::endl;
            std::cerr << errInfo << std::endl;
            std::cerr << "Writing default bib file";
            writeDefaultBibFile(gzfile.replace(gzfile.end()-8, gzfile.end(), "bib"));
        }
        /* call collectionProcessComplete */
        utErrorId = pEngine->collectionProcessComplete();
        /* Free annotator */
        utErrorId = pEngine->destroy();
        delete cas;
        delete pEngine;
        std::remove(tpcasfile.c_str()); //delete uncompressed temp casfile
    } catch (uima::Exception e) {
        std::cerr << "Exception: " << e << std::endl;
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        print_who();
        print_help();
        return (-1);
    }
    boost::filesystem::path inputdir(argv[1]); //tpcas file dir
    std::string indexpath("");
    std::string tempDir = getTempDir();
    bool dir_created = false;
    while (dir_created != true) {
        std::cout << "dir not created" << std::endl;
        tempDir = getTempDir();
        dir_created = boost::filesystem::create_directories(tempDir);
    }
    std::string indexdescriptor(tempDir + "/Tpcas2Bib.xml");
    writeToIndexDescriptor(indexpath, indexdescriptor, tempDir); ///write to /run/shm/[tempDir]/Tpcas2Lindex.xml
    boost::filesystem::directory_iterator end_itr;
    for (boost::filesystem::directory_iterator dit(inputdir); dit != end_itr; dit++) {
        if (boost::filesystem::is_regular_file(dit->status())) {
          std::cout << "file path is " << dit->path() << std::endl;
            addCasFile(dit->path().string().c_str(), indexdescriptor);
        } else if (boost::filesystem::is_directory(dit->status())) {
            boost::filesystem::path subdir(dit->path().string().c_str());
            for (boost::filesystem::directory_iterator dit2(subdir); dit2 != end_itr; dit2++) {
                if (boost::filesystem::is_regular_file(dit2->status())) {
                    addCasFile(dit2->path().string().c_str(), indexdescriptor);
                }
            }
        }
    }
    boost::filesystem::remove(indexdescriptor);
    boost::filesystem::remove(tempDir);
}
