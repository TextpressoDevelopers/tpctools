/*
 * File:   main.cpp
 * Author: liyuling
 *
 * Created on November, 2013
 */

//#include "../TextpressoCentralGlobals.h"
#include "../TextpressoCentralGlobalDefinitions.h"
#include "xercesc/util/XMLString.hpp"
#include <uima/api.hpp>
#include <uima/xmideserializer.hpp>
#include <cstdio>
#include <fstream>
#include "getbibUtils.h"
#include <boost/filesystem.hpp>
#include <boost/date_time.hpp>



#define TPCAS_2_LINDEX_VERSION "0.9.0"


using namespace boost::filesystem;

void print_who() {
    std::cout << std::endl << "CAS file bib extracter" << std::endl;
    std::cout << "Build Date: " << __DATE__ << std::endl;
    std::cout << "Version: " << TPCAS_2_LINDEX_VERSION << std::endl;
}

void print_help() {
    std::cout << std::endl;
    std::cout << "Usage: getbib [tpcas_file_directory]" << std::endl;
    std::cout << std::endl;
 //   std::cout << "       CASconcumer reads in a directory of tpcas files and adds them to the lucene index(index_location specified by user), if index_location does not exist, it will create one. ";
   // std::cout << std::endl;
    //   std::cout << "       as defined in annotator that is referenced in";
    //   std::cout << std::endl;
    //  //std::cout << "       " << TPCAS2LINDEXDESCRIPTOR;
    //   std::cout << "       " << TPCAS2SINGLEINDEXDESCRIPTOR;
    //   std::cout << std::endl;
}

void addCasFile(const char* pszInput, string indexdescriptor) {


    std::string gzfile(pszInput);
    std::cout << gzfile << std::endl;
    if(gzfile.find("tpcas.gz") == std::string::npos)
        return;
    //    string doneflagpath = "/tmp/indexerdone/"+ gzfile;
    //    cout << "done flag is " << doneflagpath << endl;
    //    if(exists(doneflagpath))
    //    {
    //        return;
    //    }
    //    
    //    std::ofstream doneflag(doneflagpath.c_str());
    //    doneflag << "" << endl;
    //    doneflag.close();

    //cout << "L43 addcas file " << pszInput << endl;
    //const char * descriptor = TPCAS2LINDEXDESCRIPTOR;
    const char * descriptor = indexdescriptor.c_str();



    string tpcasfile = uncompressGzip(gzfile);
    //std::cout << "L52 tpcasfile " << tpcasfile << std::endl;

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

            //std::cout << "L69 consumer" << tpcasfile << std::endl;
            XMLCh* native = XMLString::transcode(tpcasfile.c_str());
            LocalFileInputSource fileIS(native);
            XMLString::release(&native);

            //std::cout << "L71 tpcas " << tpcasfile.c_str() << std::endl;
            uima::XmiDeserializer::deserialize(fileIS, *cas, true);

            std::string filename(tpcasfile);
            //std::cout << "L77 " << filename << std::endl;

            /* process the CAS */

            // ((uima::AnalysisEngine*) pEngine)->processAndOutputNewCASes(*cas);

            ((uima::AnalysisEngine*) pEngine)->process(*cas);

        } catch (uima::Exception e) {
            uima::ErrorInfo errInfo = e.getErrorInfo();
            std::cerr << "Error " << errInfo.getErrorId() << " " << errInfo.getMessage() << std::endl;
            std::cerr << errInfo << std::endl;
        } catch (std::logic_error e) {
            std::cerr << "Logic error" << std::endl;
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

    //const char * descriptor = TPCAS2LINDEXDESCRIPTOR;

    path inputdir(argv[1]); //tpcas file dir
    //string indexpath(argv[2]); //index location
    string indexpath("");
    // string newOradd(argv[3]); // new/add  index option

    //  string indexpath("/home/lyl/Dropbox/work/lucene/cas_index");
    //  string indexdescriptor("/home/lyl/Dropbox/work/textpressocentral/trunk/LuceneIndexing/descriptors/Tpcas2Lindex.xml");



    //    if (!exists(indexpath)) {
    //        cout << "creating index directory " << endl;
    //        create_directories(indexpath);
    //        create_directories(indexpath + "/fulltext");
    //     //   create_directories(indexpath + "/token");
    //        create_directories(indexpath + "/sentence");
    //     //   create_directories(indexpath + "/lexical");
    //        create_directories(indexpath + "/bibliography");
    //    }

//    string inputpath(argv[1]);
//    string donedir = "/tmp/indexerdone/" + inputpath;
//    if (!exists(donedir)) {
//        create_directories(donedir);
//    }


    
    std::string tempDir = getTempDir();
    // newindexflag = tempDir + "/newindexflag";
    bool dir_created = false;
    while (dir_created != true) {
        cout << "dir not created" << endl;
        tempDir = getTempDir();

        dir_created = boost::filesystem::create_directories(tempDir);
    }
    

    //string indexdescriptor(TPCAS2LINDEXDESCRIPTOR);
    //string indexdescriptor(tempDir + "/Tpcas2Lindex.xml");
    string indexdescriptor(tempDir + "/Tpcas2Bib.xml");
    writeToIndexDescriptor(indexpath, indexdescriptor, tempDir); ///write to /run/shm/[tempDir]/Tpcas2Lindex.xml

  directory_iterator end_itr;
    for (directory_iterator dit(inputdir); dit != end_itr; dit++) {
        if (is_regular_file(dit->status())) {

            // cout << "extension " << dit->symlink_status() << endl;
          
                // addCasFile(dit->path());
                cout << "file path is " << dit->path() << endl;
                //addCasFile(dit->path().string().c_str() );
                addCasFile(dit->path().string().c_str(), indexdescriptor);
               

           
        } else if (is_directory(dit->status())) {
            path subdir(dit->path().string().c_str());
            for (directory_iterator dit2(subdir); dit2 != end_itr; dit2++) {

                if (is_regular_file(dit2->status())) {

               
                        addCasFile(dit2->path().string().c_str(), indexdescriptor);
                    
                }

            }

        }


    }

    boost::filesystem::remove(indexdescriptor);
    boost::filesystem::remove(tempDir);

}
