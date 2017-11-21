/* 
 * File:   CMYKModifier.cpp
 * Author: mueller
 * 
 * Created on June 19, 2014, 4:46 PM
 */
#include "CMYKModifier.h"
#include <Magick++.h>
#include <boost/filesystem.hpp>

CMYKModifier::CMYKModifier(const char * pFilename) {
    if (boost::filesystem::exists(pFilename)) {
        Magick::Image image;
        image.read(pFilename);
        if (image.colorSpace() == Magick::CMYKColorspace) {
            image.negate(false);
            colorspaceiscmyk_ = true;
            image.write(pFilename);
        } else {
            colorspaceiscmyk_ = false;
        }
    }
}

