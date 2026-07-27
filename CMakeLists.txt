cmake_minimum_required(VERSION 3.21)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

project(gd-ai-bot VERSION 1.0.0)

# Проверяем наличие Geode SDK (GitHub Actions предоставляет его автоматически)
if(NOT DEFINED ENV{GEODE_SDK})
    message(FATAL_ERROR "Unable to find Geode SDK! Please define GEODE_SDK environment variable")
endif()

# Добавляем пути к Geode SDK
list(APPEND CMAKE_MODULE_PATH "$ENV{GEODE_SDK}/cmake")
include(GeodeSDK)

# Объявляем мод и его исходные файлы
add_geode_mod(${PROJECT_NAME}
    SOURCES
        src/main.cpp
)

# Подключаем библиотеку для сокетов (нужна для связи с Python)
if(WIN32)
    target_link_libraries(${PROJECT_NAME} PRIVATE ws2_32)
    target_compile_definitions(${PROJECT_NAME} PRIVATE _WIN32_WINNT=0x0601)
endif()