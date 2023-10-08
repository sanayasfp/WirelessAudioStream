# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "C:/Users/PRESSO_William/esp/esp-idf/components/bootloader/subproject"
  "E:/GitHub/Wearer/wearable-hardware/firmware/Pod/hello_world/build/bootloader"
  "E:/GitHub/Wearer/wearable-hardware/firmware/Pod/hello_world/build/bootloader-prefix"
  "E:/GitHub/Wearer/wearable-hardware/firmware/Pod/hello_world/build/bootloader-prefix/tmp"
  "E:/GitHub/Wearer/wearable-hardware/firmware/Pod/hello_world/build/bootloader-prefix/src/bootloader-stamp"
  "E:/GitHub/Wearer/wearable-hardware/firmware/Pod/hello_world/build/bootloader-prefix/src"
  "E:/GitHub/Wearer/wearable-hardware/firmware/Pod/hello_world/build/bootloader-prefix/src/bootloader-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "E:/GitHub/Wearer/wearable-hardware/firmware/Pod/hello_world/build/bootloader-prefix/src/bootloader-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "E:/GitHub/Wearer/wearable-hardware/firmware/Pod/hello_world/build/bootloader-prefix/src/bootloader-stamp${cfgdir}") # cfgdir has leading slash
endif()
