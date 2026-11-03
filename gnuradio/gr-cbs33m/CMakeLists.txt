# SPDX-License-Identifier: GPL-3.0-or-later
# Este módulo contiene únicamente bloques Python y descripciones de GRC.
cmake_minimum_required(VERSION 3.16)
project(gr-cbs33m VERSION 1.0 LANGUAGES NONE)

# Compatibilidad con el argumento usado por las plantillas de gr_modtool.
if(DEFINED PYTHON_EXECUTABLE AND NOT DEFINED Python3_EXECUTABLE)
    set(Python3_EXECUTABLE "${PYTHON_EXECUTABLE}")
endif()
find_package(Python3 3.8 REQUIRED COMPONENTS Interpreter)

execute_process(
    COMMAND "${Python3_EXECUTABLE}" -c "from gnuradio import gr; print(gr.version())"
    RESULT_VARIABLE CBS33M_IMPORT_RESULT
    OUTPUT_VARIABLE CBS33M_GNURADIO_VERSION
    ERROR_VARIABLE CBS33M_IMPORT_ERROR
    OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT CBS33M_IMPORT_RESULT EQUAL 0)
    message(FATAL_ERROR "El Python seleccionado no importa GNU Radio: ${CBS33M_IMPORT_ERROR}")
endif()
message(STATUS "GNU Radio ${CBS33M_GNURADIO_VERSION}; Python ${Python3_EXECUTABLE}")

# La ruta relativa permite también instalar en un prefijo temporal para pruebas.
execute_process(
    COMMAND "${Python3_EXECUTABLE}" -c "import os, sys, sysconfig; print(os.path.relpath(sysconfig.get_path('purelib'), sys.prefix))"
    RESULT_VARIABLE CBS33M_PATH_RESULT
    OUTPUT_VARIABLE CBS33M_SITE_PACKAGES
    OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT CBS33M_PATH_RESULT EQUAL 0 OR IS_ABSOLUTE "${CBS33M_SITE_PACKAGES}" OR CBS33M_SITE_PACKAGES MATCHES "^\\.\\.")
    message(FATAL_ERROR "No se pudo determinar site-packages dentro del prefijo de Python")
endif()
set(CBS33M_PYTHON_DIR "${CBS33M_SITE_PACKAGES}/gnuradio/cbs33m")

include(CTest)
add_subdirectory(python/cbs33m)
add_subdirectory(grc)
install(FILES MANIFEST.yml DESTINATION share/gnuradio/manifests/cbs33m)
