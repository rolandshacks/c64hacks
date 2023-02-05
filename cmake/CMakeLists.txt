#
# Main build file
#

cmake_minimum_required(VERSION 3.18)
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR 6510)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
project(cppdemo LANGUAGES CXX ASM)
include(project.cmake)
set_target_properties(${CMAKE_PROJECT_NAME} PROPERTIES SUFFIX ".prg")
