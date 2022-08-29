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

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
from datetime import datetime, date, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("lms.envs.aws,SERVICE_VARIANT", "lms")
os.environ.setdefault("PATH", "/edx/app/edxapp/venvs/edxapp/bin:/edx/app/edxapp/edx-platform/bin:/edx/app/edxapp/.rbenv/bin:/edx/app/edxapp/.rbenv/shims:/edx/app/edxapp/.gem/bin:/edx/app/edxapp/edx-platform/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

os.environ.setdefault("SERVICE_VARIANT", "lms")
os.chdir("/edx/app/edxapp/edx-platform")

startup = importlib.import_module("lms.startup")
startup.run()

log = logging.getLogger()

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.course_groups.cohorts import get_cohort
from opaque_keys.edx.keys import CourseKey

from student.models import *

from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from lms.djangoapps.grades.context import grading_context_for_course, grading_context
from lms.djangoapps.tma_ensure_form.utils import ensure_form_factory
from courseware.courses import get_course_by_id
from courseware.courses import get_course
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from pprint import pformat

# SET MAIN VARIABLES
org = "academie-digitale"
register_form = configuration_helpers.get_value_for_org(org, 'FORM_EXTRA')
certificate_extra_form = configuration_helpers.get_value_for_org(org, 'CERTIFICATE_FORM_EXTRA')
form_factory = ensure_form_factory()
db = 'ensure_form'
collection = 'certificate_form'
form_factory.microsite = u"academie-digitale"
today = date.today()

# Get headers
HEADERS = [u"ID", u"Nom d'utilisateur", u"Email", u"Prénom", u"Nom",u"Date d'inscription",u"Dernière connexion"]

HEADERS_FORM = []
if register_form is not None:
    for row in register_form:
        if row.get('type') is not None:
            if 'first_name' not in row.get('name') and 'last_name' not in row.get('name'):
                HEADERS_FORM.append(row.get('name'))

NICE_HEADER = list(HEADERS_FORM)

HEADERS.extend(NICE_HEADER)

print HEADERS


course_ids=[
    "course-v1:academie-digitale+FC_20+2022",
    "course-v1:academie-digitale+FC_B30+2022",
    "course-v1:academie-digitale+FC_B20+2022",
    "course-v1:academie-digitale+FC_B40+2022"
    ]


def get_user_info(user):
    user_profile = {}
    email = user.email
    custom_field = {}
    certificate_field = {}

    user_id = str(user.id)
    user_profile = UserProfile.objects.get(user_id=user_id)

    try:
        custom_field = json.loads(UserProfile.objects.get(user=user).custom_field)
    except:
        pass

    form_factory.user_id = long(user_id)
    
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

    try:
        date_inscription = user.date_joined.strftime('%d %b %y')
    except:
        date_inscription = "n/a"

    try:
        last_login = user.last_login.strftime('%d %b %y')
    except:
        last_login = "n/a"
        
    user_row = [user.id, user.username, email, first_name, last_name, date_inscription, last_login]

    # Add custom field values
    for i in range(len(HEADERS_FORM)):
        user_row.append(custom_field.get(HEADERS_FORM[i], 'n/a'))

    return user_row

#### TRUE SCRIPT

# First get all enrolled users
enrolled_user_ids = []
user_profiles = UserProfile.objects.all()
for user_profile in user_profiles:
    try:
        custom_field = json.loads(user_profile.custom_field)
    except:
        custom_field = {}
    if custom_field.get("microsite") == "e-formation-artisanat":
        enrolled_user_ids.append(user_profile.user_id)

users_list = []

# Now get info for all users enrolled in courses
j=0
for j in range(len(course_ids)):
    # Course info from argument
    course_id = course_ids[j]
    course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(course_key) 
    enrollments = CourseEnrollment.objects.filter(course_id=course_key)
    
    i = 0
    for i in range(len(enrollments)):
        
        # If it is a new user
        if enrollments[i].created.date() == (today - timedelta(days=1)):
            user = enrollments[i].user
            users_list.append(get_user_info(user))


# WRITE FILE
# Prepare workbook
wb = Workbook(encoding='utf-8')
filename = '/home/edxtma/csv/formation.artisanat.fr_{}.xls'.format(time.strftime("%d.%m.%Y"))
sheet = wb.add_sheet('Rapport')
style_title = easyxf('font: bold 1')
i=0
j=0
for i in range(len(HEADERS)):
    sheet.write(0, i, HEADERS[i],style_title)
for j in range(len(users_list)):
    for l in range(len(users_list[j])):
        sheet.write(j+1, l, users_list[j][l])

# SEND MAILS
output = BytesIO()
wb.save(output)
_files_values = output.getvalue()

if len(users_list) >= 1:
    html = "<html><head></head><body><p>Bonjour,<br/><br/>Vous trouverez en PJ le rapport de donn&eacute;es des inscrits depuis le dernier rapport aux formations disponibles sur formation.artisanat.fr<br/><br/>Pour toute question sur ce rapport merci de contacter technical@themoocagency.com.<br/><br/>Bonne r&eacute;ception<br><br>L'&eacute;quipe formation-artisanat.fr</p></body></html>"
else:
    html = "<html><head></head><body><p>Bonjour,<br/><br/>Il n'y a pas de nouvel inscrit depuis le dernier rapport.<br/><br/>Bonne r&eacute;ception<br><br>L'&eacute;quipe formation-artisanat.fr</p></body></html>"

part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')

fromaddr = "e-formation-artisanat <ne-pas-repondre@themoocagency.com>"
toaddr = ["dimitri.hoareau@weuplearning.com", "alexandre.berteau@weuplearning.com"]
msg = MIMEMultipart()
msg['From'] = fromaddr
msg['To'] = toaddr
msg['Subject'] = "Rapport des inscriptions formation-artisanat.fr - " + time.strftime("%d.%m.%Y")
if len(users_list) >= 1:
    part = MIMEBase('application', 'octet-stream')
    attachment = _files_values
    part.set_payload(attachment)
    part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(filename))
    msg.attach(part)
    encoders.encode_base64(part)
server = smtplib.SMTP('mail3.themoocagency.com', 25)
server.starttls()
server.login('contact', 'waSwv6Eqer89')
msg.attach(part2)
text = msg.as_string()
server.sendmail(fromaddr, toaddr, text)
server.quit()
log.info('Email sent to '+str(toaddr))