/* 
 * File:   BatchSearch.h
 * Author: mueller
 *
 * Created on February 9, 2017, 12:00 PM
 */

#ifndef BATCHSEARCH_H
#define	BATCHSEARCH_H

#include <string>
#include <map>
#include <set>
#include <vector>


class BatchSearch {
public:
    BatchSearch(std::string scope, std::string keyword,
        std::string keywordnot, bool categoriesanded,
        std::set<std::string> & pickedliterature,
        std::set<std::string> & pickedcat,
        std::map<std::string, std::string> & filters);
    virtual ~BatchSearch();
    std::vector<std::string> query() { return qoutput_; }
    std::vector<std::string> summary() { return soutput_; }
    std::vector<std::string> result() { return routput_; }
private:
    std::string scope_;
    std::set<std::string> pickedliterature_;
    std::string keyword_;
    std::string keywordnot_;
    bool categoriesanded_;
    std::set<std::string> pickedcat_;
    std::map<std::string, std::string> filters_;
    std::vector<std::string> qoutput_;
    std::vector<std::string> soutput_;
    std::vector<std::string> routput_;
    void doSearch();

};

#endif	/* BATCHSEARCH_H */