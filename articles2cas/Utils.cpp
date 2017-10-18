/**
    Project: libtpc
    File name: Utils.cpp
    
    @author valerio
    @version 1.0 7/26/17.
*/

#include "Utils.h"
#include <boost/date_time/posix_time/posix_time.hpp>
#include <fstream>
#include <boost/iostreams/categories.hpp>
#include <boost/iostreams/copy.hpp>
#include <boost/iostreams/filtering_streambuf.hpp>
#include <boost/iostreams/filter/gzip.hpp>

using namespace std;
using namespace boost::posix_time;

string Utils::get_temp_dir_path()
{
    ptime now = boost::posix_time::microsec_clock::local_time();
    int month = static_cast<int> (now.date().month());
    int year = static_cast<int> (now.date().year());
    int day = static_cast<int> (now.date().day());
    time_duration duration(now.time_of_day());
    long microseconds = duration.total_microseconds();
    long pid = getpid();
    long random = pid + microseconds;
    stringstream ss;
    ss << year << month << day << random;
    return "/run/shm/" + ss.str();
}

string Utils::decompress_gzip(const string& gz_file, const string& tmp_dir) {
    std::ifstream filein(gz_file.c_str(), std::ios_base::in | std::ios_base::binary);
    boost::iostreams::filtering_streambuf<boost::iostreams::input> in;
    in.push(boost::iostreams::gzip_decompressor());
    in.push(filein);
    int lastdot = gz_file.find_last_of(".");
    int lastslash = gz_file.find_last_of("/");
    string tpFile = gz_file.substr(lastslash + 1, lastdot - lastslash - 1);
    string tempFile = tmp_dir + "/" + tpFile;
    std::ofstream out(tempFile.c_str());
    boost::iostreams::copy(in, out);
    out.close();
    return tempFile;
}

void Utils::write_index_descriptor(const std::string& index_path, const std::string& descriptor_path,
                                   const std::string& tmp_conf_files_path)
{
    ofstream output(descriptor_path.c_str());
    output << "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>" << endl;
    output << "<taeDescription xmlns = \"http://uima.apache.org/resourceSpecifier\" >" << endl;
    output << " <frameworkImplementation > org.apache.uima.cpp</frameworkImplementation>" << endl;
    output << " <primitive > true </primitive>" << endl;
    //output << " <annotatorImplementationName > Tpcas2Lpp</annotatorImplementationName>" << endl;
    output << " <annotatorImplementationName > Tpcas2SingleIndex</annotatorImplementationName>" << endl;
    output << " <analysisEngineMetaData> " << endl;
    //output << "         <name > Tpcas2Lpp</name>" << endl;
    output << "         <name > Tpcas2SingeIndex</name>" << endl;
    output << "         <description > Writes an XCAS to a Lucene index.</description> " << endl;
    output << "         <version > 1.0 </version> " << endl;
    output << "         <vendor > Textpresso</vendor> " << endl;
    output << "         <configurationParameters> " << endl;
    output << "                 <configurationParameter> " << endl;
    output << "                         <name > FulltextLuceneIndexDirectory</name>" << endl;
    output << "                         <description > Directory path of Lucene index for fulltext.</description> " << endl;
    output << "                         <type > String</type> " << endl;
    output << "                         <multiValued > false </multiValued> " << endl;
    output << "                         <mandatory > true </mandatory> " << endl;
    output << "                 </configurationParameter>" << endl;
    output << "                 <configurationParameter> " << endl;
    output << "                         <name > FulltextCaseSensitiveLuceneIndexDirectory</name>" << endl;
    output << "                         <description > Directory path of case sensitive Lucene index for fulltext.</description> " << endl;
    output << "                         <type > String</type> " << endl;
    output << "                         <multiValued > false </multiValued> " << endl;
    output << "                         <mandatory > true </mandatory> " << endl;
    output << "                 </configurationParameter>" << endl;
    output << "                 <configurationParameter> " << endl;
    output << "                 <name > TokenLuceneIndexDirectory</name> " << endl;
    output << "                 <description > Directory path of Lucene index for tokens.</description> " << endl;
    output << "                 <type > String</type>" << endl;
    output << "                 <multiValued > false </multiValued>" << endl;
    output << "                 <mandatory > true </mandatory> " << endl;
    output << "                 </configurationParameter>" << endl;
    output << "                 <configurationParameter> " << endl;
    output << "                 <name > TokenCaseSensitiveLuceneIndexDirectory</name> " << endl;
    output << "                 <description > Directory path of case sensitive Lucene index for tokens.</description> " << endl;
    output << "                 <type > String</type>" << endl;
    output << "                 <multiValued > false </multiValued>" << endl;
    output << "                 <mandatory > true </mandatory> " << endl;
    output << "                 </configurationParameter>" << endl;
    output << "                 <configurationParameter> " << endl;
    output << "                         <name > SentenceLuceneIndexDirectory</name> " << endl;
    output << "                         <description > Directory path of Lucene index for sentences.</description>" << endl;
    output << "                         <type > String</type>" << endl;
    output << "                         <multiValued > false </multiValued> " << endl;
    output << "                         <mandatory > true </mandatory> " << endl;
    output << "                 </configurationParameter> " << endl;
    output << "                 <configurationParameter> " << endl;
    output << "                         <name > SentenceCaseSensitiveLuceneIndexDirectory</name> " << endl;
    output << "                         <description > Directory path of case sensitive Lucene index for sentences.</description>" << endl;
    output << "                         <type > String</type>" << endl;
    output << "                         <multiValued > false </multiValued> " << endl;
    output << "                         <mandatory > true </mandatory> " << endl;
    output << "                 </configurationParameter> " << endl;
    output << "                 <configurationParameter> " << endl;
    output << "                         <name > LexicalLuceneIndexDirectory</name> " << endl;
    output << "                         <description > Directory path of Lucene index for lexical annotations.</description> " << endl;
    output << "                         <type > String</type>" << endl;
    output << "                         <multiValued > false </multiValued>" << endl;
    output << "                         <mandatory > true </mandatory>" << endl;
    output << "                 </configurationParameter>" << endl;
    output << "                 <configurationParameter> " << endl;
    output << "                         <name > LexicalCaseSensitiveLuceneIndexDirectory</name> " << endl;
    output << "                         <description > Directory path of case sensitive Lucene index for lexical annotations.</description> " << endl;
    output << "                         <type > String</type>" << endl;
    output << "                         <multiValued > false </multiValued>" << endl;
    output << "                         <mandatory > true </mandatory>" << endl;
    output << "                 </configurationParameter>" << endl;
    output << "                 <configurationParameter> " << endl;
    output << "                         <name > BibliographyLuceneIndexDirectory</name> " << endl;
    output << "                         <description > Directory path of Lucene index for bibliography annotations.</description> " << endl;
    output << "                         <type > String</type>" << endl;
    output << "                         <multiValued > false </multiValued>" << endl;
    output << "                         <mandatory > true </mandatory>" << endl;
    output << "                 </configurationParameter>" << endl;
    output << "                 <configurationParameter> " << endl;
    output << "                         <name > BibliographyCaseSensitiveLuceneIndexDirectory</name> " << endl;
    output << "                         <description > Directory path of case sensitive Lucene index for bibliography annotations.</description> " << endl;
    output << "                         <type > String</type>" << endl;
    output << "                         <multiValued > false </multiValued>" << endl;
    output << "                         <mandatory > true </mandatory>" << endl;
    output << "                 </configurationParameter>" << endl;
    output << "                 <configurationParameter> " << endl;
    output << "                         <name > TempDirectory</name> " << endl;
    output << "                         <description > temporary directory under /run/shm/ to store newindexflag </description>" << endl;
    output << "                         <type > String</type>" << endl;
    output << "                         <multiValued > false </multiValued>" << endl;
    output << "                         <mandatory > true </mandatory>" << endl;
    output << "                 </configurationParameter>" << endl;
    output << "         </configurationParameters>" << endl;
    output << "         <configurationParameterSettings>" << endl;
    output << "                 <nameValuePair> " << endl;
    output << "                         <name > FulltextLuceneIndexDirectory</name>" << endl;
    output << "                         <value> " << endl;
    output << "                         <string>" << index_path << "/fulltext" << "</string>" << endl;
    output << "                         </value> " << endl;
    output << "                 </nameValuePair> " << endl;
    output << "                 <nameValuePair> " << endl;
    output << "                         <name > TokenLuceneIndexDirectory</name>" << endl;
    output << "                         <value> " << endl;
    output << "                         <string>" << index_path << "/token" << "</string>" << endl;
    output << "                         </value>" << endl;
    output << "                 </nameValuePair> " << endl;
    output << "                 <nameValuePair>" << endl;
    output << "                         <name > SentenceLuceneIndexDirectory</name> " << endl;
    output << "                         <value> " << endl;
    output << "                        <string>" << index_path << "/sentence" << "</string>" << endl;
    output << "                         </value> " << endl;
    output << "                 </nameValuePair> " << endl;
    output << "                 <nameValuePair>" << endl;
    output << "                         <name > LexicalLuceneIndexDirectory</name> " << endl;
    output << "                         <value> " << endl;
    output << "                         <string>" << index_path << "/lexical" << "</string>" << endl;
    output << "                         </value> " << endl;
    output << "                 </nameValuePair> " << endl;
    output << "                 <nameValuePair>" << endl;
    output << "                         <name > BibliographyLuceneIndexDirectory</name> " << endl;
    output << "                         <value> " << endl;
    output << "                         <string>" << index_path << "/bibliography" << "</string>" << endl;
    output << "                         </value> " << endl;
    output << "                 </nameValuePair> " << endl;
    output << "                 <nameValuePair> " << endl;
    output << "                         <name > FulltextCaseSensitiveLuceneIndexDirectory</name>" << endl;
    output << "                         <value> " << endl;
    output << "                         <string>" << index_path << "/fulltext_cs" << "</string>" << endl;
    output << "                         </value> " << endl;
    output << "                 </nameValuePair> " << endl;
    output << "                 <nameValuePair> " << endl;
    output << "                         <name > TokenCaseSensitiveLuceneIndexDirectory</name>" << endl;
    output << "                         <value> " << endl;
    output << "                         <string>" << index_path << "/token_cs" << "</string>" << endl;
    output << "                         </value>" << endl;
    output << "                 </nameValuePair> " << endl;
    output << "                 <nameValuePair>" << endl;
    output << "                         <name > SentenceCaseSensitiveLuceneIndexDirectory</name> " << endl;
    output << "                         <value> " << endl;
    output << "                        <string>" << index_path << "/sentence_cs" << "</string>" << endl;
    output << "                         </value> " << endl;
    output << "                 </nameValuePair> " << endl;
    output << "                 <nameValuePair>" << endl;
    output << "                         <name > LexicalCaseSensitiveLuceneIndexDirectory</name> " << endl;
    output << "                         <value> " << endl;
    output << "                         <string>" << index_path << "/lexical_cs" << "</string>" << endl;
    output << "                         </value> " << endl;
    output << "                 </nameValuePair> " << endl;
    output << "                 <nameValuePair>" << endl;
    output << "                         <name > BibliographyCaseSensitiveLuceneIndexDirectory</name> " << endl;
    output << "                         <value> " << endl;
    output << "                         <string>" << index_path << "/bibliography_cs" << "</string>" << endl;
    output << "                         </value> " << endl;
    output << "                 </nameValuePair> " << endl;
    output << "                 <nameValuePair>" << endl;
    output << "                         <name >TempDirectory</name> " << endl;
    output << "                         <value> " << endl;
    output << "                         <string>" << tmp_conf_files_path << "</string>" << endl;
    output << "                         </value> " << endl;
    output << "                 </nameValuePair> " << endl;
    output << "         </configurationParameterSettings> " << endl;
    output << " <typeSystemDescription> " << endl;
    output << "         <imports> " << endl;
    output << "         <import location = \"/usr/local/uima_descriptors/TpLexiconAnnotatorTypeSystem.xml\"/> " << endl;
    output << "         </imports>" << endl;
    output << " </typeSystemDescription>" << endl;
    output << " <capabilities> " << endl;
    output << " <capability>" << endl;
    output << " <inputs/> " << endl;
    output << " <outputs/>" << endl;
    output << " <languagesSupported> " << endl;
    output << "         <language >x-unspecified</language>" << endl;
    output << " </languagesSupported>" << endl;
    output << " </capability>" << endl;
    output << " </capabilities> " << endl;
    output << " </analysisEngineMetaData>" << endl;
    output << "</taeDescription> " << endl;
    output.close();
}