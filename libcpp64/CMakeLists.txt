cmake_minimum_required(VERSION 3.18)

project(libcpp64 LANGUAGES CXX)

include_directories(./include)

set(INCLUDES
    ./include/memory
    ./include/array
    ./include/algorithm
    ./include/sys
    ./include/libcpp64/system.h
    ./include/libcpp64/auxiliary.h
    ./include/libcpp64/audio.h
    ./include/libcpp64/video.h
    ./include/libcpp64/keyboard.h
)

set(SOURCES
    ${INCLUDES}
    src/system.cpp
    src/auxiliary.cpp
    src/audio.cpp
    src/video.cpp
    src/keyboard.cpp
)

add_library(libcpp64 STATIC ${SOURCES})
