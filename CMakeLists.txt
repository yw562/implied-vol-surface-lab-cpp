cmake_minimum_required(VERSION 3.12)
project(implied_vol_surface_lab_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(iv_lab
    src/main.cpp
)

target_include_directories(iv_lab PRIVATE include)
target_compile_options(iv_lab PRIVATE -O2 -Wall -Wextra -Wpedantic)
