cmake_minimum_required(VERSION 3.21)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Имя проекта (должно быть уникальным, без пробелов)
project(gd_ai_bot VERSION 1.0.0)

# Находим Geode SDK (GitHub Action предоставляет его автоматически)
find_package(GeodeSDK REQUIRED)

# Объявляем мод и указываем исходные файлы
add_geode_mod(${PROJECT_NAME}
    SOURCES
        src/main.cpp
)

# Подключаем библиотеку для работы с сетью (нужна для связи с Python)
if(WIN32)
    target_link_libraries(${PROJECT_NAME} PRIVATE ws2_32)
    target_compile_definitions(${PROJECT_NAME} PRIVATE _WIN32_WINNT=0x0601)
endif()