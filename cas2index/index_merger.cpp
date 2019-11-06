/*
 * File:   main.cpp
 * Author: liyuling
 *
 * Created on Dec, 2013
 */

#include "../TextpressoCentralGlobalDefinitions.h"
#include "xercesc/util/XMLString.hpp"
#include "../lucene/CaseSensitiveAnalyzer.h"
#include <uima/api.hpp>
#include <uima/xmideserializer.hpp>
#include <cstdio>
#include <iostream>
#include <lucene++/LuceneHeaders.h>
#include <boost/filesystem.hpp>
#include <boost/date_time.hpp>

//#define TPCAS_2_LINDEX_VERSION "0.9.0"
using namespace std;
using namespace boost::filesystem;
using namespace Lucene;

void print_who() {
    std::cout << std::endl << "Lucene index merger" << std::endl;
    std::cout << "Build Date: " << __DATE__ << std::endl;

}

void print_help() {
    std::cout << std::endl;
    std::cout << "Usage: IndexerMerger [index1][index2][optimization yes|no]" << std::endl;
    std::cout << std::endl;
    std::cout << "it merges [index2] into [index1], after merging, index1 will be optimized if [optimization] = yes";
    std::cout << std::endl;
    std::cout << "both index1 and index2 need to be valid TexpressoCentral index structure(not empty)";
    std::cout << std::endl;
}

void mergeIndex(const string& indexpath1, const string& indexpath2, const string& optimization, bool caseSensitive) {

    //cout << "L138" << endl;
    String IndexDir1 = StringUtils::toString(indexpath1.c_str());
    IndexWriterPtr writer;
    if (caseSensitive) {
        writer = newLucene<IndexWriter>(FSDirectory::open(IndexDir1),
                                        newLucene<CaseSensitiveAnalyzer>(LuceneVersion::LUCENE_30), false, // append
                                        IndexWriter::MaxFieldLengthUNLIMITED);
    } else {
        writer = newLucene<IndexWriter>(FSDirectory::open(IndexDir1),
                                        newLucene<StandardAnalyzer>(LuceneVersion::LUCENE_30), false, // append
                                        IndexWriter::MaxFieldLengthUNLIMITED);
    }
    cout << "maxDoc(): " << writer->maxDoc() << endl;
    //cout << "L143" << endl;
    String IndexDir2 = StringUtils::toString(indexpath2.c_str());
    //wcout << "L146 " << IndexDir2.c_str() << endl;
    FSDirectoryPtr dir2 = FSDirectory::open(IndexDir2);
    Collection<DirectoryPtr> indexes = Collection<DirectoryPtr>::newInstance(0);
    indexes.add(dir2);
    // cout << "L152 size " << indexes.size() << endl;
    writer->addIndexesNoOptimize(indexes);
    //cout<<"L165" << endl;
    if (optimization == "yes") {
        writer->optimize();
    }
    //cout<<"L166" << endl;
    writer->close();
}

int main(int argc, char* argv[]) {
    if (argc < 4) {
        print_who();
        print_help();
        return (-1);
    }

    string indexpath1(argv[1]); //tpcas file dir
    string indexpath2(argv[2]); //index location
    string optimization(argv[3]); //optimize after merge or not

    if (optimization != "yes" && optimization != "no") {
        cout << "optimization flag error" << endl;
        return (-1);
    }

    // lowercase indexes
    if (exists(indexpath1 + "/fulltext") && exists(indexpath2 + "/fulltext")) {
        mergeIndex(indexpath1 + "/fulltext", indexpath2 + "/fulltext", optimization, false);
    }
    if (exists(indexpath1 + "/sentence") && exists(indexpath2 + "/sentence")) {
        mergeIndex(indexpath1 + "/sentence", indexpath2 + "/sentence", optimization, false);
    }
    if (exists(indexpath1 + "/lexical") && exists(indexpath2 + "/lexical")) {
        mergeIndex(indexpath1 + "/lexical", indexpath2 + "/lexical", optimization, false);
    }
    if (exists(indexpath1 + "/bibliography") && exists(indexpath2 + "/bibliography")) {
        mergeIndex(indexpath1 + "/bibliography", indexpath2 + "/bibliography", optimization, false);
    }

    // case sensitive indexes
    if (exists(indexpath1 + "/fulltext_cs") && exists(indexpath2 + "/fulltext_cs")) {
        mergeIndex(indexpath1 + "/fulltext_cs", indexpath2 + "/fulltext_cs", optimization, true);
    }
    if (exists(indexpath1 + "/sentence_cs") && exists(indexpath2 + "/sentence_cs")) {
        mergeIndex(indexpath1 + "/sentence_cs", indexpath2 + "/sentence_cs", optimization, true);
    }
    if (exists(indexpath1 + "/lexical_cs") && exists(indexpath2 + "/lexical_cs")) {
        mergeIndex(indexpath1 + "/lexical_cs", indexpath2 + "/lexical_cs", optimization, true);
    }
    if (exists(indexpath1 + "/bibliography_cs") && exists(indexpath2 + "/bibliography_cs")) {
        mergeIndex(indexpath1 + "/bibliography_cs", indexpath2 + "/bibliography_cs", optimization, true);
    }
}

