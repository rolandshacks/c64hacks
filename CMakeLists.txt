cmake_minimum_required(VERSION 3.18)

set(CMAKE_CXX_STANDARD 20)
set(ENABLE_LLVM_MOS ON)
set(ENABLE_MEMORY_MAP OFF)
set(ENABLE_DEBUG_INFO OFF)
set(ENABLE_OPTIMIZATION ON)

if(${ENABLE_LLVM_MOS})
    set(LLVM_MOS_PLATFORM               c64)
    set(CMAKE_SYSTEM_NAME               Generic)
    set(CMAKE_SYSTEM_PROCESSOR          6510)
    set(CMAKE_TRY_COMPILE_TARGET_TYPE   STATIC_LIBRARY)
endif(${ENABLE_LLVM_MOS})

project(cppdemo LANGUAGES CXX ASM)

include_directories(./libcpp64/include)

if(${ENABLE_OPTIMIZATION})
    add_compile_options(-O3)
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

add_subdirectory(libcpp64)

set(LINKER_SCRIPT ${CMAKE_SOURCE_DIR}/linker.ld)

#add_compile_options(-save-temps)

add_link_options(-T${LINKER_SCRIPT})

if(${ENABLE_MEMORY_MAP})
    add_link_options("-Wl,-M")
endif()

set(SOURCES
    resources/music.cpp
    resources/sprites.cpp
    src/asm_main.s
    src/main.cpp
)

set_property(SOURCE src/asm_main.s APPEND PROPERTY COMPILE_OPTIONS "-x" "assembler-with-cpp")

add_executable(${CMAKE_PROJECT_NAME} ${SOURCES})
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE libcpp64)

if(${ENABLE_LLVM_MOS})
    set_target_properties(${CMAKE_PROJECT_NAME} PROPERTIES SUFFIX ".prg")
else()
    set_target_properties(${CMAKE_PROJECT_NAME} PROPERTIES SUFFIX ".exe")
endif()

set_target_properties(${CMAKE_PROJECT_NAME} PROPERTIES LINK_DEPENDS ${LINKER_SCRIPT})
