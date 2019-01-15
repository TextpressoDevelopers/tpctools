/**
    Project: textpressocentral
    File name: cas2index.cpp
    
    @author valerio
    @version 1.0 7/30/17.
*/

#include "IndexManager.h"
#include <boost/program_options/options_description.hpp>
#include <boost/program_options.hpp>
#include <boost/algorithm/string/split.hpp>
#include <boost/algorithm/string.hpp>

using namespace std;
using namespace boost::filesystem;
namespace po = boost::program_options;

int main(int argc, const char* argv[]) {
    po::options_description desc("options");
    po::positional_options_description p;
    po::variables_map vm;

    // arguments
    string inputDir;
    path inputdir;
    string indexpath;
    string fileList;
    string removeList;
    string onlyFilesList;
    int numPapersPerIndex;
    bool external;

    try {
        desc.add_options()
                ("help,h", "produce help message")
                ("cas-input-directory,i", po::value<string>(&inputDir)->required(),
                 "input directory containing cas files")
                ("index-output-directory,o", po::value<string>(&indexpath)->required(),
                 "directory where to write index")
                ("subindex-size,s", po::value<int>(&numPapersPerIndex)->default_value(50000),
                 "maximum number of paper per sub-index")
                ("add-files,a", po::value<string>(&fileList),
                 "add files listed in the provided file to the existing indices")
                ("file-list,f", po::value<string>(&onlyFilesList), "create index using only the files provided in the "
                        "list")
                ("external,e", po::bool_switch(&external)->default_value(false), "Create external index")
                ("remove,r", po::value<string>(&removeList));
        p.add("cas-input-directory", 1);
        p.add("index-output-directory", 1);
        po::store(po::command_line_parser(argc, argv).options(desc).positional(p).run(), vm);
        po::notify(vm);

        if (vm.count("help")) {
            cout << desc << endl;
            return 1;
        }
        if (vm.count("index-output-directory")) {
            inputdir = path(inputDir);
        }
    } catch (std::exception &e) {
        if (vm.count("help")) {
            cout << desc << endl;
            return (EXIT_SUCCESS);
        }
        std::cerr << "Error: " << e.what() << "\n";
        return (EXIT_FAILURE);
    }
    tpc::index::IndexManager indexManager(indexpath, inputDir, false, external);
    if (!fileList.empty()) {
        std::ifstream infile(fileList);
        string filename;
        while (std::getline(infile, filename))
        {
            // TODO check if files are removed (also from bdb)
            indexManager.remove_file_from_index(filename);
            indexManager.add_file_to_index(inputDir + "/" + filename, numPapersPerIndex);
        }
        indexManager.calculate_and_save_corpus_counter();
    } else if (!removeList.empty()) {
        std::ifstream infile(removeList);
        string filename;
        while (std::getline(infile, filename))
        {
            // TODO check if files are removed (also from bdb)
            indexManager.remove_file_from_index(filename);
        }
        indexManager.calculate_and_save_corpus_counter();
    }
    else {
        std::fstream f;
        f.open(onlyFilesList, std::fstream::in);
        string line;
        set<string> filelist_set;
        while (getline(f, line)) {
            filelist_set.insert(line);
        }
        indexManager.create_index_from_existing_cas_dir(inputDir, filelist_set, numPapersPerIndex);
    }
}
