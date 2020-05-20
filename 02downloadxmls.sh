#!/usr/bin/env bash

function usage {
    echo "this script downloads articles from PMCOA."
    echo
    echo "usage: $(basename $0) [-xfh]"
    echo "  -x --xml-dir      directory where raw xml files will be stored"
    echo "  -f --ftp-dir      ftp mount point for pmcoa papers"
    echo "  -h --help         display help"
    rm ${LOCKFILE}
    exit 1
}

XML_DIR="/data/textpresso/raw_files/xml"
FTP_MNTPNT="/mnt/pmc_ftp"
LOCKFILE="/data/textpresso/tmp/02downloadxmls.lock"
if [[ -f "${LOCKFILE}" ]]
then   
    echo $(basename $0) "is already running."
    exit 1
else
    touch "${LOCKFILE}"        
    while [[ $# -gt 0 ]]
    do
	key=$1
	
	case $key in
	    -x|--xml-dir)
		shift
		XML_DIR="$1"
		shift
		;;
	    -f|--ftp-dir)
		shift
		FTP_MNTPNT="$1"
		shift
		;;
	    -h|--help)
		usage
		;;
	    *)
		echo "wrong argument: $key"
		echo
		usage
	esac
    done
    
    export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/lib
    export PATH=$PATH:/usr/local/bin
    
    # temp files
    logfile=$(mktemp)
    
    echo "Downloading xml papers ..."
    # 1.1 XML FROM PMCOA
    
    # 1.1.1 create directory for unclassified xml files
    mkdir -p ${XML_DIR}
    mkdir -p ${FTP_MNTPNT}
    # 1.1.2 mount pmcoa ftp locally through curl
    curlftpfs ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/ ${FTP_MNTPNT}
    
    for k in ${FTP_MNTPNT}/*
    do
	for j in $k/*
	do
	    for i in $j/*
	    do
		d=$(basename $(echo $i | sed 's/.tar.gz//'))
		echo $d
		if [[ $i -nt ${XML_DIR}/$d ]]
		then
		    echo $d >> ${logfile}
		    mkdir ${XML_DIR}/$d
		    touch -t 196901010000 ${XML_DIR}/$d
		    if
			rsync --timeout=600 -a $i ${XML_DIR}/$d/.
			tar xfz ${XML_DIR}/$d/$d.tar.gz --exclude="*.pdf" --exclude="*.PDF" \
			    --exclude="*.mp4" --exclude="*.webm" --exclude="*.flv" \
			    --exclude="*.avi" --exclude="*.zip" --exclude="*.mov" \
			    --exclude="*.csv" --exclude="*.xls*" --exclude="*.doc*" \
			    --exclude="*.ppt*" --exclude="*.rar" --exclude="*.txt" \
			    --exclude="*.TXT" --exclude="*.wmv" --exclude="*.DOC*" \
			    -C "${XML_DIR}"
			rm -f ${XML_DIR}/$d/$d.tar.gz
			mkdir ${XML_DIR}/$d/images
			ls ${XML_DIR}/$d | grep -v \.nxml | grep -v images | xargs -I "{}" mv ${XML_DIR}/$d/{} ${XML_DIR}/$d/images/
			gzip -f ${XML_DIR}/$d/*.nxml
		    then
			touch -r $i ${XML_DIR}/$d/
		    fi
		fi
	    done
	done
    done
    umount ${FTP_MNTPNT}
    rm ${logfile}
    rm ${LOCKFILE}
fi
