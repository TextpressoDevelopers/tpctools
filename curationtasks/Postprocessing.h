/* 
 * File:   Postprocessing.h
 * Author: mueller
 *
 * Created on February 15, 2017, 12:02 PM
 */

#ifndef POSTPROCESSING_H
#define	POSTPROCESSING_H

#include <string>
#include <vector>

class Postprocessing {
public:
    Postprocessing(std::string conditionname, const std::vector<std::string> & inp);
    Postprocessing(const Postprocessing& orig);
    virtual ~Postprocessing();
    std::vector<std::string> output() { return output_; }
private:
    std::vector<std::string> output_;
};

#endif	/* POSTPROCESSING_H */

