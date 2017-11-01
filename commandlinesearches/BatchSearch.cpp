/* 
 * File:   BatchSearch.cpp
 * Author: mueller
 * 
 * Created on February 9, 2017, 12:00 PM
 */

#include "BatchSearch.h"
#include <iostream>

#include "lucene++/LuceneHeaders.h"
#include <boost/regex.hpp>
#include <boost/filesystem.hpp>

const Lucene::String LUCENEINDEXBASE = L"/usr/local/textpresso/luceneindex/";
const int MAXHITS = 100000;

namespace {

    std::wstring str2wstr(const std::string & s) {
        std::wstring temp(s.length(), L' ');
        std::copy(s.begin(), s.end(), temp.begin());
        return temp;
    }

    std::string wstr2str(const std::wstring & wstring) {
        std::string str(wstring.begin(), wstring.end());
        return str;
    }

    std::string lucenestr2str(const Lucene::String & lstring) {
        std::wstring w_str = lstring.c_str();

        return wstr2str(w_str);
    }

    Lucene::DocumentPtr getBibDocPtr(Lucene::String identifier, const std::set<std::string> & pickedlit) {
        Lucene::Collection<Lucene::IndexReaderPtr> subReaders = Lucene::Collection<Lucene::IndexReaderPtr>::newInstance(0);
        Lucene::Collection<Lucene::ScoreDocPtr> scoredocPtrCollection;
        Lucene::SearcherPtr searcher; //  = newLucene<IndexSearcher > (reader);
        Lucene::TopScoreDocCollectorPtr collectorPtr;
        Lucene::String field = L"identifier";
        std::set<std::string>::const_iterator itpl;
        for (itpl = pickedlit.begin(); itpl != pickedlit.end(); itpl++) {
            Lucene::String index_dir = LUCENEINDEXBASE + Lucene::String((*itpl).begin(), (*itpl).end()) + L"/bibliography"; //20140802 use fulltext index to get bib temporarily
            Lucene::IndexReaderPtr reader = Lucene::IndexReader::open(Lucene::FSDirectory::open(index_dir), true);
            subReaders.add(reader);
        }
        Lucene::MultiReaderPtr mr = Lucene::newLucene<Lucene::MultiReader > (subReaders, true);
        searcher = Lucene::newLucene<Lucene::IndexSearcher > (mr);
        Lucene::AnalyzerPtr analyzer = Lucene::newLucene<Lucene::StandardAnalyzer > (Lucene::LuceneVersion::LUCENE_30);
        Lucene::QueryParserPtr parser = Lucene::newLucene<Lucene::QueryParser > (Lucene::LuceneVersion::LUCENE_30, field, analyzer);
        Lucene::String keyword = identifier;
        Lucene::QueryPtr query = parser->parse(keyword);
        int maxHits = 100;
        collectorPtr = Lucene::TopScoreDocCollector::create(maxHits, true);
        searcher->search(query, collectorPtr);
        scoredocPtrCollection = collectorPtr->topDocs()->scoreDocs; // .topDocs().scoreDocs; 
        Lucene::DocumentPtr docPtr = searcher->doc(scoredocPtrCollection[0]->doc); // first result
        mr->close();
        return docPtr;
    }

    std::string RemoveTags(std::string cleantext) {
        boost::regex tagregex("<.+?>");
        cleantext = boost::regex_replace(cleantext, tagregex, "");
        boost::regex tagregex2("</.+?>");
        cleantext = boost::regex_replace(cleantext, tagregex2, "");
        return cleantext;
    }


}

BatchSearch::BatchSearch(std::string scope, std::string keyword,
        std::string keywordnot, bool categoriesanded,
        std::set<std::string> & pickedliterature,
        std::set<std::string> & pickedcat,
        std::map<std::string, std::string> & filters) :
scope_(scope), pickedliterature_(pickedliterature),
keyword_(keyword), keywordnot_(keywordnot),
categoriesanded_(categoriesanded), pickedcat_(pickedcat), filters_(filters) {
    doSearch();
}

void BatchSearch::doSearch() {
    qoutput_.push_back("[Query]");
    Lucene::String field;
    Lucene::String subindex = L"";
    if (scope_ == "document") {
        subindex = L"fulltext";
        field = L"fulltext";
        qoutput_.push_back("scope: document");
    } else if (scope_ == "sentence") {
        subindex = L"sentence";
        field = L"sentence";
        qoutput_.push_back("scope: sentence");
    }
    //
    std::set<std::string> searchedlit;
    if (pickedliterature_.size() > 0) {
        Lucene::Collection<Lucene::IndexReaderPtr> subReaders = Lucene::Collection<Lucene::IndexReaderPtr>::newInstance(0);
        std::set<std::string>::iterator itpl;
        for (itpl = pickedliterature_.begin(); itpl != pickedliterature_.end(); itpl++) {
            Lucene::String index_dir = LUCENEINDEXBASE + Lucene::String((*itpl).begin(), (*itpl).end()) + L"/" + subindex;
            if (boost::filesystem::exists(boost::filesystem::path(lucenestr2str(index_dir)))) {
                qoutput_.push_back("literature: " + *itpl);
                Lucene::IndexReaderPtr reader = Lucene::IndexReader::open(Lucene::FSDirectory::open(index_dir), true);
                subReaders.add(reader);
                searchedlit.insert(*itpl);
            } else {
                std::cerr << "Literature '" << (*itpl) << "' not present." << std::endl;
            }
        }
        Lucene::MultiReaderPtr mr = Lucene::newLucene<Lucene::MultiReader> (subReaders, true);
        //
        Lucene::SearcherPtr keyword_searcher = Lucene::newLucene<Lucene::IndexSearcher> (mr);
        Lucene::AnalyzerPtr analyzer = Lucene::newLucene<Lucene::StandardAnalyzer> (Lucene::LuceneVersion::LUCENE_30);
        Lucene::QueryParserPtr parser = Lucene::newLucene<Lucene::QueryParser > (Lucene::LuceneVersion::LUCENE_30, field, analyzer);
        //
        Lucene::String keyword = Lucene::StringUtils::toString(str2wstr(keyword_));
        Lucene::String keywordnot = Lucene::StringUtils::toString(str2wstr(keywordnot_));
        std::string fulltext_catstring = "";
        std::string sentence_catstring = "";
        std::set<std::string>::iterator it;
        for (it = pickedcat_.begin(); it != pickedcat_.end(); it++) {
            if (it != pickedcat_.begin()) {
                if (categoriesanded_) {
                    fulltext_catstring += " AND ";
                    sentence_catstring += " AND ";
                } else {
                    fulltext_catstring += " OR ";
                    sentence_catstring += " OR ";
                }
            }
            fulltext_catstring += "fulltext_cat:\"" + (*it) + "\"";
            sentence_catstring += "sentence_cat:\"" + (*it) + "\"";
        }
        Lucene::String l_query = L"";
        if (subindex == L"fulltext") {
            if (keyword != L"") l_query = L"fulltext:" + keyword;
            if (keywordnot != L"") l_query = l_query + L" AND -fulltext:" + keywordnot;
            if (!fulltext_catstring.empty()) {
                Lucene::String aux = Lucene::StringUtils::toString(str2wstr(fulltext_catstring));
                if (l_query != L"") {
                    l_query = l_query + L" AND " + aux;
                } else {
                    l_query = aux;
                }
            }
        } else if (subindex == L"sentence") {
            if (keyword != L"") l_query = L"sentence:" + keyword;
            if (keywordnot != L"") l_query = l_query + L" -sentence:" + keywordnot;
            if (!sentence_catstring.empty()) {
                Lucene::String aux = Lucene::StringUtils::toString(str2wstr(sentence_catstring));
                if (l_query != L"") {
                    l_query = l_query + L" AND " + aux;
                } else {
                    l_query = aux;
                }
            }
        }
        // adding filters:
        if (filters_["year"] != "") {
            if (l_query == L"") {
                l_query = l_query + L"year:" + Lucene::StringUtils::toString(str2wstr(filters_["year"]));
            } else {
                l_query = l_query + L" AND year:" + Lucene::StringUtils::toString(str2wstr(filters_["year"]));
            }
        }
        if (filters_["author"] != "") {
            if (l_query == L"") {
                l_query = l_query + L"author:" + Lucene::StringUtils::toString(str2wstr(filters_["author"]));
            } else {
                l_query = l_query + L" AND author:" + Lucene::StringUtils::toString(str2wstr(filters_["author"]));
            }
        }
        if (filters_["journal"] != "") {
            if (l_query == L"") {
                l_query = l_query + L"journal:" + Lucene::StringUtils::toString(str2wstr(filters_["journal"]));
            } else {
                l_query = l_query + L" AND journal:" + Lucene::StringUtils::toString(str2wstr(filters_["journal"]));
            }
        }
        if (filters_["accession"] != "") {
            if (l_query == L"") {
                l_query = l_query + L"accession:" + Lucene::StringUtils::toString(str2wstr(filters_["accession"]));
            } else {
                l_query = l_query + L" AND accession:" + Lucene::StringUtils::toString(str2wstr(filters_["accession"]));
            }
        }
        if (l_query.empty()) {
            std::cerr << "Lucene query emtpy!" << std::endl;
            exit(-1);
        }
        qoutput_.push_back("lucene query: " + lucenestr2str(l_query));
        qoutput_.push_back("");
        Lucene::QueryPtr query = parser->parse(l_query);
        Lucene::TopScoreDocCollectorPtr collectorPtr = Lucene::TopScoreDocCollector::create(MAXHITS, true);
        keyword_searcher->search(query, collectorPtr);
        Lucene::Collection<Lucene::ScoreDocPtr> scoredocPtrCollection = collectorPtr->topDocs()->scoreDocs; // .topDocs().scoreDocs;
        //
        std::map<Lucene::String, double> doc2score; // identifier to score
        std::map<Lucene::String, std::vector<int> > doc2ids; // identifier to lucene docids
        std::multimap<double, Lucene::String> score2doc; // score to identifier (reverse of doc2score_)
        std::map<int, double> ids2score;
        std::vector<std::pair<double, Lucene::String> > result2doc;
        doc2score.clear(); // identifier to score
        score2doc.clear(); // score to identifier(key/value switch of doc2score_)
        doc2ids.clear(); // identifier to lucene docids
        ids2score.clear();
        result2doc.clear();
        for (int i = 0; i < scoredocPtrCollection.size(); i++) {
            int docid = scoredocPtrCollection[i]->doc;
            double score = scoredocPtrCollection[i]->score;
            Lucene::DocumentPtr docPtr = keyword_searcher->doc(docid);
            Lucene::String identifier = docPtr->get(Lucene::StringUtils::toString("identifier"));
            ids2score[docid] = score;
            if (doc2score.find(identifier) == doc2score.end()) {
                doc2score[identifier] = score;
                std::vector<int> ids;
                ids.push_back(docid);
                doc2ids[identifier] = ids;
            } else if (std::abs(docid - doc2ids[identifier].at(0)) < 5000) {
                doc2score[identifier] += score;
                std::vector<int> ids = doc2ids[identifier];
                ids.push_back(docid);
                doc2ids[identifier] = ids;
            }
        }
        std::map<Lucene::String, double>::iterator it2;
        for (it2 = doc2score.begin(); it2 != doc2score.end(); it2++)
            score2doc.insert(std::pair<double, Lucene::String>(it2->second, it2->first));
        std::multimap<double, Lucene::String>::iterator it3;
        for (it3 = score2doc.begin(); it3 != score2doc.end(); it3++)
            result2doc.push_back(std::make_pair(it3->first, it3->second));
        //
        soutput_.push_back("[Search Summary]");
        int32_t hits = collectorPtr->getTotalHits();
        int32_t size = score2doc.size();
        soutput_.push_back("documents: " + std::to_string(size));
        soutput_.push_back("hits: " + std::to_string(hits));
        soutput_.push_back("");
        if (size == 0) return;
        double max_score = score2doc.rbegin()->first; //getting max paper score
        std::multimap<double, Lucene::String>::reverse_iterator multimap_rit = score2doc.rend();
        multimap_rit--;
        double min_score = multimap_rit->first; //getting min paper score
        double max_min = max_score - min_score;
        std::vector<std::pair<double, Lucene::String> >::reverse_iterator rit; ////getting identifier in reverse order, due to scores
        for (rit = result2doc.rbegin(); rit != result2doc.rend(); rit++) {
            routput_.push_back("[Result]");
            double d_score = (rit->first - min_score) / max_min;
            Lucene::String identifier = rit->second;
            std::string score = std::to_string(100.0 * d_score);
            score = score.substr(0, 5); //display only 4 digit of score
            routput_.push_back("score: " + score);
            Lucene::DocumentPtr bibDocPtr = getBibDocPtr(identifier, searchedlit);
            routput_.push_back("accession: " +
                    lucenestr2str(bibDocPtr->get(Lucene::StringUtils::toString("accession"))));
            routput_.push_back("title: " +
                    lucenestr2str(bibDocPtr->get(Lucene::StringUtils::toString("title"))));
            routput_.push_back("author: " +
                    lucenestr2str(bibDocPtr->get(Lucene::StringUtils::toString("author"))));
            routput_.push_back("journal: " +
                    lucenestr2str(bibDocPtr->get(Lucene::StringUtils::toString("journal"))));
            routput_.push_back("year: " +
                    lucenestr2str(bibDocPtr->get(Lucene::StringUtils::toString("year"))));
            routput_.push_back("abstract: " +
                    lucenestr2str(bibDocPtr->get(Lucene::StringUtils::toString("abstract"))));
            std::vector<int> docids = doc2ids[identifier];
            std::multimap<double, int> score2docid;
            for (int i = 0; i < docids.size(); i++) {
                int docid = docids[i];
                double score = ids2score[docid];
                score2docid.insert(std::pair<double, int>(score, docid));
            }
            std::multimap<double, int>::reverse_iterator rit2;
            for (rit2 = score2docid.rbegin(); rit2 != score2docid.rend(); rit2++) {
                int docid = rit2->second;
                //double score = rit2->first;
                Lucene::DocumentPtr docPtr = keyword_searcher->doc(docid);
                std::string text = lucenestr2str(docPtr->get(Lucene::StringUtils::toString(field)));
                text = RemoveTags(text);
                std::string cleantext = ("");
                for (int i = 0; i < text.length(); i++) {
                    char c = text[i];
                    if (std::isprint(c)) {
                        cleantext += c;
                    } else {
                        cleantext += " ";
                    }
                }
                routput_.push_back("hit: " + cleantext);
            }
            routput_.push_back("");
        }
    } else {
        std::cerr << "No Literature selected!" << std::endl;
        exit(-1);
    }
}

BatchSearch::~BatchSearch() {
}
