/**
    Project: textpressocentral
    File name: main.cpp
    
    @author valerio
    @version 1.0 6/5/17.
*/

#include <string>
#include <boost/program_options.hpp>
#include <CImg.h>
#include <boost/filesystem/path.hpp>
#include <boost/filesystem/operations.hpp>

namespace po = boost::program_options;
namespace fs = boost::filesystem;
using namespace std;
using namespace cimg_library;

void convertFile(const string& inputFileName, bool remove) {
    fs::path inputFilePath(inputFileName);
    fs::path outputFilePath = inputFilePath;
    outputFilePath.replace_extension(fs::path("jpg"));
    try {
        CImg<unsigned char> image(inputFilePath.string().c_str());
        image.save(outputFilePath.string().c_str());
        if (remove) {
            fs::remove(inputFilePath);
        }
    } catch (Magick::ErrorCorruptImage) {
        cout << "cannot convert corrupted file " << inputFileName << endl;
    }
}

int main(int argc, char* argv[]) {

    po::options_description desc("options");
    po::positional_options_description p;
    po::variables_map vm;

    bool remove = false;
    bool recursive = false;
    string startDir;
    string inputFileName;

    try {

        desc.add_options()
                ("help,h", "produce help message")
                ("input-file,i", po::value<string>(&inputFileName)->required(), "input file or directory")
                ("delete,d", "delete original ppm files")
                ("recursive,r", "apply conversion recursively");


        p.add("input-file", -1);
        po::store(po::command_line_parser(argc, argv).
                options(desc).positional(p).run(), vm);
        po::notify(vm);

        if (vm.count("help")) {
            cout << desc << endl;
            return 1;
        }

        if (vm.count("delete")) {
            remove = true;
        }

        if (vm.count("recursive")) {
            recursive = true;
            startDir = inputFileName;
        }
    } catch(std::exception& e) {
        if (vm.count("help")) {
            cout << desc << endl;
            return (EXIT_SUCCESS);
        }
        std::cerr << "Error: " << e.what() << "\n";
        return (EXIT_FAILURE);
    }

    if (recursive) {
        fs::recursive_directory_iterator dir_end;
        fs::recursive_directory_iterator dir(startDir);
        while (dir != dir_end) {
            fs::path _path(*dir);
            ++dir;
            if (!fs::is_directory(_path) && _path.extension().string() == ".ppm") {
                convertFile(_path.string(), remove);
            }
        }
    } else {
        convertFile(inputFileName, remove);
    }

    return (EXIT_SUCCESS);
}