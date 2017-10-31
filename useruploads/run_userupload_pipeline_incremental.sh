#!/usr/bin/env bash

USERUPLOADS_DIR="/usr/local/textpresso/useruploads"
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/lib
export PATH=$PATH:/usr/local/lib

if [[ $(ls ${USERUPLOADS_DIR} | wc -l) != "0" ]]
then
    for user_dir in ${USERUPLOADS_DIR}/*
    do
        cd ${user_dir}
        username=${PWD##*/}
        mkdir -p ${user_dir}/tpcas
        mkdir -p ${user_dir}/tmp/cas1
        mkdir -p ${user_dir}/tmp/cas2
        mkdir -p ${user_dir}/useruploads/${username}
        touch ${user_dir}/tpcas/processed_files.txt
        touch ${user_dir}/tpcas/tokenized_files.txt
        tmpfile=$(mktemp)
        grep -vxf ${user_dir}/tpcas/processed_files.txt <(ls -1 ${user_dir}/uploadedfiles) > ${tmpfile}
        if [[ $(grep ".pdf" ${tmpfile} | wc -l | awk '{print $1}') != "0" ]]
        then
            articles2cas -t 1 -i uploadedfiles -o useruploads/${username} -L <(grep ".pdf" ${tmpfile})
        fi
        if [[ $(grep ".nxml" ${tmpfile} | wc -l | awk '{print $1}') != "0" ]]
        then
            articles2cas -t 2 -i ${user_dir}/uploadedfiles -o useruploads/${username} -L <(grep ".nxml" ${tmpfile})
        fi
        # TODO process compressed archives
        if [[ $(ls useruploads/${username}/ | wc -l) != "0" ]]
        then
            mv useruploads/${username}/* ${user_dir}/tpcas/
        fi
        rm -rf useruploads
        cat ${tmpfile} >> ${user_dir}/tpcas/tokenized_files.txt
        grep -xf <(sed -e 's/\.[^.]*$//' ${tmpfile}) <(ls ${user_dir}/tpcas/) | xargs -I {} cp ${user_dir}/tpcas/{}/{}.tpcas  ${user_dir}/tmp/cas1
        if [[ $(ls ${user_dir}/tmp/cas1/ | wc -l | awk '{print $0}') != "0" ]]
        then
            runAECpp /usr/local/uima_descriptors/TpLexiconAnnotatorFromPg.xml -xmi ${user_dir}/tmp/cas1 ${user_dir}/tmp/cas2
        fi
        if [[ $(ls ${user_dir}/tmp/cas2/ | wc -l) != "0" ]]
        then
            for tpcas2_file in $(ls ${user_dir}/tmp/cas2/*)
            do
                mv ${tpcas2_file} ${user_dir}/tpcas/$(basename ${tpcas2_file} | sed -e 's/\.[^.]*$//')
                if [[ -f ${user_dir}/uploadedfiles/$(basename ${tpcas2_file} | sed -e 's/\.[^.]*$//').bib ]]
                then
                    cp ${user_dir}/uploadedfiles/$(basename ${tpcas2_file} | sed -e 's/\.[^.]*$//').bib ${user_dir}/tpcas/$(basename ${tpcas2_file} | sed -e 's/\.[^.]*$//')
                fi
                gzip ${user_dir}/tpcas/$(basename ${tpcas2_file} | sed -e 's/\.[^.]*$//')/$(basename ${tpcas2_file})
            done
        fi
        rm -rf ${user_dir}/tmp/
        mkdir -p /usr/local/textpresso/tpcas/useruploads/${username}
        cd tpcas
        grep -xf <(sed -e 's/\.[^.]*$//' ${tmpfile}) <(find . -mindepth 1 -maxdepth 1 -type d | awk -F"/" '{print $NF}') | while read line
        do
            casfilename=$(ls ${line}/*.tpcas.gz)
            bibfilename="${casfilename/.tpcas.gz/.bib}"
            if [[ ! -f ${bibfilename} ]]
            then
                echo -e "author|<not uploaded>\naccession|<not uploaded>\ntype|<not uploaded>\ntitle|<not uploaded>\njournal|<not uploaded>\ncitation|<not uploaded>\nyear|<not uploaded>\nabstract|<not uploaded>" > ${bibfilename}
            fi
        done
        grep -xf <(sed -e 's/\.[^.]*$//' ${tmpfile}) <(find . -mindepth 1 -maxdepth 1 -type d | awk -F"/" '{print $NF}') | while read line
        do
            rm -rf "/usr/local/textpresso/tpcas/useruploads/${username}/${line}"
            ln -s "${user_dir}/tpcas/${line}" "/usr/local/textpresso/tpcas/useruploads/${username}/${line}"
        done
        cat ${tmpfile} >> ${user_dir}/tpcas/processed_files.txt
        rm ${tmpfile}
        if [[ ! -d ${user_dir}/luceneindex && $(wc -l "${user_dir}/tpcas/processed_files.txt" | awk '{print $1}') -gt 1 ]]
        then
            mkdir -p ${user_dir}/luceneindex
            cas2index -i ${user_dir}/tpcas -o ${user_dir}/luceneindex -s 300000 -e
            mkdir ${user_dir}/luceneindex/db
            saveidstodb -i ${user_dir}/luceneindex
            chmod -R 777 ${user_dir}/luceneindex/db
        fi
    done
fi

chown -R www-data:www-data ${USERUPLOADS_DIR}