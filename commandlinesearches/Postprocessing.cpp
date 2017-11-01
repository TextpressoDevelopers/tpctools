/* 
 * File:   Postprocessing.cpp
 * Author: mueller
 * 
 * Created on February 15, 2017, 12:02 PM
 */

#include "Postprocessing.h"
#include <boost/regex.hpp>

Postprocessing::Postprocessing(std::string conditionname, const std::vector<std::string> & inp) {
    if (conditionname.compare("unpublished") == 0) {
        boost::regex hit("^hit: .+");
        boost::regex unpublished(".*[uU]npublished.*");
        boost::regex datanotshown(".*[dD]ata\\s[nN]ot\\s[sS]hown.*");
        std::vector<std::string> oneresult;
        bool keep(false);
        for (std::vector<std::string>::const_iterator it = inp.begin(); it != inp.end(); it++) {
            oneresult.push_back(*it);
            oneresult.back() = boost::regex_replace(oneresult.back(), boost::regex("\\s+"), " ");
            if (boost::regex_match(*it, hit))
                if (boost::regex_match(*it, unpublished) || boost::regex_match(*it, datanotshown))
                    keep = true;
            if ((*it).empty()) {
                if (keep)
                    for (std::vector<std::string>::iterator itc = oneresult.begin();
                            itc != oneresult.end(); itc++)
                        if (!boost::regex_match(*itc, hit))
                            output_.push_back(*itc);
                        else if (boost::regex_match(*itc, unpublished) || boost::regex_match(*itc, datanotshown))
                            output_.push_back(*itc);
                oneresult.clear();
                keep = false;
            }
        }
    }
    if (conditionname.compare("daniela") == 0) {
        boost::regex unpublished("([uU]npublished)");
        boost::regex datanotshown("([dD]ata\\s+[nN]ot\\s+[sS]hown)");
        boost::regex wbpaper("(WBPaper\\d+)");
        boost::regex matchunpublished(".*[uU]npublished.*");
        boost::regex matchdatanotshown(".*[dD]ata\\s+[nN]ot\\s+[sS]hown.*");
        boost::regex matchwbpaper(".*WBPaper.*");
        boost::regex matchaccession("accession:.*");
        output_.clear();
        output_.push_back("<html><body>");
        bool diffable(false);
        bool keep(true);
        std::vector<std::string> oneresult;
        for (std::vector<std::string>::const_iterator it = inp.begin(); it != inp.end(); it++) {
            std::string aux(*it);
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

                for (std::vector<std::string>::iterator itc = oneresult.begin();
                        itc != oneresult.end(); itc++)
                        output_.push_back(*itc);
                        oneresult.clear();
                }
        }
        output_.push_back("</body></html>");
    }
}

Postprocessing::Postprocessing(const Postprocessing & orig) {
}

Postprocessing::~Postprocessing() {
}
