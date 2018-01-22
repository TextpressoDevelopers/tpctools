# Tpctools
## Description
This project is a collection of tools for the management of Textpresso Central project.

Textpressocentral is a platform to perform full text literature searches, view and curate research papers, 
train and apply machine learning (ML) and text mining (TM) algorithm for semantic analysis and curation purposes. 
The user is supported in this task by giving him capabilities to select, edit and store lists of papers, sentences, 
term and categories in order to perform training and mining. The system is designed with the intent to empower the user 
to perform as many operations on a literature corpus or a particular paper as possible. It uses state-of-the-art 
software packages and frameworks such as the Unstructured Information Management Architecture (UIMA), Lucene and Wt. 
The corpus of papers can be build from fulltext articles that are available in PDF or NXML format.

## Installation
### Dependencies

libtpc must be installed in the system.
 
---
**NOTE**

cmake version >= 3.5 is required.

---

### Compile and Install tpctools
To compile and install the project, run the following commands from the root directory of the repository:
```{r, engine='bash', count_lines}
$ mkdir cmake-build-release && cd cmake-build-release
$ cmake -DCMAKE_BUILD_TYPE=Release ..
$ make && make install
```

This will install the tools in the default location (/usr/local/).

### Debugging
The project can be also compiled and installed in debug mode, with the following commands:
```{r, engine='bash', count_lines}
$ mkdir cmake-build-debug && cd cmake-build-debug
$ cmake -DCMAKE_BUILD_TYPE=Debug ..
$ make && make install
```

### Install libtpc on Textpresso Docker image
Texpresso provides a Docker image with all the required dependencies pre-installed. To build it and run it, follow the
README file in libtpc project.
