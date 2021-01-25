# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
import importlib
import time
import logging
from unidecode import unidecode
from xlwt import *

from io import BytesIO

import csv
from csv import reader

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

log = logging.getLogger()

from pprint import pformat

org = 'bnpp-netexplo'
path_to_utils = '/edx/app/edxapp/edx-microsite/{}/utils/backup/'.format(org)

file_journeys = path_to_utils + 'journeys.csv'
file_expeditions = path_to_utils + 'expeditions.csv'
file_report = path_to_utils + 'rapport_ancienne_aca.csv'
file_report_v2 = path_to_utils + 'rapport_ancienne_aca_v2.csv'

journeys_match_list = {
    "Big Data":"Big Data",
    "Blockchain":"Blockchain",
    "Chatbot":"Chatbot",
    "Collaborateurs Connectés":"Collaborateurs co",
    "Compétences connectées":"Compétences co",
    "Consommateurs Connectés":"Consommateurs co",
    "Consumer to consumer":"C to C",
    "Crowdfunding":"Crowdfunding",
    "Digital in store":"Digital in Store",
    "e-Santé":"eSanté",
    "Economie Participative":"Eco participative",
    "Ewellness":"Ewellness",
    "Handicap":"Handicap",
    "Information 2.0":"Information 2 0",
    "Innovation frugale":"Inno frugale",
    "Internet Mobile":"Internet Mobile",
    "Makers":"Makers",
    "Médias Sociaux":"Médias sociaux",
    "Nouvelles Interfaces":"Nlles Interfaces",
    "Objets Connectés":"Objets connectés",
    "Robotique & IA":"Robotique & IA",
    "Savoirs Connectés":"Savoirs co",
    "Sécurité":"Sécurité",
    "Smartcities":"Smart Cities"
}

expeditions_match_list = {
    "Manager":"Manager",
    "Marketing":"Responsable marketing",
    "Opérateur":"Opérateur de production",
    "RH":"Responsable RH",
    "SI":"Chef de projet SI",
    "Vendeur":"Conseiller de clientèle"
}

users = {}

file = open(file_journeys, "rb")
old_users_journey_list = csv.DictReader(file, delimiter=';')
for old_user in old_users_journey_list:
    journey_list_str =''
    for journey_match in journeys_match_list:
        if old_user[journey_match]:
            if journey_list_str != '':
                journey_list_str += ','
            journey_list_str += journeys_match_list[journey_match]
    if journey_list_str != '':
        users[old_user['email']] = {}
        users[old_user['email']]['journeys'] = journey_list_str
file.close()

file = open(file_expeditions, "rb")
old_users_expeditions_list = csv.DictReader(file, delimiter=';')
for old_user in old_users_expeditions_list:
    expeditions_list_str =''
    for expeditions_match in expeditions_match_list:
        if expeditions_match in old_user:
            if expeditions_list_str != '':
                expeditions_list_str += ','
            expeditions_list_str += expeditions_match_list[expeditions_match]
    if expeditions_list_str != '':
        if not old_user['email'] in users:
            users[old_user['email']] = {}
        users[old_user['email']]['expeditions'] = expeditions_list_str
file.close()

users_new_version_list = []
with open(file_report, 'r') as read_obj:
    csv_reader = reader(read_obj, delimiter=';')
    header = next(csv_reader)

file = open(file_report, "rb")
old_users_report_v1 = csv.DictReader(file, delimiter=';')
log.info(users.keys())
for old_user in old_users_report_v1:
    if old_user['email'] in users.keys():
        user_dict = users[old_user['email']]
        if 'journeys' in user_dict:
            log.info(old_user['email'])
            log.info(user_dict['journeys'])
            old_user['journey'] = user_dict['journeys']
        if 'expeditions' in users:
            log.info(old_user['email'])
            log.info(user_dict['expeditions'])
            old_user['expedition'] = user_dict['expeditions']
    row = []
    for key in header:
        row.append(old_user[key])
    users_new_version_list.append(row)
file.close()

with open(file_report_v2, mode='wb') as outfile:
    writer = csv.writer(outfile, delimiter=';')
    writer.writerow(header)
    for row in users_new_version_list:
        writer.writerow(row)