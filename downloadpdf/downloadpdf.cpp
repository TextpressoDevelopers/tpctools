/* 
 * File:   downloadpdf.cpp
 * Author: mueller
 *
 * Created on May 18, 2021, 6:49 PM
 */

#include <boost/program_options.hpp>
#include <boost/filesystem.hpp>
#include <boost/foreach.hpp>
#include <boost/property_tree/json_parser.hpp>
#include <boost/algorithm/string/replace.hpp>
#include <curl/curl.h>
#include <iostream>
#include <xercesc/parsers/XercesDOMParser.hpp>
#include <xercesc/dom/DOM.hpp>
#include <xercesc/sax/HandlerBase.hpp>
#include <xercesc/util/XMLString.hpp>
#include <xercesc/util/PlatformUtils.hpp>


using namespace std;
using namespace xercesc;
namespace ba = boost::algorithm;
namespace fs = boost::filesystem;
namespace downloadpdf {

    void join(DOMNodeList* list, string c, string& s) {
        s.clear();
        for (int i = 0; i < list->getLength(); i++) {
            s += XMLString::transcode(list->item(i)->getTextContent());
            if (i != list->getLength() - 1) s += c;
        }
    }

    string parseXML(const char* xmlFile) {
        string ret("");
        try {
            XMLPlatformUtils::Initialize();
        } catch (const XMLException& toCatch) {
            char* message = XMLString::transcode(toCatch.getMessage());
            cout << "Error during initialization! :\n"
                    << message << "\n";
            XMLString::release(&message);
            return ret;
        }

        XercesDOMParser* parser = new XercesDOMParser();
        parser->setValidationScheme(XercesDOMParser::Val_Always);
        parser->setDoNamespaces(true); // optional

        ErrorHandler* errHandler = (ErrorHandler*) new HandlerBase();
        parser->setErrorHandler(errHandler);

        try {
            parser->parse(xmlFile);
        } catch (const XMLException& toCatch) {
            char* message = XMLString::transcode(toCatch.getMessage());
            cout << "Exception message is: \n"
                    << message << "\n";
            XMLString::release(&message);
            return ret;
        } catch (const DOMException& toCatch) {
            char* message = XMLString::transcode(toCatch.msg);
            cout << "Exception message is: \n"
                    << message << "\n";
            XMLString::release(&message);
            return ret;
        } catch (...) {
            cout << "Unexpected Exception \n";
            return ret;
        }
        DOMDocument* doc = parser->adoptDocument();
        //
        XMLCh* temp = XMLString::transcode("dc:creator");
        DOMNodeList* list = doc->getElementsByTagName(temp);
        string line;
        join(list, "; ", line);
        ret = "author|" + line + "\n";
        //
        temp = XMLString::transcode("dc:identifier");
        list = doc->getElementsByTagName(temp);
        join(list, "; ", line);
        ret += "accession|" + line + "\n";
        //
        temp = XMLString::transcode("dc:subject");
        list = doc->getElementsByTagName(temp);
        join(list, "; ", line);
        ret += "type|" + line + "\n";
        //
        temp = XMLString::transcode("dc:title");
        list = doc->getElementsByTagName(temp);
        join(list, "; ", line);
        ret += "title|" + line + "\n";
        //
        temp = XMLString::transcode("dc:source");
        list = doc->getElementsByTagName(temp);
        join(list, "; ", line);
        ret += "journal|" + line + "\n";
        //
        ret += "citation| not available\n";
        //
        temp = XMLString::transcode("dc:date");
        list = doc->getElementsByTagName(temp);
        join(list, "; ", line);
        ret += "year|" + line + "\n";
        //
        //
        temp = XMLString::transcode("dc:description");
        list = doc->getElementsByTagName(temp);
        join(list, "; ", line);
        ret += "abstract|" + line + "\n";
        //        
        XMLString::release(&temp);
        if (doc) doc->release();
        ////
        delete parser;
        delete errHandler;
        return ret;
    }

    size_t write_data(void *ptr, size_t size, size_t nmemb, FILE *stream) {
        size_t written;
        written = fwrite(ptr, size, nmemb, stream);
        return written;
    }

    void downloadFile(const char* url, const char* outfilename) {
        CURL *curl;
        FILE *fp;
        CURLcode res;
        curl = curl_easy_init();
        if (curl) {
            fp = fopen(outfilename, "wb");
            curl_easy_setopt(curl, CURLOPT_URL, url);
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_data);
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, fp);
            curl_easy_setopt(curl, CURLOPT_VERBOSE, 0L);
            curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
            res = curl_easy_perform(curl);
            curl_easy_cleanup(curl);
            fclose(fp);
        }
    }

    void saveString2file(const char* filename, const string &s) {
        ofstream ofs(filename);
        if (ofs.is_open()) {
            ofs << s;
            ofs.close();
        } else {
            cerr << "Unable to open file " << filename << endl;
        }
    }

    void getMetadata(string pmcid, const char* outfilename) {
        ba::replace_first(pmcid, "PMC", "");
        string baseurl("https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi"
                "?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:%s&metadataPrefix=oai_dc");
        ba::replace_first(baseurl, "%s", pmcid);
        string destination("/tmp/PMC" + pmcid);
        downloadFile(baseurl.c_str(), destination.c_str());
        saveString2file(outfilename, parseXML(destination.c_str()));
        remove(destination.c_str());
    }

    void downloadLiteratures(const string urlParameter,
            const string downloadDir,
            const multimap<string, string> &lits) {
        for (auto x : lits) {
            string literature((fs::path(x.first).filename().string()));
            string url(urlParameter);
            ba::replace_first(url, "%s", x.second);
            string dlDir(downloadDir + "/" + literature + "/" + x.second);
            if (!fs::exists(dlDir)) fs::create_directories(dlDir);
            string destination(dlDir + "/" + x.second + ".pdf");
            string bibfile(dlDir + "/" + x.second + ".bib");
            if (!fs::exists(destination)) {
                cerr << destination << endl;
                downloadFile(url.c_str(), destination.c_str());
                sleep(1 + rand() % 8);
            }
            if (!fs::exists(bibfile)) {
                cerr << bibfile << endl;
                getMetadata(x.second, bibfile.c_str());
                sleep(1 + rand() % 2);
            }
        }
    }

    void loadLiteratures(const string &literaturelists,
            multimap<string, string> &literatures) {
        literatures.clear();
        fs::path pDir(literaturelists);
        fs::directory_iterator iter(pDir), eod;
        vector<string> aux;
        aux.clear();
        BOOST_FOREACH(fs::path const& i, make_pair(iter, eod))
        if (is_regular_file(i))
            aux.push_back(i.string());
        for (auto x : aux) {
            ifstream ifsfilelist(x);
            if (ifsfilelist.is_open()) {
                string file;
                while (getline(ifsfilelist, file))
                    literatures.insert(make_pair(x, file));
                ifsfilelist.close();
            } else {
                cerr << "Unable to open file " << x << std::endl;
            }
        }
    }
}

/*
 * 
 */

namespace dp = downloadpdf;

int main(int argc, char** argv) {
    int ret(EXIT_SUCCESS);
    srand(NULL);
    boost::program_options::options_description desc("options");
    boost::program_options::variables_map vm;
    boost::property_tree::ptree inputtree;
    // arguments
    // can set some default here
    string jsonfile("input.json");
    desc.add_options()
            ("help,h", "produce help message")
            ("jsonfile,j", boost::program_options::value<string>(&jsonfile),
            "name of input json file")
            ;
    try {
        boost::program_options::store(boost::program_options::parse_command_line(argc, argv, desc), vm);
        if (vm.count("help")) {
            cout << argv[0] << " ";
            cout << "Build date:  " << __DATE__ << endl;
            cout << desc << endl;
            return EXIT_FAILURE;
        }
        boost::program_options::notify(vm);
        boost::property_tree::read_json(jsonfile, inputtree);
    } catch (exception &e) {
        cerr << "Error: " << e.what() << "\n";
        return (EXIT_FAILURE);
    }
    string urlParameter = inputtree.get<string>("URL parameter",
            "https://www.ncbi.nlm.nih.gov/pmc/articles/%s/pdf/");
    string downloadList = inputtree.get<string>("Download list",
            "/data/textpresso/etc/download.lst");
    string literatureLists = inputtree.get<string>("Literature lists",
            "/data/textpresso/etc/literatures");
    string downloadDir = inputtree.get<string>("Download dir",
            "/data/textpresso/raw_files/pdf");
    cout << "URL parameter : " << urlParameter << endl;
    cout << "Download list : " << downloadList << endl;
    cout << "Literature lists : " << literatureLists << endl;
    multimap<string, string> lits;
    dp::loadLiteratures(literatureLists, lits);
    dp::downloadLiteratures(urlParameter, downloadDir, lits);
    return ret;
}

