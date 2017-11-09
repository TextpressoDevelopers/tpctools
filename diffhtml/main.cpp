/* 
 * File:   main.cpp
 * Author: mueller
 *
 * Created on February 17, 2017, 12:22 PM
 */

/*
 * 
 */

#include <iostream>
#include <fstream>
#include <math.h>
#include <string>
#include <vector>
#include "cmdline.h"

#define MIN(x,y) ((x) < (y) ? (x) : (y))
#define MAXARRAY 250

int lev(std::string s, std::string t) {
    int d[MAXARRAY][MAXARRAY];
    int i, j, m, n, temp, tracker;
    m = MIN(s.length(), MAXARRAY - 1);
    n = MIN(t.length(), MAXARRAY - 1);
    for (i = 0; i <= m; i++)
        d[0][i] = i;
    for (j = 0; j <= n; j++)
        d[j][0] = j;
    for (j = 1; j <= m; j++) {
        for (i = 1; i <= n; i++) {
            if (s[i - 1] == t[j - 1]) {
                tracker = 0;
            } else {
                tracker = 1;
            }
            temp = MIN((d[i - 1][j] + 1), (d[i][j - 1] + 1));
            d[i][j] = MIN(temp, (d[i - 1][j - 1] + tracker));
        }
    }
    return d[n][m];
}

int main(int argc, char** argv) {
    cmdline::parser p;
    //
    std::string newfilename("");
    p.add<std::string> ("newfile", 'n', "file 1 to be compared", true);
    //
    std::string oldfilename("");
    p.add<std::string> ("oldfile", 'o', "file 2 to be compared", true);
    //
    int threshold(10);
    p.add<int>("threshold", 't', "levenshtein distance threshold", false, 10);
    p.set_program_name("diffhtml");
    p.footer(
            "\n\n"
            "Performs a diff on html outputs of curationtasks/\n"
            );
    if (argc < 2) {
        std::cerr << p.usage() << std::endl;
        return -1;
    }
    if (p.parse(argc, argv) == 0) {
        std::cerr << "Error:" << p.error() << std::endl
                << p.usage() << std::endl;
        return -1;
    }
    newfilename = p.get<std::string>("newfile");
    oldfilename = p.get<std::string>("oldfile");
    threshold = p.get<int>("threshold");
    try {
        std::string in;
        std::ifstream fold(oldfilename.c_str());
        std::vector<std::string> diffrecords;
        bool recording(false);
        std::string recordstring("");
        while (getline(fold, in)) {
            if (in.find("<!-HTMLDIFFEND->") != std::string::npos) {
                diffrecords.push_back(recordstring);
                recordstring = "";
                recording = false;
            }
            if (recording) recordstring += in + "\n";
            if (in.find("<!-HTMLDIFFSTART->") != std::string::npos) recording = true;
        }
        fold.close();
        //
        std::ifstream fnew(newfilename.c_str());
        recording = false;
        recordstring = "";
        while (getline(fnew, in)) {
            if (in.find("<!-HTMLDIFFEND->") != std::string::npos) {
                bool printout(true);
                for (std::vector<std::string>::iterator it = diffrecords.begin(); it != diffrecords.end(); it++) {
                    if (lev(recordstring, *it) < threshold) {
                        printout = false;
                        break;
                    }
                }
                if (printout) std::cout << recordstring << std::endl;
                recordstring = "";
                recording = false;
            }
            if (recording)
                recordstring += in + "\n";
            else if (in.find("<!-HTMLDIFF") == std::string::npos)
                std::cout << in << std::endl;
            if (in.find("<!-HTMLDIFFSTART->") != std::string::npos) recording = true;
        }
        fnew.close();
        //
    } catch (std::string & errorMessage) {
        std::cerr << errorMessage << std::endl;
        return -1;
    }
    return 0;
}
