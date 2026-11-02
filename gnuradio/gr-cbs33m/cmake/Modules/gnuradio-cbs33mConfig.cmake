find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_CBS33M gnuradio-cbs33m)

FIND_PATH(
    GR_CBS33M_INCLUDE_DIRS
    NAMES gnuradio/cbs33m/api.h
    HINTS $ENV{CBS33M_DIR}/include
        ${PC_CBS33M_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_CBS33M_LIBRARIES
    NAMES gnuradio-cbs33m
    HINTS $ENV{CBS33M_DIR}/lib
        ${PC_CBS33M_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-cbs33mTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_CBS33M DEFAULT_MSG GR_CBS33M_LIBRARIES GR_CBS33M_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_CBS33M_LIBRARIES GR_CBS33M_INCLUDE_DIRS)
