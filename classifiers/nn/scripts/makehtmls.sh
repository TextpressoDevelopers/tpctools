#!/usr/bin/env bash
INDIR=$1;
OUTDIR=$2;
for i in $(find "$INDIR" -type d)
do
    mkdir -p "$OUTDIR"/${i##"$INDIR"}
done
for i in $(find "$INDIR" -type f)
do
    OUT="$OUTDIR/"${i##"$INDIR"}".html"
    echo "<html>" > $OUT
    echo "<body>" >> $OUT
    while read line
    do
	echo $line | cut -f 1,8,9 -d "/" | cut -f 1 -d "." | sed 's#/#XXX#' \
	    | sed 's#/#">#' | sed 's#$#</a><br>#' \
            | sed 's#XXX#<a target="_blank" href="http://tazendra.caltech.edu/~azurebrd/cgi-bin/forms/paper_display.cgi?action=Search+!\&data_number=#'\
	    | sed 's/^0 /NEG    /' \
	    | sed 's/^1 /LOW    /' \
	    | sed 's/^2 /LOW    /' \
	    | sed 's/^3 /LOW    /' \
	    | sed 's/^4 /LOW    /' \
	    | sed 's/^5 /MEDIUM /' \
	    | sed 's/^6 /MEDIUM /' \
	    | sed 's/^7 /MEDIUM /' \
	    | sed 's/^8 /HIGH   /' \
	    | sed 's/^9 /HIGH   /' \
	    | sed 's/^10 /HIGH   /'
    done <$i >> $OUT
    echo "</body>" >> $OUT
    echo "</html>" >> $OUT
done
