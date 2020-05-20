#!/bin/bash
cd /data/textpresso/pgdumps
d=$(date +%Y%m%d)
pg_dump -F t -T "pcrelation*" -T "tpontology*" -T ontologymembers  www-data > www-data.$d.tar
gzip www-data.$d.tar
