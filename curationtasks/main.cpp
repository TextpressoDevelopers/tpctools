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
#include <textpresso/DataStructures.h>
#include <IndexManager.h>
#include <boost/regex.hpp>


using namespace std;
using namespace tpc::index;

int main(int argc, char * argv[]) {
    cmdline::parser p;
    p.add<std::string> ("keyword", 'k', "keyword(s)", false);
    p.add<std::string> ("exclusionkeyword", 'e', "keyword(s) to be excluded", false);
    p.add<std::string> ("category", 'c', "one or more categories, separated by comma", false);
    p.add<std::string>("literature", 'l', "one or more literatures, separated by comma", false);
    p.add<std::string>("year", 'y', "filter on year", false);
    p.add<std::string>("author", 'a', "filter on author", false);
    p.add<std::string>("id", 'i', "filter on publication id", false);
    p.add<std::string>("journal", 'j', "filter on journal name", false);
    p.add<std::string>("scope", 's', "search scope (sentence or document)", false, "sentence");
    p.add("sortbyyear", 'o', "sort output by year");
    p.add("boolorcategories", 'b', "when several categories are present, OR them (AND is default)");
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
    Query q = Query();
    q.keyword = p.get<std::string>("keyword");
    q.exclude_keyword = p.get<std::string>("exclusionkeyword");
    boost::split(q.categories, p.get<std::string>("category"), boost::is_any_of(","));
    boost::split(q.literatures, p.get<std::string>("literature"), boost::is_any_of(","));
    q.year = p.get<std::string>("year");
    q.author = p.get<std::string>("author");
    q.accession = p.get<std::string>("id");
    q.journal = p.get<std::string>("journal");
    q.type = p.get<std::string>("scope") == "sentence" ? QueryType::sentence : QueryType::document;
    q.sort_by_year = p.exist("sortbyyear");
    q.categories_and_ed = !p.exist("boolorcategories");
    std::string printoptions(p.get<std::string>("print"));

    IndexManager indexManager = IndexManager(INDEX_ROOT_LOCATION, CAS_ROOT_LOCATION, true);
    SearchResults searchResults = indexManager.search_documents(q);

    vector<string> txt_output;
    if (printoptions.find("q") != std::string::npos) {
        txt_output.push_back("[Query]");
        string scope = q.type == QueryType::document ? "document" : "sentence";
        txt_output.push_back("scope: " + scope);
        for (auto& lit : q.literatures) {
            txt_output.push_back("literature: " + lit);
        }
        txt_output.push_back(q.get_query_text());
    }
    if (printoptions.find("s") != std::string::npos) {
        txt_output.push_back("");
        txt_output.push_back("[Search Summary]");
        txt_output.push_back("documents: " + to_string(searchResults.hit_documents.size()));
        txt_output.push_back("hits: " + to_string(searchResults.total_num_sentences));
    }
    vector<DocumentDetails> documentsDetails;
    if (printoptions.find("r") != std::string::npos) {
        set<string> exclude_doc_fields;
        set<string> exclude_sent_fields;
        if (q.type == QueryType::sentence) {
            exclude_doc_fields = {"fulltext_compressed"};
        } else {
            exclude_sent_fields = {"sentence_compressed"};
        }
        documentsDetails = indexManager.get_documents_details(searchResults.hit_documents, q.sort_by_year, true,
                                                              DOCUMENTS_FIELDS_DETAILED, SENTENCE_FIELDS_DETAILED,
                                                              exclude_doc_fields, exclude_sent_fields);
        for (auto& result : documentsDetails) {
            txt_output.push_back("");
            txt_output.push_back("[Result]");
            txt_output.push_back("score: " + to_string(result.score));
            txt_output.push_back("accession: " + result.accession);
            txt_output.push_back("title: " + result.title);
            txt_output.push_back("author: " + result.author);
            txt_output.push_back("journal: " + result.journal);
            txt_output.push_back("year: " + result.year);
            txt_output.push_back("abstract: " + result.abstract);
            txt_output.push_back("type: " + result.type);
            if (q.type == QueryType::document) {
                txt_output.push_back("hit: " + result.fulltext);
            } else {
                for (auto& hit_sentence : result.sentences_details) {
                    txt_output.push_back("hit: " + hit_sentence.sentence_text);
                }
            }
        }
    }
    // TODO: split in two programs, one for searches and the second one for transforming the output

    // post-processing
    if (p.get<std::string>("postprocessing") == "unpublished") {
        boost::regex hit("^hit: .+");
        boost::regex unpublished(".*[uU]npublished.*");
        boost::regex datanotshown(".*[dD]ata\\s[nN]ot\\s[sS]hown.*");
        std::vector<std::string> oneresult;
        bool keep(false);
        for (const auto& line : txt_output) {
            oneresult.push_back(line);
            oneresult.back() = boost::regex_replace(oneresult.back(), boost::regex("\\s+"), " ");
            if (boost::regex_match(line, hit))
                if (boost::regex_match(line, unpublished) || boost::regex_match(line, datanotshown))
                    keep = true;
            if ((line).empty()) {
                if (keep)
                    for (auto itc = oneresult.begin(); itc != oneresult.end(); itc++)
                        if (!boost::regex_match(*itc, hit))
                            cout << *itc << endl;
                        else if (boost::regex_match(*itc, unpublished) || boost::regex_match(*itc, datanotshown))
                            cout << *itc << endl;
                oneresult.clear();
                keep = false;
            }
        }
    } else if (p.get<std::string>("postprocessing") == "daniela") {
        boost::regex unpublished("([uU]npublished)");
        boost::regex datanotshown("([dD]ata\\s+[nN]ot\\s+[sS]hown)");
        boost::regex wbpaper("(WBPaper\\d+)");
        boost::regex matchunpublished(".*[uU]npublished.*");
        boost::regex matchdatanotshown(".*[dD]ata\\s+[nN]ot\\s+[sS]hown.*");
        boost::regex matchwbpaper(".*WBPaper.*");
        boost::regex matchaccession("accession:.*");
        cout << "<html><body>" << endl;
        bool diffable(false);
        bool keep(true);
        std::vector<std::string> oneresult;
        for (const auto& line : txt_output) {
            string aux = line;
            if (aux.compare("[Result]") == 0) {
                oneresult.push_back("<!-HTMLDIFFSTART->");
                diffable = true;
                keep = false;
            }
            if (diffable) {
                if (boost::regex_match(aux, matchunpublished) || boost::regex_match(aux, matchdatanotshown)) {
                    keep = true;
                    aux = boost::regex_replace(aux, unpublished, "<b>\\1</b>");
                    aux = boost::regex_replace(aux, datanotshown, "<b>\\1</b>");
                }
                if (boost::regex_match(aux, matchwbpaper) && boost::regex_match(aux, matchaccession))
                    aux = boost::regex_replace(aux, wbpaper, "<b>\\1</b>");
            }
            oneresult.push_back(aux + "<br>");
            oneresult.back() = boost::regex_replace(oneresult.back(), boost::regex("\\s+"), " ");
            if (aux.empty()) {
                if (diffable) {
                    oneresult.push_back("<!-HTMLDIFFEND->");
                    diffable = false;
                    if (!keep) {
                        keep = true;
                        oneresult.clear();
                    }
                }
                for (const auto& outline : oneresult) {
                    cout << outline << endl;
                }
                oneresult.clear();
            }
        }
        for (auto& line : oneresult) {
            cout << line << endl;
        }
        cout << "</body></html>" << endl;
    }
    else {
        for (auto& line : txt_output) {
            cout << line << endl;
        }
    }
    return 0;
}
