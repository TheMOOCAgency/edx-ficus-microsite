# -*- coding: utf-8 -*-

import os
import importlib

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

from django.core.management import execute_from_command_line
import django

from student.models import *

from xlsxwriter import *

from pprint import pformat

import json

import time

import sys

reload(sys)
sys.setdefaultencoding('utf8')

timestr = time.strftime("%Y_%m_%d")
timesfr = time.strftime("%d.%m.%Y")
timesfr = str(timesfr)


_title = [
    "email",
    "Nom",
    "prenom",
    "Pays",
    "Genre",
    "Année de naissance",
    #"Code Postal",
    #"Adresse",
    "LaPatisserie - MOOCPatisserieAFPA_S1",
    "LaPatisserie2 - MOOCPatisserieAFPA_S2",
    "MOOC_FLE_AFPA - FLE",
    "Mets et Vins - Saison 3",
    "Les101techniquesdebase - MOOCCUISINEAFPA",
    "Les101techniquesdebase - MOOCCUISINEAFPA_S2",
    "Les101techniquesdebase - MOOCCUISINEAFPA_S3",
    "Les101techniquesdebase - Replay 2019",
    #"Occitanie",
    "FLI",
    "Patisserie 2020",
    "Mets et vins 2020",
    "FLI 2020",
    "Cuisine 2020",
    "Mixite",
    "CPF",
    "Handicap",
    "TRE",
    "MATU",
    "MOOC Love Food"
]

_id = [
    "course-v1:afpa+LaPatisserie+MOOCPatisserieAFPA_S1",
    "course-v1:afpa+LaPatisserie2+MOOCPatisserieAFPA_S2",
    "course-v1:afpa+MOOC_FLE_AFPA+FLE",
    "course-v1:afpa+Metsetvins+MOOCmetsetvinsAFPA_S3",
    "course-v1:afpa+Les101techniquesdebase+MOOCCUISINEAFPA",
    "course-v1:afpa+Les101techniquesdebase+MOOCCUISINEAFPA_S2",
    "course-v1:afpa+Les101techniquesdebase+MOOCCUISINEAFPA_S3",
    "course-v1:afpa+Les101techniquesreplay+2019",
    #"course-v1:afpa+occitanie+2019_S1",
    "course-v1:afpa+MOOC_FLI+FLI_2019",
    "course-v1:afpa+La_Patisserie_replay_2020+2020",
    "course-v1:afpa+Mets_et_vins_replay_2020+2020",
    "course-v1:afpa+MOOC_FLI_replay_2020+2020",
    "course-v1:afpa+replay_2020+2020",
    "course-v1:afpa+mixite+mixite_2020",
    "course-v1:afpa+CPF+CPF_2020",
    "course-v1:afpa+inclusion_sociale+2020",
    "course-v1:afpa+TRE_2020+2020",
    "course-v1:afpa+MATU+2020",
    "course-v1:afpa+love_food+2020"
]

#PREPARE LE XLS

filename = '/edx/app/edxapp/edx-microsite/afpa/utils/xls/{}_export_enroll_afpa.xlsx'.format(timestr)
wb = Workbook(filename)
sheet = wb.add_worksheet('Enroll')
for i, header in enumerate(_title):
   sheet.write(0, i, header)

#BIG REQ SQL
query = 'SELECT a.id,a.username,a.first_name,a.last_name,a.email,b.name,b.custom_field,c.user_id,group_concat(c.course_id) AS course_id FROM auth_user a, auth_userprofile b, student_courseenrollment c WHERE a.id = c.user_id AND a.id = b.user_id AND c.course_id in ('

i=0
while i < len(_id) - 1:
   query = query + '"' + str(_id[i]) + '",'
   i = i + 1

query = query + '"' + str(_id[len(_id) - 1]) + '"'

query = query + ') GROUP BY a.id;'

#users = User.objects.raw('SELECT a.id,a.username,a.first_name,a.last_name,a.email,b.name,b.custom_field,c.user_id,group_concat(c.course_id) AS course_id FROM auth_user a, auth_userprofile b, student_courseenrollment c WHERE a.id = c.user_id AND a.id = b.user_id AND c.course_id in("course-v1:afpa+LaPatisserie+MOOCPatisserieAFPA_S1","course-v1:afpa+LaPatisserie2+MOOCPatisserieAFPA_S2","course-v1:afpa+Metsetvins+MOOCmetsetvinsAFPA_S3","course-v1:afpa+MOOC_FLE_AFPA+FLE","course-v1:afpa+Les101techniquesdebase+MOOCCUISINEAFPA","course-v1:afpa+Les101techniquesdebase+MOOCCUISINEAFPA_S2","course-v1:afpa+Les101techniquesdebase+MOOCCUISINEAFPA_S3","course-v1:afpa+occitanie+2019_S1","course-v1:afpa+MOOC_FLI+FLI_2019","course-v1:afpa+La_Patisserie_replay_2020+2020","course-v1:afpa+Mets_et_vins_replay_2020+2020","course-v1:afpa+MOOC_FLI_replay_2020+2020","course-v1:afpa+replay_2020+2020") GROUP BY a.id;')

users = User.objects.raw(query)

i = 1
for user in users:

    _email = user.email
    try:
        _custom = json.loads(user.custom_field)
    except:
        _custom = {}

    if _custom.get('last_name') is not None:
        _last_name = _custom.get('last_name')
    else:
        _last_name = user.last_name
    if _custom.get('first_name') is not None:
        _first_name = _custom.get('first_name')
    else:
        _first_name = user.first_name

    values = [
        _last_name,
        _first_name,
        _custom.get('country'),
        _custom.get('gender'),
        _custom.get('year_of_birth')
        #_custom.get('cp')
        #_custom.get('mailing_adress')
    ]

    courses = user.course_id


    # ecriture colonne de chaques lignes
    sheet.write(i, 0, _email)
    j = 1
    #values from custom form
    for val in values:
        if val:
            sheet.write(i, j, str(val))
        else:
            sheet.write(i, j, 'n/a')
        j = j + 1
    #is enroll
    q = {}
    course_id = user.course_id.split(',')
    for n in _id:
        for c in course_id:
            if str(n) == str(c):
                q[n] = True



    for n in _id:
        try:
            q[n]
            sheet.write(i, j, 'oui')
        except:
            sheet.write(i, j, 'non')
        j = j + 1
    i = i + 1


wb.close()

# envoyer un mail test
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
html = u"<html><head></head><body><p>Bonjour,<br/><br/>Voici la liste des inscrits Afpa.<br/><br/>Bonne reception<br>The MOOC Agency<br></p></body></html>"
part2 = MIMEText(html, 'html')
TO_EMAILS = ['sysadmin@themoocagency.com','loic.tournedouet@gmail.com']
#TO_EMAILS = ['yoann.mroz@themoocagency.com']
for i in range(len(TO_EMAILS)):
   fromaddr = "no-reply@themoocagency.com"
   toaddr = str(TO_EMAILS[i])
   msg = MIMEMultipart()
   msg['From'] = fromaddr
   msg['To'] = toaddr
   msg['Subject'] = "Inscriptions MOOC AFPA"
   attachment = open(filename, "rb")
   part = MIMEBase('application', 'octet-stream')
   part.set_payload((attachment).read())
   encoders.encode_base64(part)
   part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(filename))
   msg.attach(part)
   server = smtplib.SMTP('mail3.themoocagency.com', 25)
   server.starttls()
   server.login('contact', 'waSwv6Eqer89')
   msg.attach(part2)
   text = msg.as_string()
   server.sendmail(fromaddr, toaddr, text)
   server.quit()
   print 'mail send to '+str(TO_EMAILS[i])
os.remove(filename)
