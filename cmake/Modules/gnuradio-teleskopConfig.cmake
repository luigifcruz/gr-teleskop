find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_TELESKOP gnuradio-teleskop)

FIND_PATH(
    GR_TELESKOP_INCLUDE_DIRS
    NAMES gnuradio/teleskop/api.h
    HINTS $ENV{TELESKOP_DIR}/include
        ${PC_TELESKOP_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_TELESKOP_LIBRARIES
    NAMES gnuradio-teleskop
    HINTS $ENV{TELESKOP_DIR}/lib
        ${PC_TELESKOP_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-teleskopTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_TELESKOP DEFAULT_MSG GR_TELESKOP_LIBRARIES GR_TELESKOP_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_TELESKOP_LIBRARIES GR_TELESKOP_INCLUDE_DIRS)
