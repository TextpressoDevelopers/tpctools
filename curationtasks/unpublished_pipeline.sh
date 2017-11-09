#!/usr/bin/env bash

export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/lib
export PATH=$PATH:/usr/local/lib

IFS=$(echo -en "\n\b")
date=$(date +%Y%m%d)
curationtasks --keyword "Unpublished OR (\"data not shown\")" --literature "C. elegans, C. elegans Supplementals" -r daniela > /var/www/html/curators/daniela/unpublished/${date}.html
diffhtml -n /var/www/html/curators/daniela/unpublished/${date}.html -o /var/www/html/curators/daniela/unpublished/last.html > /var/www/html/curators/daniela/unpublished/d${date}.html
rm /var/www/html/curators/daniela/unpublished/last.html
ln -s /var/www/html/curators/daniela/unpublished/${date}.html /var/www/html/curators/daniela/unpublished/last.html
if [ -n "$(grep hit: /var/www/html/curators/daniela/unpublished/d${date}.html)" ];
then
    echo "New results about your keyword search \"Unpublished OR (\"data not shown\")\" are available at https://textpressocentral.org/unpublished/d${date}. All results can be found at https://textpressocentral.org/unpublished/." | mail -s "Cronjob Alert" valearna@caltech.edu,mueller@caltech.edu,draciti@caltech.edu,karen@wormbase.org
fi