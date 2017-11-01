/* 
 * File:   main.cpp
 * Author: mueller
 *
 * Created on February 9, 2017, 11:11 AM
 */

#include "cmdline.h"
#include "BatchSearch.h"
#include "Postprocessing.h"
#include <set>
#include <boost/algorithm/string.hpp>

int main(int argc, char * argv[]) {
    cmdline::parser p;
    //
    std::string keyword("");
    p.add<std::string> ("keyword", 'k', "keyword(s)", false);
    //
    std::string keywordnot("");
    p.add<std::string> ("exclusionkeyword", 'e', "keyword(s) to be excluded", false);
    //
    std::set<std::string> pickedcat;
    p.add<std::string> ("category", 'c', "one or more categories, separated by comma", false);
    //
    std::set<std::string> pickedliterature;
    p.add<std::string>("literature", 'l', "one or more literatures, separated by comma", false);
    //
    std::map<std::string, std::string> filters;
    p.add<std::string>("year", 'y', "filter on year", false);
    p.add<std::string>("author", 'a', "filter on author", false);
    p.add<std::string>("id", 'i', "filter on publication id", false);
    p.add<std::string>("journal", 'j', "filter on journal name", false);
    //
    std::string scope("sentence");
    p.add<std::string>("scope", 's', "search scope (sentence or document)", false, "sentence");
    //
    bool sortbyyear(false);
    p.add("sortbyyear", 'o', "sort output by year");
    //
    bool categoriesanded(true);
    p.add("boolorcategories", 'b', "when several categories are present, OR them (AND is default)");
    //
    p.add<std::string>("print", 'p', "print options q)uery s)ummary r)esult", false, "qsr");
    p.add<std::string>("postprocessing", 'r', "post process result output with specified condition", false);
    p.set_program_name("curationtask");
    p.footer(
            "\n\n"
            "Performs command line TPC searches and curation tasks.\n"
            "Search must have at least one keyword or category.\n"
            );
    if (argc < 3) {
        std::cerr << p.usage() << std::endl;
        return -1;
    }
    if (p.parse(argc, argv) == 0) {
        std::cerr << "Error:" << p.error() << std::endl
                << p.usage() << std::endl;
        return -1;
    }
    keyword = p.get<std::string>("keyword");
    keywordnot = p.get<std::string>("exclusionkeyword");
    std::string aux = p.get<std::string>("category");
    if (!aux.empty()) {
        std::vector<std::string> splits;
        boost::split(splits, aux, boost::is_any_of(","));
        while (!splits.empty()) {
            boost::trim(splits.back());
            pickedcat.insert(splits.back());
            splits.pop_back();
        }
    }
    aux = p.get<std::string>("literature");
    if (!aux.empty()) {
        std::vector<std::string> splits;
        boost::split(splits, aux, boost::is_any_of(","));
        while (!splits.empty()) {
            boost::trim(splits.back());
            pickedliterature.insert(splits.back());
            splits.pop_back();
        }
    }
    aux = p.get<std::string>("year");
    if (!aux.empty()) filters["year"] = aux;
    aux = p.get<std::string>("author");
    if (!aux.empty()) filters["author"] = aux;
    aux = p.get<std::string>("id");
    if (!aux.empty()) filters["id"] = aux;
    aux = p.get<std::string>("journal");
    if (!aux.empty()) filters["journal"] = aux;
    scope = p.get<std::string>("scope");
    sortbyyear = p.exist("sortbyyear");
    categoriesanded = !p.exist("boolorcategories");
    std::string printoptions(p.get<std::string>("print"));
    try {
        BatchSearch * bs = new BatchSearch(scope, keyword, keywordnot,
                categoriesanded, pickedliterature, pickedcat, filters);
        std::vector<std::string> o;
        if (printoptions.find("q") != std::string::npos) {
            std::vector<std::string>i(bs->query());
            o.insert(o.end(), i.begin(), i.end());
        }
        if (printoptions.find("s") != std::string::npos) {
            std::vector<std::string>i(bs->summary());
            o.insert(o.end(), i.begin(), i.end());
        }
        if (printoptions.find("r") != std::string::npos) {
            std::vector<std::string>i(bs->result());
            o.insert(o.end(), i.begin(), i.end());
        }
        if (!o.empty()) {
            if (p.get<std::string>("postprocessing").empty()) {
                for (std::vector<std::string>::iterator it = o.begin(); it != o.end(); it++)
                    std::cout << *it << std::endl;
            } else {
                Postprocessing * pp = new Postprocessing(p.get<std::string>("postprocessing"), o);
                std::vector<std::string> oo(pp->output());
                for (std::vector<std::string>::iterator it = oo.begin(); it != oo.end(); it++)
                    std::cout << *it << std::endl;
            }
        }
    } catch (std::string & errorMessage) {
        std::cerr << errorMessage << std::endl;
        return -1;
    }
    return 0;
}
