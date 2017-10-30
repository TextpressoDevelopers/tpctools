#!/bin/bash
cd /mnt/data1/textpresso/pgdumps
d=$(date +%Y%m%d)
pg_dump -U textpresso -F t www-data > www-data.$d.tar
gzip www-data.$d.tar 
