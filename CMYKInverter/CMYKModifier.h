/* 
 * File:   CMYKModifier.h
 * Author: mueller
 *
 * Created on June 19, 2014, 4:46 PM
 */

#ifndef CMYKMODIFIER_H
#define	CMYKMODIFIER_H

class CMYKModifier {
public:
    CMYKModifier(const char * pFilename);
    bool IsCMYK() { return colorspaceiscmyk_; }
private:
    bool colorspaceiscmyk_;
};

#endif	/* CMYKMODIFIER_H */

