#!/usr/bin/env python

import os
import sys
import json

import logging
log = logging.getLogger()

# check the input json name
with open("/edx/var/edxapp/secret/microsite/psa-netexplo/grades.json", 'r') as f:
    crude_data = json.load(f)

# try to print out the object to know about our object
# print('print =========>  crude_data[0]["userData"][0]["grades"]["global"] to check the path')
# print(crude_data[0]["userData"][0]["grades"]["global"])

histograms_data = []
for course in crude_data:
    data = [
        {"value": 0, "score": '0-5', "users_percent": 0 },
        {"value": 5, "score": '5-10', "users_percent": 0 },
        {"value": 10, "score": '10-15', "users_percent": 0 },
        {"value": 15, "score": '15-20', "users_percent": 0 },
        {"value": 20, "score": '20-25', "users_percent": 0 },
        {"value": 25, "score": '25-30', "users_percent": 0 },
        {"value": 30, "score": '30-35', "users_percent": 0 },
        {"value": 35, "score": '35-40', "users_percent": 0 },
        {"value": 40, "score": '40-45', "users_percent": 0 },
        {"value": 45, "score": '45-50', "users_percent": 0 },
        {"value": 50, "score": '50-55', "users_percent": 0 },
        {"value": 55, "score": '55-60', "users_percent": 0 },
        {"value": 60, "score": '60-65', "users_percent": 0 },
        {"value": 65, "score": '65-70', "users_percent": 0 },
        {"value": 70, "score": '70-75', "users_percent": 0 },
        {"value": 75, "score": '75-80', "users_percent": 0 },
        {"value": 80, "score": '80-85', "users_percent": 0 },
        {"value": 85, "score": '85-90', "users_percent": 0 },
        {"value": 90, "score": '90-95', "users_percent": 0 },
        {"value": 95, "score": '95-100', "users_percent": 0 }
    ]
    total = 0

    for user in course["userData"]:
        if user["fields"]["has_finished"] :
            total += 1
            if user["grades"]["global"] <= 0.05:
                data[0]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.10:
                data[1]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.15:
                data[2]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.20:
                data[3]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.25:
                data[4]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.30:
                data[5]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.35:
                data[6]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.40:
                data[7]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.45:
                data[8]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.50:
                data[9]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.55:
                data[10]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.60:
                data[11]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.65:
                data[12]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.70:
                data[13]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.75:
                data[14]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.80:
                data[15]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.85:
                data[16]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.90:
                data[17]["users_percent"] += 1
            elif user["grades"]["global"] <= 0.95:
                data[18]["users_percent"] += 1
            elif user["grades"]["global"] <= 1:
                data[19]["users_percent"] += 1

    if total != 0:
        print(total)
        for obj in data:
            obj["users_percent"] = round(obj["users_percent"]*100/total, 4)

    histograms_data.append(data)

#rename output json
with open('/edx/var/edxapp/secret/microsite/psa-netexplo/histogram_data.json', 'w') as outfile:
    json.dump(histograms_data, outfile)

# 1. check input file name
# 2. check output file name
# 3. run the code line below on the right server: 
# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/psa-netexplo/utils/psa-histogram-script.py