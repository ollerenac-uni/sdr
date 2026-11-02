# Copyright 2020 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

########################################################################
# Check if there is C++ code at all
########################################################################
if(NOT cbs33m_sources)
    message(STATUS "No C++ sources... skipping python bindings")
    return()
endif(NOT cbs33m_sources)

########################################################################
# Check for pygccxml
########################################################################
gr_python_check_module_raw("pygccxml" "import pygccxml" PYGCCXML_FOUND)

include(GrPybind)

########################################################################
# Python Bindings
########################################################################

list(APPEND cbs33m_python_files python_bindings.cc)

gr_pybind_make_oot(cbs33m ../../.. gr::cbs33m "${cbs33m_python_files}")

# copy bindings extension for use in QA test module
add_custom_command(
    TARGET cbs33m_python
    POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:cbs33m_python>
            ${PROJECT_BINARY_DIR}/test_modules/gnuradio/cbs33m/)

install(
    TARGETS cbs33m_python
    DESTINATION ${GR_PYTHON_DIR}/gnuradio/cbs33m
    COMPONENT pythonapi)
