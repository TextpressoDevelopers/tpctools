/* 
 * File:   main.cpp
 * Author: mueller
 *
 * Created on July 18, 2014, 10:27 AM
 */

#define TPCAS2TPCENTRALDESCRIPTOR "/usr/local/uima_descriptors/Tpcas2TpCentral.xml"

#include "xercesc/util/XMLString.hpp"
#include <uima/api.hpp>
#include "uima/xmideserializer.hpp"
#include <boost/iostreams/filtering_streambuf.hpp>
#include <boost/iostreams/copy.hpp>
#include <boost/iostreams/filter/gzip.hpp>
#include <boost/filesystem.hpp>
#include <boost/regex.hpp>
#include "cmdline.h"

/*
 * getXMLstring and GetBibFromXML were written by Yuling Li.
 */

namespace {

    std::string getXMLstring(uima::CAS & tcas) {
        uima::UnicodeStringRef usdocref = tcas.getDocumentText();
        if (usdocref.length() > 0) {
            std::string xmlstring = usdocref.asUTF8();
            return xmlstring;
        } else {
            return "";
        }
    }

    std::vector<std::string> GetBibFromXML(std::string xml_text) {
        boost::regex nline("\\n");
        xml_text = boost::regex_replace(xml_text, nline, "");
        //find author
        std::string t_xmltext = xml_text;
        boost::regex authorregex("\<contrib-group\>(.+?)\<\/contrib-group\>");
        boost::smatch author_matches;
        std::string author = "";
        while (boost::regex_search(t_xmltext, author_matches, authorregex)) {
            int size = author_matches.size();
            std::string hit_text = author_matches[1];
            boost::smatch name_matches;
            boost::regex nameregex("\<surname\>(.+?)\<\/surname\>\\s+\<given-names\>(.+?)\<\/given-names\>");
            while (boost::regex_search(hit_text, name_matches, nameregex)) {
                author = author + name_matches[1] + " " + name_matches[2] + ", ";
                hit_text = name_matches.suffix().str();
            }
            t_xmltext = author_matches.suffix().str();
        }
        boost::regex comma("\\, $");
        author = boost::regex_replace(author, comma, "");
        //find subject
        t_xmltext = xml_text;
        boost::regex subjectregex("\<subject\>(.+?)\<\/subject>");
        boost::smatch subject_matches;
        std::string subject = "";
        while (boost::regex_search(t_xmltext, subject_matches, subjectregex)) {
            subject = subject + subject_matches[1] + ", ";
            t_xmltext = subject_matches.suffix().str();
        }
        subject = boost::regex_replace(subject, comma, "");
        //find accession
        t_xmltext = xml_text;
        std::string accession = "";
        boost::regex pmidregex("\<article-id pub-id-type=\"pmid\"\>(\\d+?)\<\/article-id\>");
        boost::regex pmcregex("\<article-id pub-id-type=\"pmc\"\>(\\d+?)\<\/article-id\>");
        boost::smatch pmid_matches;
        boost::smatch pmc_matches;
        if (boost::regex_search(t_xmltext, pmid_matches, pmidregex)) {
            accession = "PMID       " + pmid_matches[1];
        } else if (boost::regex_search(t_xmltext, pmc_matches, pmcregex)) {
            accession = "PMC       " + pmc_matches[1];
        }
        // find article type
        t_xmltext = xml_text;
        std::string type = "";
        boost::regex typeregex("article-type=\"(.+?)\"");
        boost::smatch type_matches;
        if (boost::regex_search(t_xmltext, type_matches, typeregex)) {
            type = type_matches[1];
        }
        // find journal
        t_xmltext = xml_text;
        std::string journal = "";
        boost::regex journalregex("\<journal-title\>(.+?)\<\/journal-title\>");
        boost::smatch journal_matches;
        if (boost::regex_search(t_xmltext, journal_matches, journalregex)) {
            journal = journal_matches[1];
        }
        // find article title
        t_xmltext = xml_text;
        std::string title = "";
        boost::regex articleregex("\<article-title\>(.+?)\<\/article-title\>");

        boost::smatch article_matches;
        if (boost::regex_search(t_xmltext, article_matches, articleregex)) {
            title = article_matches[1];
        }
        // find abstract
        t_xmltext = xml_text;
        std::string abstract = "";
        boost::regex abstractregex("\<abstract\>(.+?)\<\/abstract\>");
        boost::smatch abstract_matches;
        if (boost::regex_search(t_xmltext, abstract_matches, abstractregex)) {
            abstract = abstract_matches[1];
        }
        // find citation
        t_xmltext = xml_text;
        std::string citation = "";
        boost::regex volumeregex("\<volume\>(\\d+)\<\/volume\>");
        boost::smatch volume_matches;
        if (boost::regex_search(t_xmltext, volume_matches, volumeregex)) {
            citation = citation + "V : " + volume_matches[1] + " ";
        }
        boost::regex issueregex("\<issue\>(\\d+)\<\/issue\>");
        boost::smatch issue_matches;
        if (boost::regex_search(t_xmltext, issue_matches, issueregex)) {
            citation = citation + "(" + issue_matches[1] + ") ";
        }
        boost::regex pageregex("\<fpage\>(\\d+)\<\/fpage\>\\s+\<lpage\>(\\d+)\<\/lpage\>");
        boost::smatch page_matches;
        if (boost::regex_search(t_xmltext, page_matches, pageregex)) {
            citation = citation + "pp. " + page_matches[1] + "-" + page_matches[2];
        }
        // find year
        t_xmltext = xml_text;
        std::string year = "";
        boost::regex yearregex("\<pub-date pub-type=\".*?\"\>.*?\<year\>(\\d+)\<\/year\>\\s+\<\/pub-date\>");
        boost::smatch year_matches;
        if (boost::regex_search(t_xmltext, year_matches, yearregex)) {
            year = year_matches[1];
        }
        std::vector<std::string> bibinfo;
        bibinfo.push_back(author);
        bibinfo.push_back(accession);
        bibinfo.push_back(type);
        bibinfo.push_back(title);
        bibinfo.push_back(journal);
        bibinfo.push_back(citation);
        bibinfo.push_back(year);
        bibinfo.push_back(abstract);
        bibinfo.push_back(subject);
        return bibinfo;
    }

    std::string uncompressGzip2(std::string gzFile) {
        std::ifstream filein(gzFile.c_str(), std::ios_base::in | std::ios_base::binary);
        boost::iostreams::filtering_streambuf<boost::iostreams::input> in;
        in.push(boost::iostreams::gzip_decompressor());
        in.push(filein);
        char tmpname[L_tmpnam];
        char * pDummy = tmpnam(tmpname);
        std::string tmpfile(tmpname);
        while (boost::filesystem::exists(tmpfile)) {
            char * pDummy = tmpnam(tmpname);
            tmpfile = std::string(tmpname);
        }
        std::ofstream out(tmpfile.c_str());
        boost::iostreams::copy(in, out);
        out.close();
        return tmpfile;
    }

    //[ Uima related

    uima::AnalysisEngine * CreateUimaEngine(const char * descriptor) {
        uima::ErrorInfo errorInfo;
        uima::AnalysisEngine * ret = uima::Framework::createAnalysisEngine(descriptor, errorInfo);
        if (errorInfo.getErrorId() != UIMA_ERR_NONE) {
            std::cerr << std::endl
                    << "  Error string  : "
                    << uima::AnalysisEngine::getErrorIdAsCString(errorInfo.getErrorId())
                    << std::endl
                    << "  UIMACPP Error info:" << std::endl
                    << errorInfo << std::endl;
        }
        return ret;
    }

    uima::CAS * GetCas(const char * pszInputFile, uima::AnalysisEngine * pEngine) {
        uima::CAS * ret = pEngine->newCAS();
        if (ret == NULL) {
            std::cerr << "pEngine_->newCAS() failed." << std::endl;
        } else {
            try {
                /* initialize from an xmicas */
                XMLCh * native = XMLString::transcode(pszInputFile);
                LocalFileInputSource fileIS(native);
                XMLString::release(&native);
                uima::XmiDeserializer::deserialize(fileIS, * ret, true);
            } catch (uima::Exception e) {
                uima::ErrorInfo errInfo = e.getErrorInfo();
                std::cerr << "Error " << errInfo.getErrorId() << " " << errInfo.getMessage() << std::endl;
                std::cerr << errInfo << std::endl;
            }
        }
        return ret;
    }
    //] Uima related
}

int main(int argc, char * argv[]) {

    cmdline::parser p;
    p.set_program_name("printbibfromcasfile");
    p.add("abstract", 'a', "print abstract");
    p.add("author", 'u', "print author");
    p.add("accession", 'c', "print citation");
    p.add("citation", 'i', "print citation");
    p.add("journal", 'j', "print journal");
    p.add("subject", 's', "print subject");
    p.add("title", 't', "print title");
    p.add("type", 'p', "print type");
    p.add("year", 'y', "print year");
    p.add("nxml", 'n', "file is in nxml format, not gzipped cas.");
    p.footer("<filename>");
    if (p.parse(argc, argv) == 0) {
        std::cerr << "Error:" << p.error() << std::endl
                << p.usage() << std::endl;
        return -1;
    }
    if (argc < 3) {
        std::cerr << p.usage() << std::endl;
        return -1;
    }
    std::string filename;
    if (p.rest().size() > 0) filename = p.rest()[0];
    //
    std::vector<std::string> bib_info;
    if (p.exist("nxml")) {
        std::ifstream f(filename.c_str());
        std::string in;
        std::string all;
        while (getline(f, in)) all += in;
        f.close();
        bib_info = GetBibFromXML(all);
    } else {
        (void) uima::ResourceManager::createInstance("TPCAS2TPCENTRALAE");
        uima::AnalysisEngine * pEngine = CreateUimaEngine(TPCAS2TPCENTRALDESCRIPTOR);
        std::string tmpfl = uncompressGzip2(filename);
        uima::CAS * pcas = GetCas(tmpfl.c_str(), pEngine);
        boost::filesystem::remove(tmpfl);
        bib_info = GetBibFromXML(getXMLstring(*pcas));
    }
    std::string l_author = bib_info[0];
    std::string l_accession = bib_info[1];
    std::string l_type = bib_info[2];
    std::string l_title = bib_info[3];
    std::string l_journal = bib_info[4];
    std::string l_citation = bib_info[5];
    std::string l_year = bib_info[6];
    std::string l_abstract = bib_info[7];
    std::string l_subject = bib_info[8];
    std::cout << "Filename:" << filename << "\t";
    if (p.exist("title")) std::cout << "Title:" << l_title << "\t";
    if (p.exist("author")) std::cout << "Author:" << l_author << "\t";
    if (p.exist("accession")) std::cout << "Accession:" << l_accession << "\t";
    if (p.exist("type")) std::cout << "Type:" << l_type << "\t";
    if (p.exist("journal")) std::cout << "Journal:" << l_journal << "\t";
    if (p.exist("citation")) std::cout << "Citation:" << l_citation << "\t";
    if (p.exist("year")) std::cout << "Year:" << l_year << "\t";
    if (p.exist("abstract")) std::cout << "Abstract:" << l_abstract << "\t";
    if (p.exist("subject")) std::cout << "Subject:" << l_subject << "\t";
    std::cout << std::endl;
    return 0;
}
