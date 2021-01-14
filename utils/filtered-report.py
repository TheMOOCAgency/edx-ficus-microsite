# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf8')

#IMPORT FOR SCRIPT TO
##RUN
##WRITE EXCEL FILE
##SEND EMAIL
import os
import importlib
import csv
import time
import os
from xlwt import *
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
#IMPORT TO
##RUN OUTSITE EDX
from django.core.management import execute_from_command_line
import django
##USE EDX FUNCTIONS
from opaque_keys.edx.keys import CourseKey
from courseware.access import has_access
from lms.djangoapps.ccx.utils import prep_course_for_grading
from lms.djangoapps.courseware import courses
from lms.djangoapps.grades.api.serializers import GradingPolicySerializer
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from student.roles import CourseStaffRole
from student.models import *
from courseware.courses import get_course_by_id
from courseware.courses import get_course
from tma_ensure_form.models import ensure_form_models
from datetime import datetime, timedelta
import pytz
import logging
log = logging.getLogger()

from microsite_configuration.models import (
    MicrositeOrganizationMapping,
    Microsite
)

utc=pytz.UTC

string_emails = sys.argv[1]
TO_EMAILS = string_emails.split(';')
try:
    course_id = sys.argv[2]
except:
    pass
    course_id = ""

try:
    frequence = int(sys.argv[3])
except:
    pass
    frequence = 1

try:
    based_on_last_login = sys.argv[4]
    if based_on_last_login == "true" or based_on_last_login == "True":
        based_on_last_login = True
    else:
        based_on_last_login = False
except:
    pass
    based_on_last_login = False

if based_on_last_login:
    based_on_text = "connectés"
else:
    based_on_text = "inscrits"
course_key = CourseKey.from_string(course_id)
course=get_course_by_id(course_key)
last_report_date = datetime.now() - timedelta(days=frequence)

#get microsite
org = course.org
query = "SELECT a.id,a.organization,b.key FROM microsite_configuration_micrositeorganizationmapping a,microsite_configuration_microsite b WHERE a.microsite_id = b.id"
microsite_list = MicrositeOrganizationMapping.objects.raw(query)
microsite_name = None
for row in microsite_list:
    if row.organization == org:
        microsite_name = row.key

domain_prefix = None

microsite = Microsite.objects.get(key=microsite_name)
microsite_value = microsite.values
i=0
for val in microsite_value:
    if val == 'domain_prefix':
        domain_prefix = microsite_value.values()[i]
    i=i+1

timestr = time.strftime("%Y_%m_%d")
timesfr = time.strftime("%d.%m.%Y")
timesfr = str(timesfr)

#headers
HEADERS = ["Student ID","Nom","Prénom","Code postal","Username","Email","Téléphone","Année de naissance","Sexe","Note","Date inscription","Date de dernière connexion"]

#get course enrolls
course_enrollements=CourseEnrollment.objects.filter(course_id=course_key)
users_number = 0

#prepare workbook
wb = Workbook(encoding='utf-8')

filename = '/home/edxtma/csv/{}_{}.xls'.format(timestr,course.display_name_with_default)
sheet = wb.add_sheet('Stats')
for i, header in enumerate(HEADERS):
   sheet.write(0, i, header)

j=0
for i in range(len(course_enrollements)):
    user=course_enrollements[i].user
    
    if based_on_last_login:
        comparison_date = user.last_login
    else:
        comparison_date=user.date_joined

    if comparison_date and comparison_date >= utc.localize(last_report_date) :
        users_number += 1
        #Grade
        course_grade = CourseGradeFactory().create(user, course)
        user_profile = {}
        try:
            user_profile = json.loads(UserProfile.objects.get(user=user).custom_field)
        except:
            user_profile = {}
        j=j+1

        last_name=user_profile.get('last_name','n/a')
        first_name=user_profile.get('first_name','n/a')
        student_id=user.id
        email=user.email
        username=user.username
        gender=user_profile.get('genre','')
        year_of_birth=user_profile.get('year_of_birth','')
        code_postal=user_profile.get('code_postal','')
        telephone=user_profile.get('telephone','')
        try:
            register_date=user.date_joined.strftime('%d %b %y')
        except:
            register_date="Null"
        try:
            last_login_formated=user.last_login.strftime('%d %b %y')
        except:
            last_login_formated="Null"

        final_grade = str(course_grade.percent * 100)+'%'

        #insert rows
        primary_rows = [
            student_id,last_name,first_name,code_postal,username,email,telephone,year_of_birth,gender,final_grade,register_date,last_login_formated
        ]

        l=0
        for prim_row in primary_rows:
            sheet.write(j, l, prim_row)
            l=l+1

output = BytesIO()

wb.save(output)

_files_values = output.getvalue()
# envoyer un mail test

if users_number >= 1:
    html = "<html><head></head><body><p>Bonjour,<br/><br/>Vous trouverez en PJ le rapport de données du MOOC \"{}\" sur les {} utilisateurs s'étant {}s ces {} derniers jours.<br/><br/>Bonne réception<br>L'équipe {}<br></p></body></html>".format(course.display_name, users_number, based_on_text, str(frequence), org)
else :
    html = "<html><head></head><body><p>Bonjour,<br/><br/>Il n'y aucun utilisateur s'étant {} au MOOC \"{}\" ces {} derniers jours.<br/><br/>Bonne réception<br>L'équipe {}<br></p></body></html>".format(based_on_text, course.display_name, str(frequence), org)

part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

for i in range(len(TO_EMAILS)):
    fromaddr = "{} <ne-pas-repondre@themoocagency.com>".format(org)
    toaddr = str(TO_EMAILS[i])
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Rapport des utilisateurs {} au cours {}".format(based_on_text, course.display_name)
    if users_number >= 1:
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
    log.info('[WUL] : mail send to '+str(TO_EMAILS[i]))
