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

find_package(CImg REQUIRED)
include_directories(${CImg_INCLUDE_DIRS})

find_package(Lucene++ REQUIRED)
include_directories(${Lucene++_INCLUDE_DIRS})

find_package(Textpresso REQUIRED)
include_directories(${Textpresso_INCLUDE_DIR})

include_directories("/home/valerio/workspace/caltech/libtpc")

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

add_executable(getbib getbib/getbib.cpp getbib/getbibUtils.h getbib/getbibUtils.cpp
        TextpressoCentralGlobalDefinitions.h TextpressoCentralGlobals.h)
target_link_libraries(getbib lucene++ xerces-c icuuc boost_system uima boost_filesystem boost_iostreams)

add_executable(getbib4nxml getbib/getbib4nxml.cpp getbib/getbib4nxmlUtils.h getbib/getbib4nxmlUtils.cpp
        TextpressoCentralGlobalDefinitions.h TextpressoCentralGlobals.h)
target_link_libraries(getbib4nxml lucene++ xerces-c icuuc boost_system uima boost_filesystem boost_iostreams)

add_executable(saveidstodb cas2index/saveidstodb.cpp)
target_link_libraries(saveidstodb lucene++ boost_filesystem boost_system boost_program_options ${Textpresso_LIBRARY}
        db_cxx db_stl)

#### INSTALL ####

install(TARGETS getbib getbib4nxml
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib)

install(TARGETS cas2index RUNTIME DESTINATION ${CMAKE_INSTALL_PREFIX}/bin)
install(TARGETS saveidstodb RUNTIME DESTINATION ${CMAKE_INSTALL_PREFIX}/bin)
install(TARGETS updatecorpuscounter RUNTIME DESTINATION ${CMAKE_INSTALL_PREFIX}/bin)
install(PROGRAMS cas2index/create_index_multi_literatures.sh cas2index/create_single_index.sh
        ppm2jpg/ppm2jpgCas.sh run_tpc_pipeline_incremental.sh
        getpdfs/getpdfs.py getbibinfoforpdffromserver/download_pdfinfo.pl
        getbibinfoforpdffromserver/extract_pdfbibinfo.pl
        DESTINATION ${CMAKE_INSTALL_PREFIX}/bin)

install(TARGETS articles2cas RUNTIME DESTINATION ${CMAKE_INSTALL_PREFIX}/bin)
install(PROGRAMS articles2cas/convertallarticles2cas.sh
        DESTINATION ${CMAKE_INSTALL_PREFIX}/bin)



