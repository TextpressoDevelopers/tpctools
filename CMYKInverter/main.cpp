/* 
 * File:   main.cpp
 * Author: mueller
 *
 * Created on June 20, 2014, 12:38 PM
 */

#include "CMYKModifier.h"
#include <boost/filesystem.hpp>
#include <set>
#include <fstream>

int main(int argc, char * argv[]) {
    //
    boost::filesystem::path p(argv[1]);
    //
    std::set<boost::filesystem::path> files;
    files.clear();
    if (boost::filesystem::exists(p) && boost::filesystem::is_directory(p)) {
        std::copy(boost::filesystem::directory_iterator(p), boost::filesystem::directory_iterator(),
                std::inserter(files, files.end()));
    }
    //
    boost::filesystem::path cmykindex(std::string(argv[1]) + "/" + "cmyk.index");
    std::set<std::string> cmykfiles;
    std::ifstream fi(cmykindex.string().c_str());
    std::string aux;
    while (fi >> aux)
        cmykfiles.insert(aux);
    fi.close();
    //
    for (std::set<boost::filesystem::path>::iterator it = files.begin(); it != files.end(); it++)
        if ((*it).extension().string().compare(".jpg") == 0)
            if (cmykfiles.find((*it).string()) == cmykfiles.end()) {
                CMYKModifier cmykmodifier((*it).string().c_str());
                if (cmykmodifier.IsCMYK())
                    cmykfiles.insert((*it).string());
            }
    //
    std::ofstream fo(cmykindex.string().c_str());
    for (std::set<std::string>::iterator it = cmykfiles.begin(); it != cmykfiles.end(); it++)
        fo << *it << std::endl;
    fo.close();
    return 0;
}
