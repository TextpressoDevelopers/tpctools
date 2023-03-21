cmake_minimum_required(VERSION 3.5)
project(tpctools)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake/Modules/")
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON) #...is required...
set(CMAKE_CXX_FLAGS "-DBOOST_NO_CXX11_SCOPED_ENUMS -w")

set(CMAKE_STATIC_LIBRARY_PREFIX "") # avoid the prefix "lib"
set(CMAKE_SHARED_LIBRARY_PREFIX "")

SET(CMAKE_INSTALL_PREFIX /usr/local)
SET(CMAKE_SKIP_BUILD_RPATH  FALSE)
SET(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE)
set(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

find_package(APR REQUIRED)
include_directories(${APR_INCLUDE_DIR})

find_package(ImageMagick COMPONENTS Magick++)
include_directories(${ImageMagick_INCLUDE_DIRS})

find_package(CImg REQUIRED)
include_directories(${CImg_INCLUDE_DIRS})

find_package(Lucene++ REQUIRED)
include_directories(${Lucene++_INCLUDE_DIRS})

find_package(Textpresso REQUIRED)
include_directories(${Textpresso_INCLUDE_DIR})

# uncomment this line to debug library
include_directories("/home/valerio/workspace/caltech/textpresso/libtpc")

#### Main projects ####

add_executable(printbibfromnxmlorcasfile printbibfromnxmlorcasfile/main.cpp printbibfromnxmlorcasfile/cmdline.h)
target_link_libraries(printbibfromnxmlorcasfile uima xerces-c boost_system boost_filesystem boost_iostreams
        boost_regex)

#### Subprojects ####

add_executable(ppm2jpg ppm2jpg/main.cpp)
target_link_libraries(ppm2jpg boost_system boost_filesystem boost_program_options pthread ${CImg_SYSTEM_LIBS})

add_executable(cas2index cas2index/cas2index.cpp)
target_link_libraries(cas2index ${Textpresso_LIBRARY} boost_filesystem boost_system boost_program_options lucene++)

add_executable(updatecorpuscounter cas2index/update_corpus_counter.cpp)
target_link_libraries(updatecorpuscounter ${Textpresso_LIBRARY} boost_filesystem boost_system boost_program_options
        lucene++)

add_executable(indexmerger cas2index/index_merger.cpp lucene/CaseSensitiveAnalyzer.cpp)
target_link_libraries(indexmerger uima boost_filesystem boost_system lucene++)

add_executable(articles2cas articles2cas/articles2cas.cpp articles2cas/Utils.h articles2cas/Utils.cpp)
target_link_libraries(articles2cas ${Textpresso_LIBRARY} boost_filesystem boost_system boost_program_options boost_iostreams)

add_executable(downloadpdf downloadpdf/downloadpdf.cpp)
target_link_libraries(downloadpdf xerces-c boost_program_options boost_filesystem boost_system curl pthread)

add_executable(getbib getbib/getbib.cpp getbib/getbibUtils.h getbib/getbibUtils.cpp
        TextpressoCentralGlobalDefinitions.h TextpressoCentralGlobals.h)
target_link_libraries(getbib lucene++ xerces-c icuuc boost_system uima boost_filesystem boost_iostreams)

add_executable(getbib4nxml getbib/getbib4nxml.cpp getbib/getbib4nxmlUtils.h getbib/getbib4nxmlUtils.cpp
        TextpressoCentralGlobalDefinitions.h TextpressoCentralGlobals.h)
target_link_libraries(getbib4nxml lucene++ xerces-c icuuc boost_system uima boost_filesystem boost_iostreams
        boost_program_options)

add_executable(saveidstodb cas2index/saveidstodb.cpp)
target_link_libraries(saveidstodb lucene++ boost_filesystem boost_system boost_program_options ${Textpresso_LIBRARY}
        db_cxx db_stl)

add_executable(cmykinverter CMYKInverter/CMYKModifier.h CMYKInverter/CMYKModifier.cpp CMYKInverter/main.cpp)
target_link_libraries(cmykinverter ${ImageMagick_LIBRARIES} boost_system boost_filesystem)

add_executable(curationtasks curationtasks/main.cpp)
target_link_libraries(curationtasks lucene++ boost_filesystem boost_system boost_regex boost_program_options
        ${Textpresso_LIBRARY})

add_executable(diffhtml diffhtml/main.cpp diffhtml/cmdline.h)

#### INSTALL ####

install(TARGETS downloadpdf getbib getbib4nxml cas2index saveidstodb updatecorpuscounter articles2cas
        curationtasks diffhtml cmykinverter indexmerger
        RUNTIME DESTINATION ${CMAKE_INSTALL_PREFIX}/bin LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX}/lib)
install(PROGRAMS cas2index/create_index_multi_literatures.sh cas2index/create_single_index.sh
        ppm2jpg/ppm2jpgCas.sh run_tpc_pipeline_incremental.sh combinepdfs.sh tai.sh 03catch.non-conv.pdfs.4.cas1.sh
        01downloadpdfs.sh 01downloadpdfs4tai.sh 02downloadxmls.sh 03pdf2cas.sh 03pdf2cas4tai.sh 04xml2cas.sh 
        05addimages2cas1.sh 06removecas1.sh 07cas1tocas2.sh 08removecas2.sh 09getpmcoabib.sh   
        10getcelegansbib.sh 11invertimages.sh 12index.sh check_data.sh
	classifiers/nn/scripts/01computeceleganswordmodel.sh classifiers/nn/scripts/02createcelegansdocvectors.sh
        classifiers/nn/scripts/01computewordmodel.sh classifiers/nn/scripts/02createdocvectors.sh   
	classifiers/nn/scripts/03makelist.sh classifiers/nn/scripts/04classify.sh classifiers/nn/scripts/cleancas.pl
	classifiers/nn/scripts/nxmlfil.pl classifiers/nn/scripts/pdfclean.pl classifiers/nn/scripts/wikifil.pl
        classifiers/nn/scripts/makehtmls.sh getpdfs/getpdfs.py getbibinfoforpdffromserver/download_pdfinfo.pl
        getbibinfoforpdffromserver/extract_pdfbibinfo.pl useruploads/run_userupload_pipeline_incremental.sh
	useruploads/uulcas1tocas2.bash
        pgdumps/dump.sh articles2cas/convertallarticles2cas.sh curationtasks/unpublished_pipeline.sh
        getbib/getallbibfiles.sh getbib/download_abstract.py getbib/make_bib.py
        DESTINATION ${CMAKE_INSTALL_PREFIX}/bin)
install(FILES SupplMatCoverSheet.pdf DESTINATION ${CMAKE_INSTALL_PREFIX}/etc)
