# Copyright 2021 awilliam
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

"""
Iterates through all files in sourceData/hourlies/ folder for all years, one station
at a time, and compile dataframe of max temp, max wind speed, min RH, max FFMC, and
max FWI observed each day. Also records the hour of the day (on 24H clock) when each
daily high or low was observed. Writes the resulting dataframe to a CSV file.
"""
