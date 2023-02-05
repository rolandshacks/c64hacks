#
# LibCpp64 build file
#

set(LIBCPP64_DIR ../libcpp64)
set(LIBCPP64_INCDIR ${LIBCPP64_DIR}/include)
set(LIBCPP64_SRCDIR ${LIBCPP64_DIR}/src)

include_directories(${LIBCPP64_INCDIR})

set(LIBCPP64_INCLUDES
    ${LIBCPP64_INCDIR}/memory
    ${LIBCPP64_INCDIR}/array
    ${LIBCPP64_INCDIR}/algorithm
    ${LIBCPP64_INCDIR}/sys
    ${LIBCPP64_INCDIR}/libcpp64/system.h
    ${LIBCPP64_INCDIR}/libcpp64/auxiliary.h
    ${LIBCPP64_INCDIR}/libcpp64/audio.h
    ${LIBCPP64_INCDIR}/libcpp64/video.h
    ${LIBCPP64_INCDIR}/libcpp64/keyboard.h
)

set(LIBCPP64_SOURCES
    ${LIBCPP64_INCLUDES}
    ${LIBCPP64_SRCDIR}/system.cpp
    ${LIBCPP64_SRCDIR}/auxiliary.cpp
    ${LIBCPP64_SRCDIR}/audio.cpp
    ${LIBCPP64_SRCDIR}/video.cpp
    ${LIBCPP64_SRCDIR}/keyboard.cpp
)

add_library(libcpp64 STATIC ${LIBCPP64_SOURCES})
