# CMakeLists for PoMiDAQ Python module

list(APPEND CMAKE_MODULE_PATH "/home/agroo/src/pomidaq/contrib/cmake/")
list(APPEND CMAKE_MODULE_PATH "/home/agroo/anaconda3/envs/miniscope")
list(APPEND CMAKE_PREFIX_PATH "/home/agroo/anaconda3/envs/miniscope/lib/python3.12/site-packages/")


find_package(pybind11 REQUIRED)
find_package(NumPy REQUIRED)

pybind11_add_module(pyminiscope
    pyminiscope.cpp
    cvmatndsliceconvert.h
    cvmatndsliceconvert.cpp
    qstringtopy.h
)

target_link_libraries(pyminiscope PRIVATE
    miniscope
)
set_target_properties(pyminiscope PROPERTIES OUTPUT_NAME miniscope)

install(TARGETS pyminiscope
    LIBRARY DESTINATION "lib/python${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}/dist-packages/"
)

include_directories(SYSTEM
    ${NUMPY_INCLUDE_DIRS}
)
include_directories(
    ../libminiscope/
)
