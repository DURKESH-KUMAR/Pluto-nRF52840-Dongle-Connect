# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file LICENSE.rst or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION ${CMAKE_VERSION}) # this file comes with cmake

# If CMAKE_DISABLE_SOURCE_CHANGES is set to true and the source directory is an
# existing directory in our source tree, calling file(MAKE_DIRECTORY) on it
# would cause a fatal error, even though it would be a no-op.
if(NOT EXISTS "C:/Users/Public/Documents/Pluto-nRF52840-Dongle-Connect")
  file(MAKE_DIRECTORY "C:/Users/Public/Documents/Pluto-nRF52840-Dongle-Connect")
endif()
file(MAKE_DIRECTORY
  "C:/Users/Public/Documents/Pluto-nRF52840-Dongle-Connect/build/Pluto-nRF52840-Dongle-Connect"
  "C:/Users/Public/Documents/Pluto-nRF52840-Dongle-Connect/build/_sysbuild/sysbuild/images/Pluto-nRF52840-Dongle-Connect-prefix"
  "C:/Users/Public/Documents/Pluto-nRF52840-Dongle-Connect/build/_sysbuild/sysbuild/images/Pluto-nRF52840-Dongle-Connect-prefix/tmp"
  "C:/Users/Public/Documents/Pluto-nRF52840-Dongle-Connect/build/_sysbuild/sysbuild/images/Pluto-nRF52840-Dongle-Connect-prefix/src/Pluto-nRF52840-Dongle-Connect-stamp"
  "C:/Users/Public/Documents/Pluto-nRF52840-Dongle-Connect/build/_sysbuild/sysbuild/images/Pluto-nRF52840-Dongle-Connect-prefix/src"
  "C:/Users/Public/Documents/Pluto-nRF52840-Dongle-Connect/build/_sysbuild/sysbuild/images/Pluto-nRF52840-Dongle-Connect-prefix/src/Pluto-nRF52840-Dongle-Connect-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "C:/Users/Public/Documents/Pluto-nRF52840-Dongle-Connect/build/_sysbuild/sysbuild/images/Pluto-nRF52840-Dongle-Connect-prefix/src/Pluto-nRF52840-Dongle-Connect-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "C:/Users/Public/Documents/Pluto-nRF52840-Dongle-Connect/build/_sysbuild/sysbuild/images/Pluto-nRF52840-Dongle-Connect-prefix/src/Pluto-nRF52840-Dongle-Connect-stamp${cfgdir}") # cfgdir has leading slash
endif()
