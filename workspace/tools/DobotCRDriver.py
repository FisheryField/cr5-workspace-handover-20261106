# -*- coding: UTF-8 -*-
# Copyright 2015-2025 - RoboDK Inc. - https://robodk.com/
#
# This file loads the compiled version of the RoboDK driver for:
#   DobotCRDriver robot controllers
#
# More information about RoboDK Drivers is available here:
#     https://robodk.com/doc/en/Robot-Drivers.html
# ----------------------------------------------------

import sys
import os

# Detect Python version and driver
print("Using Python version: " + str(sys.version_info))
path_file = os.path.dirname(__file__).replace(os.sep, "/")
print("RoboDK Driver: " + path_file)

# Check if the driver is compatible with the Python version
version_str = str(sys.version_info[0]) + str(sys.version_info[1])
path_library = path_file + '/v' + version_str
if not os.path.isdir(path_library):
    msg = "Invalid Python version or driver not found. Make sure you are using a supported Python version: " + path_library
    msg += "\nSelect Tools-Options-Python and select a supported Python version"
    print(msg)
    raise Exception(msg)

# Load the driver
exec("from v" + version_str + ".DobotCRDriver import *")


if __name__== "__main__":
    exec("from v" + version_str + ".DobotCRDriver import RunMain")
    RunMain()

