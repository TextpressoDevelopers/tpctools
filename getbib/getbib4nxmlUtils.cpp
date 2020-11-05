/*
 * CAS file utils
 * author: liyuling
 * Date: Nov, 2013
 */

#include "getbib4nxmlUtils.h"
#include <boost/filesystem/operations.hpp>

std::string uncompressGzip(std::string gzFile) {
    std::string tempFile;
    try {
      std::ifstream filein(gzFile.c_str(), std::ios_base::in | std::ios_base::binary);
      boost::iostreams::filtering_streambuf<boost::iostreams::input> in;
      in.push(boost::iostreams::gzip_decompressor());
      in.push(filein);
      int lastdot = gzFile.find_last_of(".");
      int lastslash = gzFile.find_last_of("/");
      std::string tpFile = gzFile.substr(lastslash + 1, lastdot - lastslash - 1);
      //std::string shm("/run/shm/");
      //std::string tempFile = shm + tpFile;
      std::string tempDir = getTempDir();
      tempFile = tempDir + "/" + tpFile;
      boost::filesystem::create_directories(tempDir);
      std::ofstream out(tempFile.c_str());
      boost::iostreams::copy(in, out);
      out.close();
    } catch (const std::exception &e) {
      std::cerr << "uncompressGzip Error " << e.what() << std::endl;
    }
    return tempFile;
}

std::string getTempDir() {
    boost::posix_time::ptime now = boost::posix_time::microsec_clock::local_time();
    int month = static_cast<int> (now.date().month());
    int year = static_cast<int> (now.date().year());
    int day = static_cast<int> (now.date().day());
    boost::posix_time::time_duration duration(now.time_of_day());
    long microseconds = duration.total_microseconds();
    long pid = getpid();
    long random = pid + microseconds;
    std::stringstream ss;
    ss << year << month << day << random;
    std::string tempDir = "/run/shm/" + ss.str();
    return tempDir;
}

void writeToIndexDescriptor(std::string indexpath, std::string descriptor, std::string tempDir) {
    std::ofstream output(descriptor.c_str());
    output << "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>" << std::endl;
    output << "<taeDescription xmlns = \"http://uima.apache.org/resourceSpecifier\" >" << std::endl;
    output << " <frameworkImplementation > org.apache.uima.cpp</frameworkImplementation>" << std::endl;
    output << " <primitive > true </primitive>" << std::endl;
    output << " <annotatorImplementationName > Tpcas2Bib4Nxml</annotatorImplementationName>" << std::endl;
    output << " <analysisEngineMetaData> " << std::endl;
    output << "         <name > Tpcas2Bib4Nxml</name>" << std::endl;
    output << "         <description > Writes an XCAS to a Lucene index.</description> " << std::endl;
    output << "         <version > 1.0 </version> " << std::endl;
    output << "         <vendor > Textpresso</vendor> " << std::endl;
    output << "         <configurationParameters> " << std::endl;
    output << "                 <configurationParameter> " << std::endl;
    output << "                         <name > FulltextLuceneIndexDirectory</name>" << std::endl;
    output << "                         <description > Directory path of Lucene index for fulltext.</description> " << std::endl;
    output << "                         <type > String</type> " << std::endl;
    output << "                         <multiValued > false </multiValued> " << std::endl;
    output << "                         <mandatory > true </mandatory> " << std::endl;
    output << "                 </configurationParameter>" << std::endl;
    output << "                 <configurationParameter> " << std::endl;
    output << "                 <name > TokenLuceneIndexDirectory</name> " << std::endl;
    output << "                 <description > Directory path of Lucene index for tokens.</description> " << std::endl;
    output << "                 <type > String</type>" << std::endl;
    output << "                 <multiValued > false </multiValued>" << std::endl;
    output << "                 <mandatory > true </mandatory> " << std::endl;
    output << "                 </configurationParameter>" << std::endl;
    output << "                 <configurationParameter> " << std::endl;
    output << "                         <name > SentenceLuceneIndexDirectory</name> " << std::endl;
    output << "                         <description > Directory path of Lucene index for sentences.</description>" << std::endl;
    output << "                         <type > String</type>" << std::endl;
    output << "                         <multiValued > false </multiValued> " << std::endl;
    output << "                         <mandatory > true </mandatory> " << std::endl;
    output << "                 </configurationParameter> " << std::endl;
    output << "                 <configurationParameter> " << std::endl;
    output << "                         <name > LexicalLuceneIndexDirectory</name> " << std::endl;
    output << "                         <description > Directory path of Lucene index for lexical annotations.</description> " << std::endl;
    output << "                         <type > String</type>" << std::endl;
    output << "                         <multiValued > false </multiValued>" << std::endl;
    output << "                         <mandatory > true </mandatory>" << std::endl;
    output << "                 </configurationParameter>" << std::endl;
    output << "                 <configurationParameter> " << std::endl;
    output << "                         <name > BibliographyLuceneIndexDirectory</name> " << std::endl;
    output << "                         <description > Directory path of Lucene index for bibliography annotations.</description> " << std::endl;
    output << "                         <type > String</type>" << std::endl;
    output << "                         <multiValued > false </multiValued>" << std::endl;
    output << "                         <mandatory > true </mandatory>" << std::endl;
    output << "                 </configurationParameter>" << std::endl;
    output << "                 <configurationParameter> " << std::endl;
    output << "                         <name > TempDirectory</name> " << std::endl;
    output << "                         <description > temporary directory under /run/shm/ to store newindexflag </description>" << std::endl;
    output << "                         <type > String</type>" << std::endl;
    output << "                         <multiValued > false </multiValued>" << std::endl;
    output << "                         <mandatory > true </mandatory>" << std::endl;
    output << "                 </configurationParameter>" << std::endl;
    output << "         </configurationParameters>" << std::endl;
    output << "         <configurationParameterSettings>" << std::endl;
    output << "                 <nameValuePair> " << std::endl;
    output << "                         <name > FulltextLuceneIndexDirectory</name>" << std::endl;
    output << "                         <value> " << std::endl;
    output << "                         <string>" << indexpath << "/fulltext" << "</string>" << std::endl;
    output << "                         </value> " << std::endl;
    output << "                 </nameValuePair> " << std::endl;
    output << "                 <nameValuePair> " << std::endl;
    output << "                         <name > TokenLuceneIndexDirectory</name>" << std::endl;
    output << "                         <value> " << std::endl;
    output << "                         <string>" << indexpath << "/token" << "</string>" << std::endl;
    output << "                         </value>" << std::endl;
    output << "                 </nameValuePair> " << std::endl;
    output << "                 <nameValuePair>" << std::endl;
    output << "                         <name > SentenceLuceneIndexDirectory</name> " << std::endl;
    output << "                         <value> " << std::endl;
    output << "                        <string>" << indexpath << "/sentence" << "</string>" << std::endl;
    output << "                         </value> " << std::endl;
    output << "                 </nameValuePair> " << std::endl;
    output << "                 <nameValuePair>" << std::endl;
    output << "                         <name > LexicalLuceneIndexDirectory</name> " << std::endl;
    output << "                         <value> " << std::endl;
    output << "                         <string>" << indexpath << "/lexical" << "</string>" << std::endl;
    output << "                         </value> " << std::endl;
    output << "                 </nameValuePair> " << std::endl;
    output << "                 <nameValuePair>" << std::endl;
    output << "                         <name > BibliographyLuceneIndexDirectory</name> " << std::endl;
    output << "                         <value> " << std::endl;
    output << "                         <string>" << indexpath << "/bibliography" << "</string>" << std::endl;
    output << "                         </value> " << std::endl;
    output << "                 </nameValuePair> " << std::endl;
    output << "                 <nameValuePair>" << std::endl;
    output << "                         <name >TempDirectory</name> " << std::endl;
    output << "                         <value> " << std::endl;
    output << "                         <string>" << tempDir << "</string>" << std::endl;
    output << "                         </value> " << std::endl;
    output << "                 </nameValuePair> " << std::endl;
    output << "         </configurationParameterSettings> " << std::endl;
    output << " <typeSystemDescription> " << std::endl;
    output << "         <imports> " << std::endl;
    output << "         <import location = \"/usr/local/uima_descriptors/TpLexiconAnnotatorTypeSystem.xml\"/> " << std::endl;
    output << "         </imports>" << std::endl;
    output << " </typeSystemDescription>" << std::endl;
    output << " <capabilities> " << std::endl;
    output << " <capability>" << std::endl;
    output << " <inputs/> " << std::endl;
    output << " <outputs/>" << std::endl;
    output << " <languagesSupported> " << std::endl;
    output << "         <language >x-unspecified</language>" << std::endl;
    output << " </languagesSupported>" << std::endl;
    output << " </capability>" << std::endl;
    output << " </capabilities> " << std::endl;
    output << " </analysisEngineMetaData>" << std::endl;
    output << "</taeDescription> " << std::endl;
    output.close();
}

void writeDefaultBibFile(const std::string &file_path) {
    std::ofstream output(file_path);
    output << "author|<not uploaded>" << std::endl;
    output << "accession|<not uploaded>" << std::endl;
    output << "type|<not uploaded>" << std::endl;
    output << "title|<not uploaded>" << std::endl;
    output << "journal|<not uploaded>" << std::endl;
    output << "citation|<not uploaded>" << std::endl;
    output << "year|<not uploaded>" << std::endl;
    output << "abstract|<not uploaded>" << std::endl;
    output.close();
}
