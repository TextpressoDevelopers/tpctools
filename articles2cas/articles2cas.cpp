/**
    Project: textpressocentral
    File name: articles2cas.cpp
    
    @author valerio
    @version 1.0 7/30/17.
 */

#include <CASManager.h>
#include <boost/program_options/options_description.hpp>
#include <boost/program_options.hpp>
#include <iostream>
#include <boost/filesystem.hpp>
#include <fstream>
#include "Utils.h"

using namespace std;
using namespace boost::filesystem;
namespace po = boost::program_options;
using namespace tpc::cas;

void convert_dir_recursively(const string& inputDir, const string& outputDir, const string& literature,
        const set<string>& filelist_set, const set<string>& dirlist_set, FileType fileType,
        bool use_parent_dir_as_outname) {
    for (directory_iterator dit(inputDir); dit != directory_iterator(); ++dit) {
        if ((is_regular_file(*dit) && (dit->path().filename().string().find(".nxml.gz") != string::npos ||
                dit->path().filename().string().find(".pdf") != string::npos ||
                dit->path().filename().string().find(".txt") != string::npos)) && ((filelist_set.empty() ||
                filelist_set.find(dit->path().filename().string()) != filelist_set.end()) &&
                (dirlist_set.empty() || dirlist_set.find(dit->path().parent_path().filename().string()) !=
                dirlist_set.end()))) {
            if (fileType == FileType::xml) {
                cout << dit->path().string() << endl;
                try {
                    string decomp_file = Utils::decompress_gzip(dit->path().string(),
                            dit->path().parent_path().string());
                    CASManager::convert_raw_file_to_cas1(decomp_file, fileType, outputDir, use_parent_dir_as_outname);
                    if (boost::filesystem::exists(decomp_file)) {
                        try {
                            boost::filesystem::remove(decomp_file);
                        } catch (boost::filesystem::filesystem_error e) {
                            std::cerr << "Error " << e.what() << std::endl;
                        }
                    }
                } catch (const std::exception &e) {
                    std::cerr << "Error " << e.what() << std::endl;
                }
            } else if (fileType == FileType::tai) {
                if (dit->path().filename().string().find(".pdf") != string::npos) {
                    cout << dit->path().string() << endl;
                    CASManager::convert_raw_file_to_cas1(dit->path().string(), fileType, outputDir,
                            use_parent_dir_as_outname);
                }
            } else {
                cout << dit->path().string() << endl;
                CASManager::convert_raw_file_to_cas1(dit->path().string(), fileType, outputDir,
                        use_parent_dir_as_outname);
            }
        } else if (is_directory(*dit) && dit->path().filename().string() != "images") {
            convert_dir_recursively(dit->path().string(), outputDir, literature, filelist_set, dirlist_set, fileType,
                    use_parent_dir_as_outname);
        }
    }
}

int main(int argc, const char* argv[]) {
    po::options_description desc("options");
    po::positional_options_description p;
    po::variables_map vm;

    // arguments
    string inputDir;
    string outputDir;
    int fileType;
    string filelist;
    string dirlist;

    try {
        desc.add_options()
                ("help,h", "produce help message")
                ("articles-input-directory,i", po::value<string>(&inputDir)->required(),
                "input directory containing articles")
                ("cas-output-directory,o", po::value<string>(&outputDir)->required(),
                "directory where to write cas files")
                ("input-files-type,t", po::value<int>(&fileType)->default_value(1),
                "type of files to process. 1 for pdf, 2 for xml, 3 for text")
                ("dir-list,l", po::value<string>(&dirlist)->default_value(""),
                "optional list of directory names containing the final files to be processed. Other "
                "directories are ignored")
                ("file-list,L", po::value<string>(&filelist)->default_value(""),
                "optional list of file names to be processed. Other files are ignored")
                ("use_parent_dir_as_outname,p", po::bool_switch()->default_value(false), "Use parent dir name instead "
                "of file name as output name for the cas file");
        p.add("articles-input-directory", 1);
        p.add("cas-output-directory", 1);
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

    FileType ft;
    if (fileType == 1) {
        ft = FileType::pdf;
    } else if (fileType == 2) {
        ft = FileType::xml;
    } else if (fileType == 3) {
        ft = FileType::txt;
    } else if (fileType == 4) {
        ft = FileType::tai;
    }
    if (is_directory(inputDir)) {
        path p(inputDir);
        string literature = p.filename().string();
        create_directories(outputDir);
        std::fstream f;
        f.open(dirlist, std::fstream::in);
        string line;
        set<string> dirlist_set;
        while (getline(f, line)) {
            dirlist_set.insert(line);
        }
        f.close();
        f.open(filelist, std::fstream::in);
        string line2;
        set<string> filelist_set;
        while (getline(f, line)) {
            filelist_set.insert(line);
        }
        f.close();
        convert_dir_recursively(inputDir, outputDir, literature, filelist_set, dirlist_set, ft,
                vm["use_parent_dir_as_outname"].as<bool>());
    }
}
