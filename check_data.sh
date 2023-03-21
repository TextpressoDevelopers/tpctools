#!/usr/bin/env bash

function set_colors {
# Reset
Color_Off='\033[0m'       # Text Reset

# Regular Colors
Black='\033[0;30m'        # Black
Red='\033[0;31m'          # Red
Green='\033[0;32m'        # Green
Yellow='\033[0;33m'       # Yellow
Blue='\033[0;34m'         # Blue
Purple='\033[0;35m'       # Purple
Cyan='\033[0;36m'         # Cyan
White='\033[0;37m'        # White

# Bold
BBlack='\033[1;30m'       # Black
BRed='\033[1;31m'         # Red
BGreen='\033[1;32m'       # Green
BYellow='\033[1;33m'      # Yellow
BBlue='\033[1;34m'        # Blue
BPurple='\033[1;35m'      # Purple
BCyan='\033[1;36m'        # Cyan
BWhite='\033[1;37m'       # White

# Underline
UBlack='\033[4;30m'       # Black
URed='\033[4;31m'         # Red
UGreen='\033[4;32m'       # Green
UYellow='\033[4;33m'      # Yellow
UBlue='\033[4;34m'        # Blue
UPurple='\033[4;35m'      # Purple
UCyan='\033[4;36m'        # Cyan
UWhite='\033[4;37m'       # White

# Background
On_Black='\033[40m'       # Black
On_Red='\033[41m'         # Red
On_Green='\033[42m'       # Green
On_Yellow='\033[43m'      # Yellow
On_Blue='\033[44m'        # Blue
On_Purple='\033[45m'      # Purple
On_Cyan='\033[46m'        # Cyan
On_White='\033[47m'       # White

# High Intensity
IBlack='\033[0;90m'       # Black
IRed='\033[0;91m'         # Red
IGreen='\033[0;92m'       # Green
IYellow='\033[0;93m'      # Yellow
IBlue='\033[0;94m'        # Blue
IPurple='\033[0;95m'      # Purple
ICyan='\033[0;96m'        # Cyan
IWhite='\033[0;97m'       # White

# Bold High Intensity
BIBlack='\033[1;90m'      # Black
BIRed='\033[1;91m'        # Red
BIGreen='\033[1;92m'      # Green
BIYellow='\033[1;93m'     # Yellow
BIBlue='\033[1;94m'       # Blue
BIPurple='\033[1;95m'     # Purple
BICyan='\033[1;96m'       # Cyan
BIWhite='\033[1;97m'      # White

# High Intensity backgrounds
On_IBlack='\033[0;100m'   # Black
On_IRed='\033[0;101m'     # Red
On_IGreen='\033[0;102m'   # Green
On_IYellow='\033[0;103m'  # Yellow
On_IBlue='\033[0;104m'    # Blue
On_IPurple='\033[0;105m'  # Purple
On_ICyan='\033[0;106m'    # Cyan
On_IWhite='\033[0;107m'   # White
}

function usage {
    echo "This script checks incomining data for validity and completeness."
    echo
    echo "usage: $(basename $0) [-ith]"
    echo "  -i --incoming     check incoming data"
    echo "  -t --text         check text conversion"
    echo "  -1 --phase1       check first phase of processing"
    echo "  -2 --phase2       check second phase of processing"
    echo "  -h --help         display help"
    rm ${LOCKFILE}
    exit 1
}

function check_incoming {
    if [[ ! -d "${ROOT_DIR}/oboheaderfiles" ]]
    then
	echo -e "${Red}${ROOT_DIR}/oboheaderfiles does not exist.${Color_Off}"
	EXIT=1
    else
	if [[ -z "$(ls -A ${ROOT_DIR}/oboheaderfiles)" ]]
	then	
	    echo -e "${Yellow}${ROOT_DIR}/oboheaderfiles is empty.${Color_Off}"
	    EXIT=1
	else
	    echo -e "${Green}${ROOT_DIR}/oboheaderfiles is valid.${Color_Off}"
	fi
    fi
    #
    if [[ ! -d "${ROOT_DIR}/obofiles4production" ]]
    then
	echo -e "${Red}${ROOT_DIR}/obofiles4production does not exist.${Color_Off}"
    else
	if [[ -z "$(ls -A ${ROOT_DIR}/obofiles4production)" ]]
	then	
	    echo -e "${Yellow}${ROOT_DIR}/obofiles4production is empty.${Color_Off}"
	else
	    echo -e "${Green}${ROOT_DIR}/obofiles4production is valid.${Color_Off}"
	fi
    fi
    #
    IFS=$'\n'
    BIBLIST=$(find "${ROOT_DIR}/raw_files/bib/" -name "*bib")
    for i in $(find "${ROOT_DIR}/raw_files/pdf/" -name "*pdf")
    do
	k=$(echo "$i" | sed 's/pdf/bib/g')
	if [[ ! "$BIBLIST" =~ "$k" ]]
	then
	    echo -e "${Red}Bib file for $i missing.${Color_Off}"
	    EXIT=1
	fi
    done
    #    
}

function check_text_conversion {
    IFS=$'\n'
    for d in $(find "${ROOT_DIR}/raw_files/pdf/" -name "*.pdf" | xargs -I {} dirname {})
    do
	if [[ -z "$(ls -A ${d}/*.txt 2>/dev/null)" ]]
	then
	 echo -e "${Yellow}No converted text in ${ROOT_DIR}/${d}.${Color_Off}"
	fi
    done
}

function check_cas1 {
    IFS=$'\n'
    for i in $(find "${ROOT_DIR}/raw_files/pdf/" -name "*.pdf" | xargs -I {} dirname {} | sed 's#/data/textpresso/raw_files/pdf/##'g)
    do
	if [[ -z "$(ls -A ${ROOT_DIR}/tpcas-1/${i}/*.tpcas.gz 2>/dev/null)" ]]
	then
        echo -e "${Yellow}Phase 1 not completed in ${ROOT_DIR}/tpcas-1/${i}.${Color_Off}"
	fi
    done
}

function check_cas2 {
    IFS=$'\n'
    for i in $(find "${ROOT_DIR}/raw_files/pdf/" -name "*.pdf" | xargs -I {} dirname {} | sed 's#/data/textpresso/raw_files/pdf/##'g)
    do
	if [[ -z "$(ls -A ${ROOT_DIR}/tpcas-2/${i}/*.tpcas.gz 2>/dev/null)" ]]
	then
        echo -e "${Yellow}Phase 1 not completed in ${ROOT_DIR}/tpcas-2/${i}.${Color_Off}"
	fi
    done
}

set_colors
EXIT=0
ROOT_DIR="/data/textpresso"
LOCKFILE="/tmp/check_incoming.lock"
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
            -i|--incoming)
                shift
                check_incoming
                ;;
            -t|--text)
                shift
                check_text_conversion
                ;;
            -1|--phase1)
                shift
                check_cas1
                ;;
            -2|--phase2)
                shift
                check_cas2
                ;;
	    -h|--help)
		usage
		;;
	    *)
		echo
		echo -e ${Red}"wrong argument: $key"${Color_Off}
		echo
		usage
	esac
    done
    #
    rm ${LOCKFILE}
fi
exit $EXIT
