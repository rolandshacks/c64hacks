#
# Application build file
#

set(APP_NAME ${CMAKE_PROJECT_NAME})
set(APP_DIR ..)
set(APP_SRCDIR ${APP_DIR}/src)
set(APP_RESDIR ${APP_DIR}/resources)

include_directories(./libcpp64/include)

set(APP_SOURCES_ASM
    ${APP_SRCDIR}/asm_main.s
)

set(APP_SOURCES
    ${APP_RESDIR}/music.cpp
    ${APP_RESDIR}/sprites.cpp
    ${APP_SRCDIR}/main.cpp
)

set_property(SOURCE ${APP_SOURCES_ASM} APPEND PROPERTY COMPILE_OPTIONS "-x" "assembler-with-cpp")

add_executable(${APP_NAME} ${APP_SOURCES} ${APP_SOURCES_ASM})
target_link_libraries(${APP_NAME} PRIVATE libcpp64)

if(${ENABLE_LLVM_MOS})
    set_target_properties(${APP_NAME} PROPERTIES SUFFIX ".prg")
else()
    set_target_properties(${APP_NAME} PROPERTIES SUFFIX ".exe")
endif()
