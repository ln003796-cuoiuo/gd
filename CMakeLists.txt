cmake_minimum_required(VERSION 3.21)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Имя проекта
project(gd_ai_bot)

# Явно указываем путь к Geode SDK, который скачал GitHub Action
list(APPEND CMAKE_MODULE_PATH "$ENV{GEODE_SDK}/cmake")
include(GeodeSDK)

# Объявляем мод
add_geode_mod(${PROJECT_NAME}
    SOURCES
        src/main.cpp
)

# Подключаем библиотеку для работы с сетью
if(WIN32)
    target_link_libraries(${PROJECT_NAME} PRIVATE ws2_32)
    target_compile_definitions(${PROJECT_NAME} PRIVATE _WIN32_WINNT=0x0601)
endif()