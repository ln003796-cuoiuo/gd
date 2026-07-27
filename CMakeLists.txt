cmake_minimum_required(VERSION 3.21)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Имя проекта (должно быть уникальным, без точек и пробелов)
project(gd_ai_bot)

# Эта магическая команда автоматически предоставляется GitHub Actions!
# Она читает mod.json и собирает мод.
add_geode_mod(${PROJECT_NAME}
    SOURCES
        src/main.cpp
)

# Подключаем библиотеку для работы с сетью (нужна для связи с Python)
if(WIN32)
    target_link_libraries(${PROJECT_NAME} PRIVATE ws2_32)
    target_compile_definitions(${PROJECT_NAME} PRIVATE _WIN32_WINNT=0x0601)
endif()