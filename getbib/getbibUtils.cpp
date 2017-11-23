/*
 * CAS file utils
 * author: liyuling
 * Date: Nov, 2013
 */

#include "getbibUtils.h"

//const char* newindexflag = "/run/shm/newindexflag"; 

string uncompressGzip(string gzFile) {
    // std::cout << "166" << endl;
    std::ifstream filein(gzFile.c_str(), std::ios_base::in | std::ios_base::binary);
    boost::iostreams::filtering_streambuf<boost::iostreams::input> in;
    in.push(boost::iostreams::gzip_decompressor());
    in.push(filein);

    int lastdot = gzFile.find_last_of(".");
    int lastslash = gzFile.find_last_of("/");
    string tpFile = gzFile.substr(lastslash + 1, lastdot - lastslash - 1);

    string shm("/run/shm/");
    string tempFile = shm + tpFile;
    //string tempFile = getTempDir() + "/" + tpFile;
    //  std::cout << "177 " << tempFile << endl;
    std::ofstream out(tempFile.c_str());
    boost::iostreams::copy(in, out);
    out.close();

    return tempFile;
}

string getTempDir() {
    // boost::posix_time::ptime now = boost::posix_time::second_clock::local_time();

    boost::posix_time::ptime now = boost::posix_time::microsec_clock::local_time();

    int month = static_cast<int> (now.date().month());
    int year = static_cast<int> (now.date().year());
    int day = static_cast<int> (now.date().day());


    boost::posix_time::time_duration duration(now.time_of_day());

    long microseconds = duration.total_microseconds();



    long pid = getpid();
    //int second = time(0);



    //int random = pid + second;

    long random = pid + microseconds;

    //cout << "r: " << random << endl;
    std::stringstream ss;
    //ss << year << month << day << minutes;
    ss << year << month << day << random;
    std::string tempDir = "/run/shm/" + ss.str();
    //cout <<"hello" <<tempDir << endl;

    return tempDir;

}

//void writeToIndexDescriptor(string indexpath, string descriptor, string tempDir) {

void writeToIndexDescriptor(string indexpath, string descriptor, string tempDir) {
    ofstream output(descriptor.c_str());
    output << "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>" << endl;
    output << "<taeDescription xmlns = \"http://uima.apache.org/resourceSpecifier\" >" << endl;
    output << " <frameworkImplementation > org.apache.uima.cpp</frameworkImplementation>" << endl;
    output << " <primitive > true </primitive>" << endl;
    //output << " <annotatorImplementationName > Tpcas2Lpp</annotatorImplementationName>" << endl;
    output << " <annotatorImplementationName > Tpcas2Bib</annotatorImplementationName>" << endl;
    output << " <analysisEngineMetaData> " << endl;
    //output << "         <name > Tpcas2Lpp</name>" << endl;
    output << "         <name > Tpcas2Bib</name>" << endl;
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
    output << "                 <name > TokenLuceneIndexDirectory</name> " << endl;
    output << "                 <description > Directory path of Lucene index for tokens.</description> " << endl;
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
    output << "                         <name > LexicalLuceneIndexDirectory</name> " << endl;
    output << "                         <description > Directory path of Lucene index for lexical annotations.</description> " << endl;
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
    output << "                         <string>" << indexpath << "/fulltext" << "</string>" << endl;
    output << "                         </value> " << endl;
    output << "                 </nameValuePair> " << endl;
    output << "                 <nameValuePair> " << endl;
    output << "                         <name > TokenLuceneIndexDirectory</name>" << endl;
    output << "                         <value> " << endl;
    output << "                         <string>" << indexpath << "/token" << "</string>" << endl;
    output << "                         </value>" << endl;
    output << "                 </nameValuePair> " << endl;
    output << "                 <nameValuePair>" << endl;
    output << "                         <name > SentenceLuceneIndexDirectory</name> " << endl;
    output << "                         <value> " << endl;
    output << "                        <string>" << indexpath << "/sentence" << "</string>" << endl;
    output << "                         </value> " << endl;
    output << "                 </nameValuePair> " << endl;
    output << "                 <nameValuePair>" << endl;
    output << "                         <name > LexicalLuceneIndexDirectory</name> " << endl;
    output << "                         <value> " << endl;
    output << "                         <string>" << indexpath << "/lexical" << "</string>" << endl;
    output << "                         </value> " << endl;
    output << "                 </nameValuePair> " << endl;
    output << "                 <nameValuePair>" << endl;
    output << "                         <name > BibliographyLuceneIndexDirectory</name> " << endl;
    output << "                         <value> " << endl;
    output << "                         <string>" << indexpath << "/bibliography" << "</string>" << endl;
    output << "                         </value> " << endl;
    output << "                 </nameValuePair> " << endl;
    output << "                 <nameValuePair>" << endl;
    output << "                         <name >TempDirectory</name> " << endl;
    output << "                         <value> " << endl;
    output << "                         <string>" << tempDir << "</string>" << endl;
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

/*
void optimizeIndex(string indexpath)
{
     String TokenIndexDir = StringUtils::toString(indexpath.c_str());
     IndexWriterPtr tokenwriter = newLucene<IndexWriter > (FSDirectory::open(TokenIndexDir),
     newLucene<StandardAnalyzer > (LuceneVersion::LUCENE_CURRENT), false, 
     IndexWriter::MaxFieldLengthLIMITED);
}
 */