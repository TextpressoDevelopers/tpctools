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
#include <thread>


using namespace std;
using namespace xercesc;
namespace ba = boost::algorithm;
namespace fs = boost::filesystem;
namespace downloadpdf {

    void join(DOMNodeList* list, string c, string& s) {
        s.clear();
        for (XMLSize_t i = 0; i < list->getLength(); i++) {
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
            cerr << "parseXML: Exception message is: \n"
                    << message << "\n";
            XMLString::release(&message);
            return ret;
        } catch (const DOMException& toCatch) {
            char* message = XMLString::transcode(toCatch.msg);
            cerr << "parseXML: Exception message is: \n"
                    << message << "\n";
            XMLString::release(&message);
            return ret;
        } catch (...) {
            cerr << "parseXML: Unexpected Exception \n";
            return ret;
        }
        DOMDocument* doc = parser->adoptDocument();
        //
        XMLCh *temp = XMLString::transcode("OAI-PMH");
        DOMNodeList *list = doc->getElementsByTagName(temp);
        bool is_oai_pmh = list->getLength() > 0;
        temp = XMLString::transcode("PubmedArticleSet");
        list = doc->getElementsByTagName(temp);
        bool is_pubmedArticleSet = list->getLength() > 0;
        //
        if (is_oai_pmh) {
            temp = XMLString::transcode("dc:creator");
            list = doc->getElementsByTagName(temp);
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
            temp = XMLString::transcode("dc:description");
            list = doc->getElementsByTagName(temp);
            join(list, "; ", line);
            ret += "abstract|" + line + "\n";
            //
        } else if (is_pubmedArticleSet) {
            temp = XMLString::transcode("LastName");
            list = doc->getElementsByTagName(temp);
            temp = XMLString::transcode("ForeName");
            DOMNodeList *auxlist = doc->getElementsByTagName(temp);
            string line;
            for (XMLSize_t i = 0; i < list->getLength(); i++) {
                line += XMLString::transcode(list->item(i)->getTextContent());
                line += " ";
                if (auxlist->getLength() > i)
                    line += XMLString::transcode(auxlist->item(i)->getTextContent());
                if (i != list->getLength() - 1) line += "; ";
            }
            ret = "author|" + line + "\n";
            //
            temp = XMLString::transcode("PMID");
            list = doc->getElementsByTagName(temp);
            join(list, "; ", line);
            ret += "accession|" + line + "\n";
            //
            temp = XMLString::transcode("PublicationType");
            list = doc->getElementsByTagName(temp);
            join(list, "; ", line);
            ret += "type|" + line + "\n";
            //
            temp = XMLString::transcode("ArticleTitle");
            list = doc->getElementsByTagName(temp);
            join(list, "; ", line);
            ret += "title|" + line + "\n";
            //
            temp = XMLString::transcode("Title");
            list = doc->getElementsByTagName(temp);
            join(list, "; ", line);
            ret += "journal|" + line + "\n";
            //
            temp = XMLString::transcode("JournalIssue");
            list = doc->getElementsByTagName(temp);
            line.clear();
            if (list->getLength() > 0) {
                DOMNodeList *children = list->item(0)->getChildNodes();
                if (children->getLength() > 1) {
                    line += XMLString::transcode(children->item(0)->getNodeName()) + string(" ");
                    line += XMLString::transcode(children->item(0)->getTextContent()) + string(" ");
                    line += XMLString::transcode(children->item(1)->getNodeName()) + string(" ");
                    line += XMLString::transcode(children->item(1)->getTextContent());
                }
            } else
                line = "not available";
            ret += "citation|" + line + "\n";
            //
            temp = XMLString::transcode("PubDate");
            list = doc->getElementsByTagName(temp);
            line.clear();
            if (list->getLength() > 0) {
                DOMNodeList *children = list->item(0)->getChildNodes();
                for (XMLSize_t i = 0; i < children->getLength(); i++) {
                    line += XMLString::transcode(children->item(i)->getTextContent());
                    if (i != children->getLength() - 1) line += "-";
                }
            }
            ret += "year|" + line + "\n";
            //
            temp = XMLString::transcode("Abstract");
            list = doc->getElementsByTagName(temp);
            join(list, "; ", line);
            ret += "abstract|" + line + "\n";
        }
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

    CURLcode downloadFile(const char* url, const char* outfilename) {
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
            curl_easy_setopt(curl, CURLOPT_USERAGENT, "Firefox/89.0");
            res = curl_easy_perform(curl);
            curl_easy_cleanup(curl);
            fclose(fp);
        }
        return res;
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

    void getMetadata(const string& metaUrlParameter, string id, const char* outfilename) {
        ba::replace_first(id, "PMC", "");
        string baseurl(metaUrlParameter);
        ba::replace_first(baseurl, "%s", id);
        string destination("/tmp/" + id);
        CURLcode cc = downloadFile(baseurl.c_str(), destination.c_str());
        if (cc != CURLcode::CURLE_OK)
            cerr << "Error downloading meta data! " << curl_easy_strerror(cc) << endl;
        string x(parseXML(destination.c_str()));
        if (!x.empty())
            saveString2file(outfilename, x);
        remove(destination.c_str());
    }

    void processEntry(const string lit, const string file, const string pdfUrlParameter,
            const string metaUrlParameter, const string downloadDir, const bool bibonly) {
        if (!file.empty()) {
            string literature((fs::path(lit).filename().string()));
            string url(pdfUrlParameter);
            ba::replace_first(url, "%s", file);
            string dlDir(downloadDir + "/" + literature + "/" + file);
            if (!fs::exists(dlDir)) fs::create_directories(dlDir);
            string destination(dlDir + "/" + file + ".pdf");
            string bibfile(dlDir + "/" + file + ".bib");
            if (!fs::exists(destination))
                if (!bibonly) {
                    cerr << destination << endl;
                    CURLcode cc = downloadFile(url.c_str(), destination.c_str());
                    if (cc != CURLcode::CURLE_OK)
                        std::cerr << "Error downloading pdf file! " << curl_easy_strerror(cc) << std::endl;
                }
            if (!fs::exists(bibfile)) {
                cerr << bibfile << endl;
                getMetadata(metaUrlParameter, file, bibfile.c_str());
            }
        }
    }

    void downloadLiteratures(const string pdfUrlParameter,
            const string metaUrlParameter, const string downloadDir,
            const multimap<string, string> &lits, const bool bibonly) {
        std::vector<std::thread*> threadvec;
        for (auto x : lits) {
            threadvec.push_back(new std::thread(processEntry, x.first, x.second,
                    pdfUrlParameter, metaUrlParameter, downloadDir, bibonly));
            sleep(1 + rand() % 2);
            if (threadvec.size() > 20)
                while (threadvec.size() > 0) {
                    threadvec.back()->join();
                    delete threadvec.back();
                    threadvec.pop_back();
                }
        }
        while (threadvec.size() > 0) {
            threadvec.back()->join();
            delete threadvec.back();
            threadvec.pop_back();
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
    string pdfUrlParameter = inputtree.get<string>("PDF URL parameter",
            "https://www.ncbi.nlm.nih.gov/pmc/articles/%s/pdf/");
    string metaUrlParameter = inputtree.get<string>("Meta data URL parameter",
            "https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi?verb=GetRecord"
            "&identifier=oai:pubmedcentral.nih.gov:%s&metadataPrefix=oai_dc");
    string literatureLists = inputtree.get<string>("Literature lists",
            "/data/textpresso/etc/literatures");
    string downloadDir = inputtree.get<string>("Download directory",
            "/data/textpresso/raw_files/pdf");
    bool bibonly = inputtree.get<bool>("Bibliography only", true);
    cout << "PDF URL parameter : " << pdfUrlParameter << endl;
    cout << "Meta data URL parameter : " << metaUrlParameter << endl;
    cout << "Literature lists : " << literatureLists << endl;
    cout << "Download directory : " << downloadDir << endl;
    cout << "Bibliography only : ";
    if (bibonly)
        cout << "true";
    else
        cout << "false";
    cout << endl;
    multimap<string, string> lits;
    dp::loadLiteratures(literatureLists, lits);
    dp::downloadLiteratures(pdfUrlParameter, metaUrlParameter, downloadDir, lits, bibonly);
    return ret;
}

