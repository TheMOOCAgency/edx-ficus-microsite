# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
import importlib
import time
from xlwt import *
from datetime import datetime
import json


from io import BytesIO

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()


from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.course_groups.cohorts import get_cohort
from opaque_keys.edx.keys import CourseKey

from student.models import *

from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from lms.djangoapps.grades.context import grading_context_for_course, grading_context
from courseware.courses import get_course_by_id
from courseware.courses import get_course
from tma_apps.models import TmaCourseEnrollment


import logging
log= logging.getLogger()

# RETRIEVE ARGUMENTS
TO_EMAILS = sys.argv[1].split(';')
course_id = ""
try:
    course_id = sys.argv[2]
except:
    pass

# SET MAIN VARIABLES
org = course_id.split(":")[1].split("+")[0]
register_form = configuration_helpers.get_value_for_org(org, 'FORM_EXTRA')

# Get headers
HEADERS_GLOBAL = []
HEADERS_USER = ["email", "Prénom", "Nom", "Temps passé (min)", "saisie_1", "saisie_2", "saisie_3", "saisie_4", "saisie_5_1", "saisie_5_2", "saisie_5_3", "saisie_theme"] 

# Course info from argument
course_key = CourseKey.from_string(course_id)
course = get_course_by_id(course_key) 

HEADERS_GLOBAL.append(course.display_name_with_default)

# Get course enrollments for each course
enrollments = CourseEnrollment.objects.filter(course_id=course_key)

ROWS = []
users_rows = []
for i in range(len(enrollments)):
    user = enrollments[i].user
    log.info(user)
    tma_enrollment,is_exist=TmaCourseEnrollment.objects.get_or_create(course_enrollment_edx=enrollments[i])


    # Dev Cyril Start
    # Hide when user is testuser 
    if user.email.find("@weuplearning") != -1 or user.email.find("@themoocagency") != -1 or user.email.find("@yopmail") != -1:
        continue

    # ONLY SAVE IF USER IS NEW (J-30) 
    string_data = str(enrollments[i])
    date_registration = datetime.strptime(string_data.split(' ')[3].replace('(',''), '%Y-%m-%d')

    today =  datetime.now()

    test_substract = (today - date_registration).days
    if test_substract > 31 :
        log.info(test_substract)
        continue
    # Dev Cyril End


    # USER INFO
    user_profile = {}
    email = user.email
    custom_field = {}
    try:
        custom_field = json.loads(UserProfile.objects.get(user=user).custom_field)
    except:
        pass

    log.info('custom_field')
    log.info(custom_field)

    if user.first_name:
        first_name = user.first_name
    elif custom_field :
        first_name = custom_field.get('first_name', 'n/a')
    else:
        first_name = "n/a"

    if user.last_name:
        last_name = user.last_name
    elif custom_field :
        last_name = custom_field.get('last_name', 'n/a')
    else:
        last_name = "n/a"

    
    # Time tracking
    try:
        seconds = tma_enrollment.global_time_tracking
        minute = seconds // 60
        time_tracking = int(minute)
    except:
        time_tracking = int(0)


    if custom_field :
        data1_SC = custom_field.get('data1_SC', 'n/a')
    else:
        data1_SC = "n/a"


    if custom_field :
        saisie_1 = custom_field.get('saisie_1', 'n/a')
    else:
        saisie_1 = "n/a"

    if custom_field :
        saisie_2 = custom_field.get('saisie_2', 'n/a')
    else:
        saisie_2 = "n/a"

    if custom_field :
        saisie_3 = custom_field.get('saisie_3', 'n/a')
    else:
        saisie_3 = "n/a"

    if custom_field :
        saisie_4 = custom_field.get('saisie_4', 'n/a')
    else:
        saisie_4 = "n/a"

    if custom_field :
        saisie_5_1 = custom_field.get('saisie_5_1', 'n/a')
    else:
        saisie_5_1 = "n/a"

    if custom_field :
        saisie_5_2 = custom_field.get('saisie_5_2', 'n/a')
    else:
        saisie_5_2 = "n/a"

    if custom_field :
        saisie_5_3 = custom_field.get('saisie_5_3', 'n/a')
    else:
        saisie_5_3 = "n/a"

    if custom_field :
        saisie_theme = custom_field.get('saisie_theme', 'n/a')
    else:
        saisie_theme = "n/a"

    user_row = [email, first_name, last_name, time_tracking, saisie_1, saisie_2, saisie_3, saisie_4, saisie_5_1, saisie_5_2, saisie_5_3, saisie_theme]

    ROWS.append(user_row)

# WRITE FILE
# Prepare workbook
wb = Workbook(encoding='utf-8')
filename = '/home/edxtma/csv/formation-data_{}_{}.xls'.format(course_id.encode('ascii', errors='xmlcharrefreplace'), time.strftime("%d.%m.%Y"))
sheet = wb.add_sheet('Rapport')
style_title = easyxf('font: bold 1')
sheet.write(0, 0, HEADERS_GLOBAL[0], style_title)

for i, header in enumerate(HEADERS_USER):
   sheet.write(1, i, header, style_title)

j = 1
for row in ROWS:
    j = j + 1
    for i, value in enumerate(row):
       sheet.write(j, i, value)

# SEND MAILS
output = BytesIO()
wb.save(output)
_files_values = output.getvalue()

course_names_html = "<li>"+ course.display_name_with_default.encode('ascii', errors='xmlcharrefreplace')+"</li>"

html = "<html><head></head><body><p>Bonjour,<br/><br/>Vous trouverez en PJ le rapport de donn&eacute;es des MOOCs : "+ course_names_html +" pour la période des 30 derniers jours uniquement.<br/><br/>Bonne r&eacute;ception<br>L'&eacute;quipe NETEXPLO<br></p></body></html>"

part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

for i in range(len(TO_EMAILS)):
   fromaddr = "ne-pas-repondre@themoocagency.com"
   toaddr = str(TO_EMAILS[i])
   msg = MIMEMultipart()
   msg['From'] = fromaddr
   msg['To'] = toaddr
   msg['Subject'] = "NETEXPLO - " + course.display_name_with_default.encode('ascii', errors='xmlcharrefreplace') + ' - last 30 days - ' + time.strftime("%d.%m.%Y")
   attachment = _files_values
   part = MIMEBase('application', 'octet-stream')
   part.set_payload(attachment)
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
   print('Email sent to '+str(TO_EMAILS[i]))


# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/faciliter-transformation/utils/script_new_users_faciliter.py "tom.douce@weuplearning.com;eruch-ext@netexplo.org;clescop-ext@netexplo.org;melanie.zunino@weuplearning.com" "course-v1:faciliter-transformation+FR+2020"

# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/faciliter-transformation/utils/script_new_users_faciliter.py "tom.douce@weuplearning.com;eruch-ext@netexplo.org;clescop-ext@netexplo.org;melanie.zunino@weuplearning.com" "course-v1:faciliter-transformation+EN+2021"


# PPROD1 TEST
# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/faciliter-transformation/utils/script_new_users_faciliter.py "cyril.adolf@weuplearning.com" "course-v1:faciliter-transformation+01+01"

# Test Prod
# sudo -H -u edxapp /edx/bin/python.edxapp /edx/app/edxapp/edx-microsite/faciliter-transformation/utils/script_new_users_faciliter.py "cyril.adolf@weuplearning.com" "course-v1:faciliter-transformation+EN+2021"
