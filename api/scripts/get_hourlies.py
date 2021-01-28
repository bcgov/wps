"""
For diurnal curve experimentation sprint -
send POST request to BC fire Weather Phase 1 website
to retrieve hourly weather data (in CSV format) for all 277 weather stations,
1 station at a time, 1 year at a time, for April 1 - September 30 for
years 2011 - 2020.
"""
import requests
import re
import time
import os
from requests_ntlm import HttpNtlmAuth

codes = [322, 838, 209, 317, 213, 977, 1275, 331, 302, 111, 167, 503, 221, 149, 37, 390, 175, 432, 228, 267, 868, 1040, 262, 148, 866, 1108, 113, 193, 56, 445, 283, 865, 181, 253, 554, 793, 199, 59, 429, 1283, 791, 189, 832, 239, 232, 556, 433, 426, 352, 292, 1203, 108, 251, 421, 905, 385, 243, 170, 391, 438, 412, 425, 383, 298, 440, 1029, 418, 1144, 1377, 599, 146, 1375, 306, 182, 222, 227, 291, 401, 886, 379, 919, 270, 124, 392, 161, 321, 1332, 309, 904, 67, 250, 118, 187, 201, 654, 1349, 93, 230, 162, 343, 132, 876, 145, 112, 190, 419, 444, 388, 428, 106, 1348, 166, 225, 1075, 1323, 307, 140, 171, 255, 280, 1330, 218, 163, 1350,
         362, 101, 1276, 155, 141, 367, 263, 1082, 195, 180, 334, 192, 311, 153, 236, 1083, 19, 294, 934, 226, 165, 1176, 131, 151, 179, 316, 407, 1251, 427, 211, 789, 119, 216, 393, 172, 437, 173, 159, 396, 1270, 1045, 121, 411, 183, 326, 178, 301, 402, 328, 1248, 938, 129, 212, 1387, 380, 1218, 264, 1093, 138, 363, 210, 394, 1092, 105, 788, 346, 45, 1345, 82, 1165, 344, 555, 882, 117, 152, 120, 1024, 406, 404, 305, 1055, 1359, 374, 11, 156, 144, 208, 206, 110, 279, 234, 126, 75, 417, 387, 995, 1378, 1362, 956, 1002, 1056, 1066, 945, 944, 1025, 361, 127, 286, 72, 169, 431, 200, 1268, 430, 158, 447, 266, 1277, 366, 790, 244, 154, 136, 21, 235]

url = 'https://bcfireweatherp1.nrs.gov.bc.ca/Scripts/Public/Common/Results_Report.asp'

headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

for code in codes:
    for year in range(2011, 2021):
        data = {
            'End_Date': str(year)+'093024',
            'Start_Date': str(year)+'040100',
            'Format': 'CSV',
            'rdoReport': 'OSBH',
            'cboFilters': '0',
            'Station_Code': code
        }

        password = 'password'
        user = 'username'
        auth = HttpNtlmAuth('idir\\'+user, password)
        response = requests.post(url, headers=headers, data=data, auth=auth)
        csv_path = re.search(r"fire_weather\/csv\/.+\.csv", response.text)
        if csv_path is not None:
            print(response.status_code, csv_path.group(0))
            r = requests.get('https://bcfireweatherp1.nrs.gov.bc.ca/'+csv_path.group(0), auth=auth)
            try:
                os.stat(os.path.join('/Users/awilliam/Desktop/wps/api/sourceData/hourlies/', str(year)))
            except:
                os.mkdir(os.path.join('/Users/awilliam/Desktop/wps/api/sourceData/hourlies/', str(year)))
            filename = os.path.join('/Users/awilliam/Desktop/wps/api/sourceData/hourlies/', str(year),
                                    csv_path.group(0)[-24:])
            with open(filename, 'wb') as f:
                f.write(r.content)
                f.close()
                print('Wrote to', filename)
            time.sleep(1)
        else:
            print('Skipping station', code, 'for', year)
