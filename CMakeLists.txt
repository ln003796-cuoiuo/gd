cmake_minimum_required(VERSION 3.21)
project(gd-ai-bot VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(${PROJECT_NAME} SHARED
    src/main.cpp
)

if(NOT DEFINED ENV{GEODE_SDK})
    message(FATAL_ERROR "Unable to find Geode SDK! Please define GEODE_SDK environment variable.")
endif()

include($ENV{GEODE_SDK}/cmake/GeodeSDK.cmake)
setup_geode_mod(${PROJECT_NAME})

target_link_libraries(${PROJECT_NAME}
    ws2_32
)

if(WIN32)
    target_compile_definitions(${PROJECT_NAME} PRIVATE _WIN32_WINNT=0x0601)
endif()