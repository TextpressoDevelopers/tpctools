/**
    Project: textpressocentral
    File name: update_corpus_counter.cpp
    
    @author valerio
    @version 1.0 10/06/17.
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
    string casDir;

    try {
        desc.add_options()
                ("help,h", "produce help message")
                ("index_dir,i", po::value<string>(&inputDir)->required(),
                 "index directory where to read the data and store the counter file")
                ("cas_dir,c", po::value<string>(&casDir)->required(),
                 "cas directory that has tpcas-2 files");
        p.add("cas-input-directory", -1);
        po::store(po::command_line_parser(argc, argv).options(desc).positional(p).run(), vm);
        po::notify(vm);

        if (vm.count("help")) {
            cout << desc << endl;
            return 1;
        }
    } catch (std::exception &e) {
        if (vm.count("help")) {
            cout << desc << endl;
            return (EXIT_SUCCESS);
        }
        std::cerr << "Error: " << e.what() << "\n";
        return (EXIT_FAILURE);
    }
    tpc::index::IndexManager indexManager(inputDir, casDir, false, false);
    indexManager.calculate_and_save_corpus_counter();
}
