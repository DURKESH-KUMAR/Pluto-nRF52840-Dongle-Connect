# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file LICENSE.rst or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION ${CMAKE_VERSION}) # this file comes with cmake

# If CMAKE_DISABLE_SOURCE_CHANGES is set to true and the source directory is an
# existing directory in our source tree, calling file(MAKE_DIRECTORY) on it
# would cause a fatal error, even though it would be a no-op.
if(NOT EXISTS "C:/Users/Public/Documents/Pluto_Calibration")
  file(MAKE_DIRECTORY "C:/Users/Public/Documents/Pluto_Calibration")
endif()
file(MAKE_DIRECTORY
  "C:/Users/Public/Documents/Pluto_Calibration/build/Pluto_Calibration"
  "C:/Users/Public/Documents/Pluto_Calibration/build/_sysbuild/sysbuild/images/Pluto_Calibration-prefix"
  "C:/Users/Public/Documents/Pluto_Calibration/build/_sysbuild/sysbuild/images/Pluto_Calibration-prefix/tmp"
  "C:/Users/Public/Documents/Pluto_Calibration/build/_sysbuild/sysbuild/images/Pluto_Calibration-prefix/src/Pluto_Calibration-stamp"
  "C:/Users/Public/Documents/Pluto_Calibration/build/_sysbuild/sysbuild/images/Pluto_Calibration-prefix/src"
  "C:/Users/Public/Documents/Pluto_Calibration/build/_sysbuild/sysbuild/images/Pluto_Calibration-prefix/src/Pluto_Calibration-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "C:/Users/Public/Documents/Pluto_Calibration/build/_sysbuild/sysbuild/images/Pluto_Calibration-prefix/src/Pluto_Calibration-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "C:/Users/Public/Documents/Pluto_Calibration/build/_sysbuild/sysbuild/images/Pluto_Calibration-prefix/src/Pluto_Calibration-stamp${cfgdir}") # cfgdir has leading slash
endif()
