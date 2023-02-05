#
# Project build file
#

STRING(TOLOWER ${CMAKE_BUILD_TYPE} BUILD_TYPE)

set(LLVM_MOS_PLATFORM               c64)
set(CMAKE_CXX_STANDARD              20)
set(ENABLE_DEBUG_INFO               ON)
set(ENABLE_MEMORY_MAP               OFF)

if("${BUILD_TYPE}" STREQUAL "debug")
set(ENABLE_OPTIMIZATION             OFF)
else()
set(ENABLE_OPTIMIZATION             ON)
endif()

if(${ENABLE_OPTIMIZATION})
    add_compile_options(-Ofast)
else()
    add_compile_options(-O0)
endif()

if(${ENABLE_DEBUG_INFO})
    add_compile_options(-g)
    add_compile_options(-fstandalone-debug)
    add_compile_options(-fno-limit-debug-info)
    add_compile_options(-fno-discard-value-names)
else()
    add_compile_options(-g0)
endif()

include(libcpp64.cmake)
include(app.cmake)

if(${ENABLE_MEMORY_MAP})
    add_link_options("-Wl,-M")
endif()
